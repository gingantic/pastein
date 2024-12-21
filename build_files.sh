#!/bin/bash

# build_files.sh

# create a virtual environment named 'venv' if it doesn't already exist
python3 -m venv venv

# activate the virtual environment
source venv/bin/activate

python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput
python3 manage.py makemigrations
python3 manage.py migrate

# fix for A Serverless Function has exceeded the unzipped maximum size of 250 MB
rm -rf venv