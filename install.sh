#!/bin/sh

echo "[Unit]
Description=Cumulocity PI Agent
After=multi-user.target

[Service]
User=pi
ExecStartPre=/bin/sleep 3
Type=idle
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/piAgent.py

[Install]
WantedBy=multi-user.target" > c8y.service

sudo apt install sense-hat

python3 -m pip install --upgrade pip
python3 -m pip install -r ./requirements.txt

sudo cp c8y.service  /etc/systemd/system/
sudo systemctl enable c8y.service 
sudo systemctl daemon-reload
sudo service c8y restart

