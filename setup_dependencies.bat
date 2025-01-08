@echo off
echo Installing TradingBot Dependencies...

REM Upgrade pip
python -m pip install --upgrade pip

REM Install core ML dependencies
pip install scikit-learn==1.3.0
pip install numpy==1.24.3
pip install pandas==2.0.3

REM Install trading dependencies
pip install backtrader==1.9.78.123

REM Install visualization dependencies
pip install matplotlib==3.7.2

REM Install genetic algorithm library
pip install deap==1.3.3

REM Install other dependencies
pip install PyQt5==5.15.9
pip install pyqtgraph==0.13.3
pip install joblib==1.3.1

REM Install development dependencies
pip install pytest==7.4.0
pip install pytest-asyncio==0.21.1
pip install black==23.7.0
pip install flake8==6.1.0

echo Dependencies installation complete!
pause 