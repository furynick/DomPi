# DomPi
Domotic UI on Raspi Zero2W/Touchscreen

## Hardware components
 - [Raspberry Pi Zero 2W](https://www.kubii.com/en/nano-computers/3455-raspberry-pi-zero-2-w-wh-3272496319363.html) *~20€*
 - [7" LCD DiY tablet](https://s.click.aliexpress.com/e/_opsU6dP) *~45€*
 - [AC220V to DC5V/20W Power supply](https://s.click.aliexpress.com/e/_omyvcPb) *~5€*
 - [32GB SD Card](https://s.click.aliexpress.com/e/_oC02Weh) *~5€*

## Software requirements
 - [Raspberry Pi Imager](https://www.raspberrypi.com/software/) *free*
 - Debian 12 Raspberry Pi OS Lite (32-bit) *free*

## Installation (WiP)
 - raspi-config
   - set wifi country
   - set locale
```sh
sudo apt -qq update && sudo apt -qqy upgrade
sudo apt -qqy install git ffmpeg vlc nodejs bluez-alsa-utils \
  libsdl2-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 libsdl2-gfx-1.0-0 \
  libts0 libportaudio2 pulseaudio-module-bluetooth
sudo systemctl disable getty@tty1
sudo raspi-config nonint do_i2c 1
sudo raspi-config nonint do_boot_splash 1
sudo sed -i 's/+console//' /usr/lib/systemd/system/rc-local.service.d/debian.conf
sudo sed -i 's/=tty1/=tty5/;s/$/ logo.nologo loglevel=1 vt.global_cursor_default=0 consoleblank=0 quiet/' /boot/firmware/cmdline.txt
sudo apt install seatd xdg-user-dirs libgl1-mesa-dri wayfire xwayland python3-dev pipewire-audio
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3.11))
sudo usermod -aG tty kioskadm
git clone https://github.com/furynick/DomPi.git
cd DomPi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl link $HOME/DomPi/install/kiosk.service
sudo systemctl enable kiosk
```
