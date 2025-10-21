# Contributing to Professional Binance Trading Bot

Thank you for your interest in contributing to the Professional Binance Trading Bot! We welcome contributions from the community and appreciate your help in making this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Development Guidelines](#development-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [contact@tradingbot.com](mailto:contact@tradingbot.com).

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Add tests for your changes
6. Ensure all tests pass
7. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Docker (optional)

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/binance-trading-bot.git
   cd binance-trading-bot
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

5. **Run tests to ensure everything works:**
   ```bash
   pytest
   ```

## Contributing Guidelines

### Types of Contributions

We welcome several types of contributions:

- **Bug fixes**: Fix existing issues
- **New features**: Add new functionality
- **Documentation**: Improve documentation
- **Tests**: Add or improve test coverage
- **Performance improvements**: Optimize existing code
- **Code quality**: Improve code style and structure

### Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, readable code
   - Follow the existing code style
   - Add appropriate comments and docstrings
   - Update documentation as needed

3. **Add tests:**
   - Write unit tests for new functionality
   - Ensure existing tests still pass
   - Aim for high test coverage

4. **Run quality checks:**
   ```bash
   # Format code
   black binance_trading_bot tests
   
   # Sort imports
   isort binance_trading_bot tests
   
   # Lint code
   flake8 binance_trading_bot tests
   
   # Type check
   mypy binance_trading_bot
   
   # Run tests
   pytest
   ```

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add: brief description of your changes"
   ```

6. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Process

### Before Submitting

- [ ] Ensure all tests pass
- [ ] Run code quality checks
- [ ] Update documentation if needed
- [ ] Add tests for new functionality
- [ ] Ensure your branch is up to date with main

### Pull Request Template

When creating a pull request, please include:

1. **Description**: Clear description of what the PR does
2. **Related Issues**: Link to any related issues
3. **Type of Change**: Bug fix, new feature, documentation, etc.
4. **Testing**: How you tested your changes
5. **Breaking Changes**: Any breaking changes and migration steps

### Review Process

1. All pull requests require review from maintainers
2. Address any feedback from reviewers
3. Ensure CI/CD checks pass
4. Maintainers will merge when ready

## Issue Reporting

### Bug Reports

When reporting bugs, please include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Relevant logs or error messages
- Screenshots if applicable

### Feature Requests

For feature requests, please include:

- Clear description of the feature
- Use case and motivation
- Proposed implementation approach
- Any relevant examples or mockups

### Issue Labels

We use labels to categorize issues:

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `priority: high`: High priority issues
- `priority: low`: Low priority issues

## Development Guidelines

### Code Style

- Follow PEP 8 style guide
- Use Black for code formatting
- Use isort for import sorting
- Maximum line length: 88 characters
- Use type hints where appropriate

### Naming Conventions

- Use descriptive variable and function names
- Use snake_case for variables and functions
- Use PascalCase for classes
- Use UPPER_CASE for constants

### Documentation

- Write clear docstrings for all functions and classes
- Use Google-style docstrings
- Include type hints in docstrings
- Update README.md for significant changes

### Error Handling

- Use appropriate exception types
- Provide meaningful error messages
- Log errors appropriately
- Handle edge cases gracefully

## Testing

### Test Structure

- Unit tests for individual functions and classes
- Integration tests for component interactions
- End-to-end tests for complete workflows
- Mock external dependencies

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=binance_trading_bot

# Run specific test categories
pytest -m unit
pytest -m integration

# Run tests in parallel
pytest -n auto
```

### Test Guidelines

- Write tests before implementing features (TDD)
- Aim for high test coverage (>80%)
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

## Documentation

### Documentation Types

- **Code documentation**: Docstrings and comments
- **API documentation**: Function and class documentation
- **User documentation**: README and guides
- **Developer documentation**: Contributing guide and setup instructions

### Documentation Standards

- Write clear, concise documentation
- Use proper grammar and spelling
- Include examples where helpful
- Keep documentation up to date
- Use markdown for user-facing documentation

## Release Process

### Version Numbering

We use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Ensure all tests pass
- [ ] Update documentation
- [ ] Create release notes
- [ ] Tag the release
- [ ] Publish to PyPI

## Getting Help

If you need help with contributing:

- Check existing documentation
- Search existing issues and discussions
- Join our community Discord
- Contact maintainers directly

## Recognition

Contributors will be recognized in:

- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to the Professional Binance Trading Bot! 🚀
