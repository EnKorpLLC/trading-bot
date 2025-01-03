# Trading Bot

A professional-grade automated trading system with advanced risk management and machine learning capabilities.

## Quick Installation

### Windows
```batch
git clone https://github.com/yourusername/trading-bot.git
cd trading-bot
scripts\install.bat
```

### Linux/macOS
```bash
git clone https://github.com/yourusername/trading-bot.git
cd trading-bot
chmod +x scripts/install.sh
./scripts/install.sh
```

## Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/trading-bot.git
cd trading-bot
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package:
```bash
pip install -e .
```

5. Configure the application:
```bash
cp config/base.yaml.example config/base.yaml
# Edit config/base.yaml with your settings
```

## Running the Application

1. Activate the virtual environment (if not already activated):
```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

2. Run the application:
```bash
trading-bot
```

## Configuration

Edit `config/base.yaml` to configure:
- API credentials
- Risk management parameters
- Trading strategies
- Notification settings

## Documentation

See the [docs](docs/) directory for detailed documentation.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 