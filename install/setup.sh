#!/bin/bash -e
cd $HOME/DomPi
python3 -m venv .venv
source .venv/bin/activate
pip install wheel
pip install -r install/requirements.txt
