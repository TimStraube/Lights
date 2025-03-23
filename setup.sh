#!/bin/bash

# Install and configuire pyenv
pyenv install 3.11.1
pyenv virtualenv 3.11.1 lights
pyenv activate lights

# Install requirements
pip install -r requirements.txt