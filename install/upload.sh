#!/bin/bash
read -p "WiFi SSID: " SSID
read -p "WiFi Pass: " PASS
curl https://dietpi.com/downloads/images/DietPi_RPi234-ARMv8-Bookworm.img.xz | unxz | sudo dd of=/dev/sda bs=4M
sudo mount /dev/sda1 /mnt
sudo cp dietpi.txt Automation_Custom_Script.sh /mnt
sudo sed -i "/WIFI_SSID.0/s²''²'$SSID'²;/WIFI_KEY.0/s²''²'$PASS'²" /mnt/dietpi-wifi.txt
sudo umount /mnt
