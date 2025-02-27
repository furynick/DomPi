#!/bin/bash
cd "$(dirname $(readlink -f $0))"
[ -z "$SSID" ] && read -p "WiFi SSID: " SSID
[ -z "$PASS" ] && read -p "WiFi Pass: " PASS
T=$'\t'
curl https://dietpi.com/downloads/images/DietPi_RPi234-ARMv8-Bookworm.img.xz | unxz | sudo dd of=/dev/sda bs=4M status=none
sudo mount /dev/sda1 /mnt
sudo cp dietpi.txt Automation_Custom_Script.sh ~/.ssh/id_ed25519* /mnt
sudo sed -i "/WIFI_SSID.0/s${T}''${T}'${SSID}'${T};/WIFI_KEY.0/s${T}''${T}'${PASS}'${T}" /mnt/dietpi-wifi.txt
sudo umount /mnt
