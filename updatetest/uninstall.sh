#!/bin/sh

sudo systemctl stop c8y.service
sudo systemctl disable c8y.service
sudo rm /etc/systemd/system/c8y.service
sudo rm /etc/systemd/system/c8y.service # and symlinks that might be related
sudo rm /usr/lib/systemd/system/c8y.service
sudo rm /usr/lib/systemd/system/c8y.service # and symlinks that might be related
sudo systemctl daemon-reload
sudo systemctl reset-failed
