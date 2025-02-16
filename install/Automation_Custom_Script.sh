#!/bin/bash
SELF="$(readlink -f $0)"
BASE="${SELF%/*}"
systemctl disable --now getty@tty1.service
su - dietpi -c '[ -d .ssh ] || mkdir .ssh; git clone https://github.com/furynick/DomPi.git &&  DomPi/install/setup.sh'
install -o dietpi -m 0400 $BASE/id_ed25519 ~dietpi/.ssh
install -o dietpi -m 0644 $BASE/id_ed25519.pub ~dietpi/.ssh
usermod -aG audio dietpi
