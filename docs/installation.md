# Installation Guide

## Prerequisites
1. Python 3.9 or higher
2. PostgreSQL 13 or higher
3. Git

## Step-by-Step Installation

### 1. System Dependencies
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.9 python3.9-dev python3-pip postgresql-13

# macOS
brew install python@3.9 postgresql@13
```

### 2. Clone Repository
```bash
git clone https://github.com/yourusername/trading-bot.git
cd trading-bot
```

### 3. Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Database Setup
```bash
# Create database
createdb trading_bot

# Run migrations
python -m src.db.migrations
```

### 6. Configuration
1. Copy example configuration:
   ```bash
   cp config/base.yaml.example config/base.yaml
   ```
2. Edit configuration file with your settings
3. Set up environment variables:
   ```bash
   export TRADING_ENV=development
   ```

### 7. Verify Installation
```bash
python -m pytest tests/
``` 