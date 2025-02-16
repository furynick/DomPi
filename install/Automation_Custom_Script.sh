#!/bin/bash -x
exec 2>&1
BASE="/boot/firmware"
systemctl disable --now getty@tty1.service
apt -y install bluez bluez-alsa-utils libsdl2-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 libsdl2-gfx-1.0-0 libts0 libportaudio2 python3-venv
su - dietpi -c '[ -d .ssh ] || mkdir .ssh; git clone https://github.com/furynick/DomPi.git &&  DomPi/install/setup.sh'
install -o dietpi -g dietpi -m 0400 $BASE/id_ed25519 ~dietpi/.ssh
install -o dietpi -g dietpi -m 0644 $BASE/id_ed25519.pub ~dietpi/.ssh
rm -f $BASE/id_ed25519*
usermod -aG audio dietpi
