#!/bin/bash

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Create necessary directories
mkdir -p data/trading_history
mkdir -p logs
mkdir -p config

# Copy example config
cp config/base.yaml.example config/base.yaml

echo "Installation complete! Edit config/base.yaml with your settings." 