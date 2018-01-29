# c8yMQTT Client

The generic MQTT Connection class for Cumulocity named c8yMQTT.py provides basic functionality like registering a device Publish/Subscribe to python clients.

The class uses the Python Paho MQTT implementation. You need at minimum the paho-mqtt python module to use the class.

# piAgent 

As a usage Example c8yMQTT was used to implement a Cumulocity Agent for the Raspberry PI that hols a Sense-Hat extension to feature sensor readings.


# Prerequsites for raspbian

To make the sample work the following adjustments have to be made to the raspbian distribution:

## Enable SPI Interface

/boot/config.txt
dtparam=spi=on

## Python
sudo apt-get install python3-pip
sudo apt-get install p:ython3
sudo apt-get install python-dev python3-dev
sudo apt-get install ca-certificates
sudo apt-get install sense-hat
echo "alias python='/usr/bin/python3'" >>  ~/.bashrc


pip3 install paho-mqtt
pip3 install configparser
pip3 install sense_hat

# Installation

* Adjust pi.properties to connect to the right cloud platfrom (mqtt.cumulocity.com is predefined) 
* Make the pi user a sudoer that can also reboot the system
* Execute install.sh

