# Cumulocity Pyhton3 Agent

## C8yAgent Class

The class c8yAgent let's you connect your device to the Cumulocity Cloud using mqtt. I provides basic methods to:

* Connect to a cumulocity tenant via mqtt (tls supported)
* Register a device, fetch credentials and store them on the device
* Subscribe to MQTT Topics
* Send and receive MQTT Messages

c8yAgent will store the device credentials file c8y.properties in the same directory as the class. It can be edited to provide manual credentials. If not present the initialized variable is false and the registerDevice method can be used to fetch new credentials. 

## piAgent.py Module

To implement a Cumulocity Device Agent you have to cater the C8yAgent class with device specific functionality. piAgent.py provides a sample implementation for the Raspberry PI 3.

piAgent.py assumes that you have the sense hat extension installed.

The used MQTT SmartREST Template for the piAgent is stored in pi.json and has to be imported into the cumulocity tenant beforehand. 

### Prerequisites for Raspian distribution

#### Enable SPI Interface

/boot/config.txt
dtparam=spi=on

#### Python3

pip install paho-mqtt

sudo apt-get install python3-pip

sudo apt-get install python3

sudo apt-get  install python-dev python3-dev

sudo apt-get install ca-certificates

sudo apt-get install sense-hat

echo "alias python='/usr/bin/python3'" >>  ~/.bashrc
