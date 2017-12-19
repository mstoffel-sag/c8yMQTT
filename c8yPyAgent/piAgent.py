'''
Created on 19.12.2017

@author: mstoffel
'''

from thread import start_new_thread
import sys
import time

from sense_hat import SenseHat
from c8yAgent import C8yAgent
import logging


sense = SenseHat()
c8y = C8yAgent("mqtt.iot.softwareag.com", 1883,loglevel=logging.DEBUG)

def sendTemperature():
    tempString = "211,"+str(sense.get_temperature())
    print "Sending Temperature  measurement: "+tempString 
    c8y.publish("s/us", tempString)

def sendHumidity():
    tempString = "992,,"+str(sense.get_humidity())
    print "Sending Humidity  measurement: "+tempString 
    c8y.publish("s/uc/pi", tempString)

def sendPressure():
    tempString = "994,,"+str(sense.get_pressure())
    print "Sending Pressure  measurement: "+tempString 
    c8y.publish("s/uc/pi", tempString)


def sendAcceleration():
    acceleration = sense.get_accelerometer_raw()
    x = acceleration['x']
    y = acceleration['y']
    z = acceleration['z']
    accString = "991,,"+str(x)+","+str(y)+","+str(z)
    print "Sending Acceleration measurement: " +accString
    c8y.publish("s/uc/pi",accString)

def sendGyroscope():
    o = sense.get_orientation()
    pitch = o["pitch"]
    roll = o["roll"]
    yaw = o["yaw"]
    gyString = "993,,"+str(pitch)+","+str(roll)+","+str(yaw)
    print "Sending Gyroscope measurement: " +gyString
    c8y.publish("s/uc/pi",gyString)

def getserial():
  # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
      f = open('/proc/cpuinfo','r')
      for line in f:
        if line[0:6]=='Serial':
          cpuserial = line[10:26]
      f.close()
    except:
      cpuserial = "ERROR000000000"
    return cpuserial

def on_message(client, obj, msg):
    print("Message Received: " +msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

def sendMeasurements():
    try:
        while True:
            sendTemperature()  
            sendAcceleration()
            sendHumidity()
            sendPressure()
            sendGyroscope()
            time.sleep(5)
    except (KeyboardInterrupt, SystemExit):
        print 'Exiting...'
        sys.exit()
        
def listenForJoystick():
    try:
        while True:
            for event in sense.stick.get_events():
                print("The joystick was {} {}".format(event.action, event.direction))
                c8y.publish("s/us","400,c8y_Joystick,{} {}".format(event.action, event.direction))
    except (KeyboardInterrupt, SystemExit):
      print 'Exiting...'
      sys.exit()  
                         
if c8y.initialized == False:
    c8y.registerDevice(getserial(), 
                       "PI_" + getserial(), 
                       "c8y_PI", 
                       getserial(), 
                       "PI3", 
                       "a02082",
                       "c8y_Restart,c8y_Message")

if c8y.initialized == False:
    exit()
   
c8y.connect(on_message,["s/ds","s/dc/pi","s/e"])


