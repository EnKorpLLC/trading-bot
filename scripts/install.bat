@echo off

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt

REM Install the package
pip install -e .

REM Create necessary directories
mkdir data\trading_history
mkdir logs
mkdir config

REM Copy example config
copy config\base.yaml.example config\base.yaml

echo Installation complete! Edit config\base.yaml with your settings.
pause 