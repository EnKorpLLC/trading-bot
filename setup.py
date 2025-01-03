from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="trading-bot",
    version="0.2.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A professional-grade automated trading system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/trading-bot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "trading-bot=src.app:main",
        ],
    },
) 