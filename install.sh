#!/bin/sh
sudo mkdir -p /opt/softwareag/c8yPyAgent
sudo chown -R pi /opt/softwareag/*
cp piAgent.py c8yMQTT.py pi.properties /opt/softwareag/c8yPyAgent
sudo cp c8y.service  /etc/systemd/system/
sudo chown -R pi /opt/softwareag
sudo systemctl enable c8y.service 
sudo systemctl daemon-reload
sudo service c8y restart

