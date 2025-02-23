#!/bin/bash
set -e

cd $HOME
DEV_PKGS="build-essential libdrm-dev libgbm-dev libudev-dev libfreetype6-dev"
DEV_PKGS+=" libts-dev python3-dev portaudio19-dev"
sudo apt -qq -y install $DEV_PKGS
git config --global http.version HTTP/1.1
git config --global http.postBuffer 268435456
git config --global core.compression 0
(
  git clone  --depth 1 https://github.com/libsdl-org/SDL.git
  mkdir SDL/build
  cd SDL/build
  V=$(git tag | sort | awk '/release-2/ {V=$0} END {print V}')
  git checkout $V
  git fetch --unshallow
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
