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
 
sudo apt-get install python3-pip  
sudo apt-get install python3  
sudo apt-get install python-dev python3-dev  
sudo apt-get install ca-certificates  
sudo apt-get install sense-hat
pip3 install paho-mqtt 

echo "alias python='/usr/bin/python3'" >>  ~/.bashrc

## Getting Started

### Cumulocity

The used MQTT SmartREST Template for the piAgent is stored in pi.json and has to be imported into the cumulocity tenant beforehand. It can be imported via Devicemanagement -> Device types -> SmartREST templates.

### Register Device

__c8y.properties__  
c8yMQTT will create and store the device credentials file c8y.properties in the same directory as the class. It can be created to provide manual credentials. 

!!!PLEASE MAKE SURE THAT THE DEVICE IS NOT ALREADY RERGISTERED WITH IT'S SERIAL NUMBER!!!
If that is the case either you have to delete the device and re-register or create the c8y.properties by hand and provide correct credentials and client id.

  
[credentials]  
user =  
tenant =   
password =   
clientid =

If not present the initialized variable is false and the registerDevice method can be used to fetch new credentials. 

To autoregister your pi got to In Cumulocity -> Device Management create a new Device Registration entering the serial (could be retrieved by cat /proc/cpuinfo) of your PI. The c8y.properties file will be created automatically. For this the bootstrap_pwd in pi.properties must be set.

__pi.properties__

the pi.properties file holds device specific parameters. To autoregister your device you need to provide the bootstrap_pwd this can be 
obtained via the cumulocity support.

### Agent Run
Checkout the project. For testing just run:  
python3 piAgent.py  

### Agent Install
Execute sudo install.sh (You need to have write access to /opt).  
A service called c8y will be registerd with systemd


## pcAgent.py Module
The pcAgent.py module is a slight modification to run on PC Hardware. It shares most of the configuration but will read CPU and Memory Usage via the psutil module. The serial/model  has to be configured inside the pcAgent.py file:

serial = 'putyourserial'
model = 'MyPcModel'

### Docker Support 
PC Agent and PI Agent can run within Docker. Dockerfiles can be used to build an image:

Build - PC:
docker build -t pcagent -f ./Dockerfile.pcAgent .

Build - Raspberry Pi:
docker build -t piagent -f ./Dockerfile.piAgent .

Run - PC:
docker run -it -v $PWD:/usr/src/app pcagent

Run - Raspberry Pi:
docker run -it -v $PWD:/usr/src/app --privileged=true piagent
