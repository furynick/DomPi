#!/bin/bash
set -e

REQ_PKGS="git libportaudio2 libopenjp2-7 libgl1-mesa-dri bluez-alsa-utils libegl1 libgl1"
REQ_PKGS+=" python3-venv libsdl2-image-2.0-0 libsdl2-gfx-1.0-0 libsdl2-ttf-2.0-0"
REQ_PKGS+=" libopenblas0-pthread libatlas3-base"
DEV_PKGS="build-essential python3-dev portaudio19-dev libbluetooth-dev"
DEV_PKGS+=" libsdl2-dev libsdl2-image-dev libjpeg-dev libpng-dev libtiff-dev libx11-dev"
DEV_PKGS+=" libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libfreetype6-dev"
DEV_PKGS+=" libatlas-base-dev libopenblas-dev"
PYGAME_DETECT_AVX2=1
CFLAGS="-mfpu=neon-vfpv4 -march=armv7-a+neon-vfpv4 -mtune=cortex-a53 -O3"
MAKEFLAGS="-j$(nproc)"
export PYGAME_DETECT_AVX2 CFLAGS MAKEFLAGS

sudo apt -qq update
sudo apt -qq -y dist-upgrade
sudo apt -qq -y --no-install-recommends install $REQ_PKGS $DEV_PKGS
sudo raspi-config nonint do_i2c 0
sudo usermod -aG tty $USER
sudo mkdir /etc/systemd/system/alsa-restore.service.d/
cat << EoF | sudo tee /etc/systemd/system/alsa-restore.service.d/no-jack.conf
[Service]
Environment=JACK_NO_AUDIO_RESERVATION=1
EoF

git clone https://github.com/furynick/DomPi.git ${HOME}/DomPi
cd ${HOME}/DomPi
[ -d .venv ] && rm -rf .venv
if ! [ -d .priv ]; then
  mkdir .priv
  cd .priv
  ytmusicapi oauth
  cd ..
fi
python3 -m venv .venv
source .venv/bin/activate
pip install wheel
pip install -r install/requirements.txt
pip install --use-pep517 --no-binary :all: pygame==2.6.1

sudo cp install/pointercal install/asound.conf /etc
sudo dpkg-reconfigure locales

# Clean
[Service]
Environment="JACK_NO_AUDIO_RESERVATION=1"

sudo apt -qq -y purge $DEV_PKGS
sudo apt -qq -y autoremove --purge
sudo systemctl daemon-reload
sudo systemctl restart alsa-restore.service
sudo systemctl disable --now getty@tty1
sudo systemctl link ${HOME}/DomPi/install/kiosk.service
sudo systemctl enable kiosk
sudo sed -i 's/+console//' /usr/lib/systemd/system/rc-local.service.d/debian.conf
sudo sed -i 's/=tty1/=tty5/;s/$/ logo.nologo loglevel=1 vt.global_cursor_default=0 consoleblank=0 quiet/' /boot/firmware/cmdline.txt
