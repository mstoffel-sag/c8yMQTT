#!/bin/sh
mkdir -p /opt/softwareag/c8yPyAgent
cp piAgent.py c8yMQTT.py pi.properties /opt/softwareag/c8yPyAgent
sudo cp c8y.service  /etc/systemd/system/
sudo systemctl enable c8y.service 
sudo systemctl daemon-reload
sudo service c8y restart

