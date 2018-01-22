#!/bin/sh
sudo mkdir -p /opt/softwareag/c8yPyAgent
sudo cp piAgent.py c8yAgent.py pi.properties /opt/softwareag/c8yPyAgent
sudo cp c8y.service  /etc/systemd/system/
sudo systemctl enable c8y.service 
sudo systemctl daemon-reload

