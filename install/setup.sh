#!/bin/bash
set -e

REQ_PKGS="git libportaudio2 libopenjp2-7 libgl1-mesa-dri bluez-alsa-utils libegl1 libgl1"
REQ_PKGS+=" python3-venv libsdl2-image-2.0-0 libsdl2-gfx-1.0-0 libsdl2-ttf-2.0-0"
DEV_PKGS="build-essential python3-dev portaudio19-dev"

sudo apt -qq update
sudo apt -qq -y dist-upgrade
sudo apt -qq -y --no-install-recommends install $REQ_PKGS $DEV_PKGS
sudo raspi-config nonint do_i2c 0
sudo usermod -aG tty $USER

git clone https://github.com/furynick/DomPi.git $HOME/DomPi
cd $HOME/DomPi
[ -d .venv ] && rm -rf .venv
if ! [ -d .priv ]; then
  mkdir .priv
  ytmusicapi oauth
fi
python3 -m venv .venv
source .venv/bin/activate
pip install wheel
pip install -r install/requirements.txt

# Clean
sudo apt -qq -y purge $DEV_PKGS
sudo apt -qq -y autoremove --purge
sudo systemctl disable --now getty@tty1
sudo sed -i 's/+console//' /usr/lib/systemd/system/rc-local.service.d/debian.conf
sudo sed -i 's/=tty1/=tty5/;s/$/ logo.nologo loglevel=1 vt.global_cursor_default=0 consoleblank=0 quiet/' /boot/firmware/cmdline.txt
