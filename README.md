# Cumulocity IoT Python3 Agent

c8yMQTT is a Python3 Cumulocity Agent for MQTT and Rasperry PI. The Cumulocity Python agent is divided into two Python modules. C8yMQTT is sort of a small SDK that wraps a lot of functionality into function calls. piAgent.py Module leverages C8yMQTT.py to implement device specific functions such as sending measurements, updating configurations and more. 

To use this agent, you may sign up for free trial tenant at [Cumulocity](http://cumulocity.com/)

The Raspberry Pi including the SensHat Sensor Array is a great starting point for rapid prototyping.

![PI](pics/rpi.jpg)

Cumulocity IoT enables companies to to quickly and easily implement smart IoT solutions. 

![Dashboard](pics/Dashboard.PNG)

______________________
For more information you can Ask a Question in the [TECHcommunity Forums](http://tech.forums.softwareag.com/techjforum/forums/list.page?product=webmethods-io-b2b).

You can find additional information in the [Software AG TECHcommunity](http://techcommunity.softwareag.com/home/-/product/name/webmethods-io-b2b).
______________________

These tools are provided as-is and without warranty or support. They do not constitute part of the Software AG product suite. Users are free to use, fork and modify them, subject to the license agreement. While Software AG welcomes contributions, we cannot guarantee to include every contribution in the master project.

Contact us at [TECHcommunity](mailto:technologycommunity@softwareag.com?subject=Github/SoftwareAG) if you have any questions.

## C8yMQTT Class

The class C8yMQTT let's you connect your device to the Cumulocity Cloud using mqtt. It provides basic methods to:

* Connect to a cumulocity tenant via mqtt (tls supported)
* Register a device, fetch credentials and store them on the device
* Subscribe to MQTT Topics
* Send and receive MQTT Messages

## piAgent.py Module

To implement a Cumulocity Device Agent you have to cater the C8yMQTT class with device specific functionality (Send Measurements etc.). piAgent.py provides a sample implementation for the Raspberry PI 3.

## Prerequisites for Raspbian distribution

#### Enable SPI Interface

edit /boot/config.txt and enable
dtparam=spi=on


## Getting Started

### Install the agent

checkout the repo and execute install.sh (sudo rights are needed).
This will install all dependencies (python etc.) via apt and pip and create a systemd file "c8y.service" that is deployed to  /etc/systemd/system/  the agent is now registered as a linux daemon. You can start it via service c8y start.

If the requirements are installed for debugging you can also start the agent simply by 

python3 piAgent.py

The agent is designed to run also without a sense hat extension. Then only CPU and Memory Measurements are transmitted.

### Configuration

The agent can be configured via the followin file:

__pi.properties__

the pi.properties file holds device specific parameters.
* host -> Mqtt host (works for cumulocity.com do not change except you running on another instance of Cumulocity )
* port -> Mqtt port it'll be set either to 1883 for tcp or to 8883 for  Transport Encryption via TLS
* tls -> Boolean which indicates whether to use tls or not. Must match the port settings
* cacert -> path to a certificate (pem format) that holds all trusted root certificates
* operations -> all supported operations of the agent which are implemented in an agent module
* subscribe -> Topics the agent will subscribe to.
* deviceType -> speaks for itself
* sendinterval -> Loop time of the RunAgent() function. Indicates in which time frame measurements etc. are read and send
* requiredinterval -> Sets the time frame in which the device must contact the platform in order to be displayed connected. 
* Loglevel -> speaks for itself
* reboot -> will be set by the restart device command to prevent from a infinite loop.
* config_update -> same as reboot
* bootstrap_pwd -> needed for auto registration process

### Device Registration

To autoregister your pi got to In Cumulocity -> Device Management create a new Device Registration entering the serial (could be retrieved by cat /proc/cpuinfo) of your PI. The c8y.properties file will be created automatically. For this the bootstrap_pwd in pi.properties must be set (default).

!!!PLEASE MAKE SURE THAT THE DEVICE IS NOT ALREADY REGISTERED WITH IT'S SERIAL NUMBER!!!
If that is the case either you have to delete the device and re-register or create the c8y.properties by hand and provide correct credentials and client id.

__c8y.properties__  
After successfull registration c8yMQTT will create and store the device credentials file c8y.properties in the same directory as the class. It can be created to provide manual credentials. Remove this file in order to initiate a new auto registration process.

[credentials]  
user =  
tenant =   
password =   
clientid =

If not present the initialized variable is false and the registerDevice method can be used to fetch new credentials. 

### Build in functions

The Agent supports the following functions:

* Configuration -> The content of pi.properties will be displayed under Device Management and can be save to the device
* Restart -> The Raspberry PI an be rebooted via the restart command.
* Send Message to the Device -> Via the Send Message Widget in the Cockpit Application. Text can be send to the PI and will be displayed on the SensHats LED  Matrix
* Transmitted Measurements -> Temperature, Gyroscope, Acceleration, Pressure, Humidity
* Joystick -> Events are created on pressing. __If the joystick is pressed three times__ the PI will start a new registration process. This comes in handy if you have to move it to another tenant.
* Remote Access -> If the remote access microservice is subscribed to the cumulocity tenant and the user has remote access rights remote access can be configured within device management of the agents device
* !!!Experimental!!! Software Update. You can create a zip file of the repo content deploy that to the cumulocity software repository. You should now be able to execute a software update in device management.

