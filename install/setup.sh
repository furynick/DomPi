#!/bin/bash
set -e

cd $HOME
DEV_PKGS="build-essential libdrm-dev libgbm-dev libudev-dev libfreetype-dev devscripts dpkg-dev fakeroot"
DEV_PKGS+=" libts-dev python3-dev portaudio19-dev libegl-dev g++ automake libegl-dev libxext-dev"
DEV_PKGS+=" build-essential:native fcitx-libs-dev libasound2-dev libdbus-1-dev libdecor-0-dev"
DEV_PKGS+=" libgles-dev libibus-1.0-dev libpipewire-0.3-dev libpulse-dev libsamplerate0-dev libsndio-dev"
DEV_PKGS+=" libudev-dev libvulkan-dev libwayland-dev libxcursor-dev libxfixes-dev libxi-dev libxinerama-dev"
DEV_PKGS+=" libxkbcommon-dev libxrandr-dev libxss-dev libxt-dev libxv-dev libxxf86vm-dev wayland-protocols"
DEV_PKGS+=" graphviz doxygen libsdl2-dev libjpeg-dev libtiff-dev libwebp-dev libharfbuzz-dev"
sudo apt -qq update
sudo apt -qq -y dist-upgrade
sudo apt -qq -y --no-install-recommends install \
  git python3-venv libportaudio2 libopenjp2-7 libgl1-mesa-dri \
  libsdl2-image-2.0-0 libsdl2-gfx-1.0-0 libsdl2-ttf-2.0-0 \
  $DEV_PKGS
sudo raspi-config nonint do_i2c 0
sudo usermod -aG tty $USER

git clone https://github.com/furynick/DomPi.git

wget http://deb.debian.org/debian/pool/main/libs/libsdl2-gfx/libsdl2-gfx_1.0.4+dfsg.orig.tar.gz
wget http://deb.debian.org/debian/pool/main/libs/libsdl2/libsdl2_2.26.5+dfsg.orig.tar.gz
wget http://deb.debian.org/debian/pool/main/libs/libsdl2-image/libsdl2-image_2.6.3+dfsg.orig.tar.gz
wget http://deb.debian.org/debian/pool/main/libs/libsdl2-ttf/libsdl2-ttf_2.20.1+dfsg.orig.tar.xz
for f in *.tar.gz; do tar xzf "$f"; done
for f in *.tar.xz; do tar xJf "$f"; done
wget -O - http://deb.debian.org/debian/pool/main/libs/libsdl2-gfx/libsdl2-gfx_1.0.4+dfsg-4.debian.tar.xz | tar xJf - -C SDL2_gfx-1.0.4
wget -O - http://deb.debian.org/debian/pool/main/libs/libsdl2/libsdl2_2.26.5+dfsg-1.debian.tar.xz | tar xJf - -C SDL2-2.26.5
wget -O - http://deb.debian.org/debian/pool/main/libs/libsdl2-image/libsdl2-image_2.6.3+dfsg-1.debian.tar.xz | tar xJf - -C SDL2_image-2.6.3
wget -O - http://deb.debian.org/debian/pool/main/libs/libsdl2-ttf/libsdl2-ttf_2.20.1+dfsg-2.debian.tar.xz | tar xJf - -C SDL2_ttf-2.20.1
for d in SDL2*/; do cd "$d"; debuild -us -uc; cd ..; done

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
