#!/bin/bash
set -x
exec 2>&1

KIOSK_USER=dietpi
BASE="/boot/firmware"

# Bluetooth setup
apt -y install bluez-firmware bluez-alsa-utils alsa-utils dbus bluez
echo 'SUBSYSTEM=="bluetooth", ACTION=="add", KERNEL=="hci0:*", RUN+="/usr/bin/bluetoothctl connect $env{DEVNAME}"' >/etc/udev/rules.d/99-btconnect.rules 

# Sofware setup
install -o ${KIOSK_USER} -g ${KIOSK_USER} -m 0755 -d ~${KIOSK_USER}/.ssh
install -o ${KIOSK_USER} -g ${KIOSK_USER} -m 0400 $BASE/id_ed25519 ~${KIOSK_USER}/.ssh
install -o ${KIOSK_USER} -g ${KIOSK_USER} -m 0644 $BASE/id_ed25519.pub ~${KIOSK_USER}/.ssh
usermod -aG audio,tty,gpio,i2c,video ${KIOSK_USER}
setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))
apt -y install libts0 libportaudio2 python3-venv
su - ${KIOSK_USER} -c 'curl -s https://raw.githubusercontent.com/furynick/DomPi/refs/heads/main/install/setup.sh | bash'
cp ${KIOSK_USER}/DomPi/install/pointercal /etc

# Clean
sed -i 's/+console//' /usr/lib/systemd/system/rc-local.service.d/debian.conf
sed -i 's/=tty1/=tty5/;s/$/ loglevel=1 vt.global_cursor_default=0 consoleblank=0 quiet/' /boot/firmware/cmdline.txt
rm -f $BASE/id_ed25519*

# Service install
systemctl link ~${KIOSK_USER}/DomPi/install/kiosk.service
systemctl enable kiosk
systemctl disable --now getty@tty1.service
