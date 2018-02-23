# Cumulocity Pyhton3 Agent

This project is a demo implementation and has no intention to meet production standards. Rather the aim is to show an example how a cumulocity agent could be implemented in python.

A cumulocity tenant to try out it can be provisioned as a trial at:

http://cumulocity.com/ -> Try Cumulocity Free

## C8yMQTT Class

The class C8yMQTT let's you connect your device to the Cumulocity Cloud using mqtt. It provides basic methods to:

* Connect to a cumulocity tenant via mqtt (tls supported)
* Register a device, fetch credentials and store them on the device
* Subscribe to MQTT Topics
* Send and receive MQTT Messages

## piAgent.py Module

To implement a Cumulocity Device Agent you have to cater the C8yMQTT class with device specific functionality (Send Measurements etc.). piAgent.py provides a sample implementation for the Raspberry PI 3.


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

## Getting Started

### Cumulocity

The used MQTT SmartREST Template for the piAgent is stored in pi.json and has to be imported into the cumulocity tenant beforehand. 

### Register Device

__c8y.properties__  
c8yMQTT will create and store the device credentials file c8y.properties in the same directory as the class. It can be created to provide manual credentials. 

  
[credentials]  
user =  
tenant =   
password =   
clientid =

If not present the initialized variable is false and the registerDevice method can be used to fetch new credentials. 

To autoregister your pi got to In Cumulocity -> Device Management create a new Device Registration using the serial of your PI.

__pi.properties__

the pi.properties file holds device specific parameters. To autoregister your device you need to provide the bootstrap_pwd this can be obtained via the cumulocity support.

### Agent Run
Checkout the project. For testing just run:  
python3 piAgent.py  

### Agent Install
Execute install.sh (You need to have write access to /opt).  
A service called c8y will be registerd with systemd
