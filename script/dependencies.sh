#!/bin/bash

# Update the package list and install dependencies
sudo apt-get update

# Install poppler-utils and libreoffice
sudo apt-get install -y poppler-utils 
sudo apt-get install -y libreoffice

# Installing dependencies in virtual environment
pip install -r ./requirements.txt

echo "All dependencies installed!"