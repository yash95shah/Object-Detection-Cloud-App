#!/bin/bash

# assumes this script is run from the cloud-proj-1/app/ directory, and uses relative paths
sudo apt-get install -fy python3-venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel gunicorn python-dotenv flask flask_restful requests boto3 pymongo
