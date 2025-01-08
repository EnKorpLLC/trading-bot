import subprocess
import sys

def install_package(package):
    print(f"Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

dependencies = [
    "numpy==1.24.3",
    "pandas==2.0.3",
    "matplotlib==3.7.2",
    "scikit-learn==1.3.0",
    "deap==1.3.3",
    "PyQt5==5.15.9",
    "pyqtgraph==0.13.3",
    "joblib==1.3.1",
    "backtrader",
    "fastapi==0.109.2",
    "uvicorn==0.27.1",
    "pydantic==2.6.1",
    "pytest==7.4.0",
    "pytest-asyncio==0.21.1",
    "black==23.7.0",
    "flake8==6.1.0"
]

def main():
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "numpy", "-y"])
    except:
        pass
    
    for package in dependencies:
        try:
            install_package(package)
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package}: {e}")
            continue
    print("Installation complete!")

if __name__ == "__main__":
    main() 