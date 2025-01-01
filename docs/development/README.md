# Development Guide

## Architecture Overview

### Component Structure
```
src/
├── core/          # Core trading logic
├── data/          # Data management
├── risk/          # Risk management
├── analysis/      # Analysis tools
├── ui/            # User interface
└── utils/         # Utilities

tests/
├── unit/          # Unit tests
├── integration/   # Integration tests
└── performance/   # Performance tests
```

## Development Setup

### 1. Development Environment
```bash
# Create development environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### 2. Code Style
We use:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking

```bash
# Format code
black src/ tests/

# Run linting
flake8 src/ tests/

# Check types
mypy src/
```

### 3. Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/unit/test_risk_manager.py
```

## Contributing

### Pull Request Process
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Run tests
5. Submit pull request

### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance 