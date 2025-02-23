#!/bin/bash
set -x
exec 2>&1

KIOSK_USER=dietpi
BASE="/boot/firmware"

# Sofware setup
install -o ${KIOSK_USER} -g ${KIOSK_USER} -m 0400 $BASE/id_ed25519 ~${KIOSK_USER}/.ssh
install -o ${KIOSK_USER} -g ${KIOSK_USER} -m 0644 $BASE/id_ed25519.pub ~${KIOSK_USER}/.ssh
usermod -aG audio,tty ${KIOSK_USER}
setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))
sed -i 's/+console//' /usr/lib/systemd/system/rc-local.service.d/debian.conf
sed -i 's/=tty1/=tty5/;s/$/ loglevel=1 vt.global_cursor_default=0 consoleblank=0 quiet/' /boot/firmware/cmdline.txt
apt -y install build-essential python3-dev portaudio19-dev
apt -y install bluez-firmware bluez-alsa-utils alsa-utils dbus bluez
apt -y install libsdl2-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 libsdl2-gfx-1.0-0 libts0 libportaudio2 python3-venv
su - ${KIOSK_USER} -c '[ -d .ssh ] || mkdir .ssh; git clone https://github.com/furynick/DomPi.git &&  DomPi/install/setup.sh'
cp ${KIOSK_USER}/DomPi/install/pointercal /etc

# Clean
apt -y purge build-essential python3-dev portaudio19-dev
apt -y autoremove --purge
rm -f $BASE/id_ed25519*

# Service install
systemctl link ~${KIOSK_USER}/DomPi/install/kiosk.service
systemctl enable kiosk
systemctl disable --now getty@tty1.service
