#!/bin/bash

echo "Setting up Publications Scraping Pipeline..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Run tests
echo "Running setup tests..."
python test_setup.py

echo ""
echo "Setup complete! To activate the virtual environment, run:"
echo "source venv/bin/activate"
echo ""
echo "Then run the pipeline with:"
echo "python main.py"