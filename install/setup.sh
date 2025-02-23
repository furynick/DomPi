#!/bin/bash -e
cd $HOME
DEV_PKGS="build-essential libdrm-dev libgbm-dev libudev-dev libfreetype6-dev"
DEV_PKGS+=" libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev"
DEV_PKGS+=" libts-dev python3-dev portaudio19-dev"
sudo apt -qq -y install $DEV_PKGS
(
  git clone https://github.com/libsdl-org/SDL.git
  cd SDL
  mkdir build
  cd build
  ../configure --enable-video-kmsdrm --enable-video-fbcon --enable-video-directfb \
             --enable-tff --enable-gfx --enable-image --enable-touchscreen
  make -j4
  sudo make install
)

(
  git clone https://github.com/furynick/DomPi.git
  cd DomPi
  [ -d .venv ] && rm -rf .venv
  python3 -m venv .venv
  source .venv/bin/activate
  pip install wheel
  pip install -r install/requirements.txt
)

# Clean
sudo apt -qq -y purge $DEV_PKGS
sudo apt -qq -y autoremove --purge
