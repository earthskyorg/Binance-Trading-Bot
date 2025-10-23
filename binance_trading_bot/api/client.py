"""
Professional Binance API client with comprehensive error handling and rate limiting.
"""

import asyncio
import aiohttp
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlencode
import json
from dataclasses import dataclass

from ..core.exceptions import APIError, ConnectionError, InsufficientFundsError, InvalidSymbolError
from ..core.logging import get_logger


@dataclass
class OrderBook:
    """Order book data structure."""
    symbol: str
    bids: List[List[float]]
    asks: List[List[float]]
    timestamp: int


@dataclass
class Ticker:
    """Ticker data structure."""
    symbol: str
    price: float
    volume: float
    change_24h: float
    timestamp: int


@dataclass
class AccountInfo:
    """Account information."""
    balance: float
    available_balance: float
    margin_balance: float
    unrealized_pnl: float
    positions: List[Dict[str, Any]]


class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, max_requests: int = 1200, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def acquire(self):
        """Acquire permission to make a request."""
        now = time.time()
        
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        
        # Check if we can make a request
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                self.requests = []
        
        self.requests.append(now)


class BinanceAPIClient:
    """Professional Binance API client with comprehensive error handling."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        rate_limit: bool = True
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.rate_limit = rate_limit
        
        # Base URLs
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
            self.ws_url = "wss://stream.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
            self.ws_url = "wss://fstream.binance.com"
        
        # Rate limiter
        self.rate_limiter = RateLimiter() if rate_limit else None
        
        # Session
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = get_logger("api_client")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Start the API client."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        """Close the API client."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature."""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """Make HTTP request to Binance API."""
        if self.session is None:
            raise ConnectionError("API client not started")
        
        # Rate limiting
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        # Prepare parameters
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            query_string = urlencode(params)
            params['signature'] = self._generate_signature(query_string)
        
        # Prepare headers
        headers = {'X-MBX-APIKEY': self.api_key}
        
        # Make request
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params if method == 'GET' else None,
                data=params if method != 'GET' else None,
                headers=headers
            ) as response:
                
                # Handle rate limiting
                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 1))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(method, endpoint, params, signed)
                
                # Parse response
                response_data = await response.json()
                
                # Check for API errors
                if response.status != 200:
                    error_code = response_data.get('code', -1)
                    error_msg = response_data.get('msg', 'Unknown error')
                    
                    if error_code == -1021:
                        raise APIError("Timestamp out of sync")
                    elif error_code == -2010:
                        raise InsufficientFundsError("Insufficient balance")
                    elif error_code == -1121:
                        raise InvalidSymbolError(f"Invalid symbol: {error_msg}")
                    else:
                        raise APIError(f"API Error {error_code}: {error_msg}")
                
                return response_data
                
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise APIError(f"Invalid JSON response: {str(e)}")
    
    async def get_server_time(self) -> int:
        """Get server time."""
        response = await self._make_request('GET', '/fapi/v1/time')
        return response['serverTime']
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information."""
        return await self._make_request('GET', '/fapi/v1/exchangeInfo')
    
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information."""
        exchange_info = await self.get_exchange_info()
        for symbol_info in exchange_info['symbols']:
            if symbol_info['symbol'] == symbol:
                return symbol_info
        raise InvalidSymbolError(f"Symbol {symbol} not found")
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> OrderBook:
        """Get order book for symbol."""
        params = {'symbol': symbol, 'limit': limit}
        response = await self._make_request('GET', '/fapi/v1/depth', params)
        
        return OrderBook(
            symbol=symbol,
            bids=[[float(bid[0]), float(bid[1])] for bid in response['bids']],
            asks=[[float(ask[0]), float(ask[1])] for ask in response['asks']],
            timestamp=response['lastUpdateId']
        )
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get 24hr ticker price change statistics."""
        params = {'symbol': symbol}
        response = await self._make_request('GET', '/fapi/v1/ticker/24hr', params)
        
        return Ticker(
            symbol=symbol,
            price=float(response['lastPrice']),
            volume=float(response['volume']),
            change_24h=float(response['priceChangePercent']),
            timestamp=response['closeTime']
        )
    
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500
    ) -> List[List[Union[int, float]]]:
        """Get kline/candlestick data."""
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        response = await self._make_request('GET', '/fapi/v1/klines', params)
        return response
    
    async def get_account_info(self) -> AccountInfo:
        """Get account information."""
        response = await self._make_request('GET', '/fapi/v2/account', signed=True)
        
        # Extract balance information
        balance = 0.0
        available_balance = 0.0
        margin_balance = 0.0
        unrealized_pnl = 0.0
        
        for asset in response['assets']:
            if asset['asset'] == 'USDT':
                balance = float(asset['walletBalance'])
                available_balance = float(asset['availableBalance'])
                margin_balance = float(asset['marginBalance'])
                unrealized_pnl = float(asset['unrealizedProfit'])
                break
        
        return AccountInfo(
            balance=balance,
            available_balance=available_balance,
            margin_balance=margin_balance,
            unrealized_pnl=unrealized_pnl,
            positions=response['positions']
        )
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for symbol."""
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        return await self._make_request('POST', '/fapi/v1/leverage', params, signed=True)
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = 'GTC',
        stop_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Place an order."""
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'timeInForce': time_in_force
        }
        
        if price:
            params['price'] = price
        if stop_price:
            params['stopPrice'] = stop_price
        
        return await self._make_request('POST', '/fapi/v1/order', params, signed=True)
    
    async def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an order."""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return await self._make_request('DELETE', '/fapi/v1/order', params, signed=True)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders."""
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        response = await self._make_request('GET', '/fapi/v1/openOrders', params, signed=True)
        return response
    
    async def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order status."""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return await self._make_request('GET', '/fapi/v1/order', params, signed=True)
