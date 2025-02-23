#!/bin/bash -x
exec 2>&1
BASE="/boot/firmware"
install -o dietpi -g dietpi -m 0400 $BASE/id_ed25519 ~dietpi/.ssh
install -o dietpi -g dietpi -m 0644 $BASE/id_ed25519.pub ~dietpi/.ssh
rm -f $BASE/id_ed25519*
usermod -aG audio dietpi
apt -y install build-essential python3-dev portaudio19-dev
apt -y install bluez-firmware bluez-alsa-utils alsa-utils dbus bluez
apt -y install libsdl2-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 libsdl2-gfx-1.0-0 libts0 libportaudio2 python3-venv
su - dietpi -c '[ -d .ssh ] || mkdir .ssh; git clone https://github.com/furynick/DomPi.git &&  DomPi/install/setup.sh'
apt -y purge build-essential python3-dev portaudio19-dev
apt -y autoremove --purge
systemctl disable --now getty@tty1.service
