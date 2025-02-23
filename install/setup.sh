#!/bin/bash -e
cd $HOME/DomPi
sudo apt -qq -y install build-essential python3-dev portaudio19-dev
[ -d .venv ] && rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install wheel
pip install -r install/requirements.txt
sudo apt -qq -y purge build-essential python3-dev portaudio19-dev
sudo apt -qq -y autoremove --purge
