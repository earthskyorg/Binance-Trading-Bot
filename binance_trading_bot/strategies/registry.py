"""
Strategy registry for managing available trading strategies.
"""

from typing import Dict, Type, List, Optional
from .base import BaseStrategy


class StrategyRegistry:
    """Registry for managing trading strategies."""
    
    def __init__(self):
        self._strategies: Dict[str, Type[BaseStrategy]] = {}
    
    def register(self, name: str, strategy_class: Type[BaseStrategy]) -> None:
        """
        Register a strategy class.
        
        Args:
            name: Strategy name
            strategy_class: Strategy class
        """
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(f"Strategy class must inherit from BaseStrategy")
        
        self._strategies[name] = strategy_class
    
    def get_strategy(self, name: str, parameters: Optional[Dict] = None) -> BaseStrategy:
        """
        Get a strategy instance.
        
        Args:
            name: Strategy name
            parameters: Strategy parameters
            
        Returns:
            Strategy instance
        """
        if name not in self._strategies:
            raise ValueError(f"Strategy '{name}' not found. Available strategies: {list(self._strategies.keys())}")
        
        strategy_class = self._strategies[name]
        return strategy_class(name, parameters)
    
    def list_strategies(self) -> List[str]:
        """Get list of available strategy names."""
        return list(self._strategies.keys())
    
    def is_registered(self, name: str) -> bool:
        """Check if strategy is registered."""
        return name in self._strategies
    
    def unregister(self, name: str) -> None:
        """Unregister a strategy."""
        if name in self._strategies:
            del self._strategies[name]


# Global strategy registry
strategy_registry = StrategyRegistry()
