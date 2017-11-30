#!/usr/bin/env python
# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import ConfigParser
import time, threading, ssl
import shlex
import signal
from sense_hat import SenseHat
from threading import Thread



receivedMessages = []

def on_message(client, userdata, message):
  print("Received operation " + str(message.payload))
  if (message.payload.startswith("510")):
     print("Simulating device restart...")
     publish("s/us", "501,c8y_Restart");
     print("...restarting...")
     time.sleep(1)
     publish("s/us", "503,c8y_Restart");
     print("...done...")
  elif (message.payload.startswith("1001")):
     messageArray =  shlex.shlex(message.payload, posix=True)
     messageArray.whitespace =',' 
     messageArray.whitespace_split =True 
     sense.show_message(list(messageArray)[-1])
     sense.clear
      
def sendMeasurements():
  try:
    sendTemperature()  
    sendAcceleration()
    sendHumidity()
    sendPressure()
    sendGyroscope()
    thread = threading.Timer(3, sendMeasurements)
    thread.daemon=True
    thread.start()
    while True: time.sleep(1000)
  except (KeyboardInterrupt, SystemExit):
    print 'Received keyboard interrupt, quitting ...'
    sys.exit()


def publish(topic, message, waitForAck = False):
  mid = client.publish(topic, message, 2)[1]
  if (waitForAck):
    while mid not in receivedMessages:
      time.sleep(0.25)

def on_publish(client, userdata, mid):
  receivedMessages.append(mid)

def sendTemperature():
    tempString = "211,"+str(sense.get_temperature())
    print "Sending Temperature  measurement: "+tempString 
    publish("s/us", tempString)

def sendHumidity():
    tempString = "992,,"+str(sense.get_humidity())
    print "Sending Humidity  measurement: "+tempString 
    publish("s/uc/pi", tempString)

def sendPressure():
    tempString = "994,,"+str(sense.get_pressure())
    print "Sending Pressure  measurement: "+tempString 
    publish("s/uc/pi", tempString)


def sendAcceleration():
    acceleration = sense.get_accelerometer_raw()
    x = acceleration['x']
    y = acceleration['y']
    z = acceleration['z']
    accString = "991,,"+str(x)+","+str(y)+","+str(z)
    print "Sending Acceleration measurement: " +accString
    publish("s/uc/pi",accString)

def sendGyroscope():
    o = sense.get_orientation()
    pitch = o["pitch"]
    roll = o["roll"]
    yaw = o["yaw"]
    gyString = "993,,"+str(pitch)+","+str(roll)+","+str(yaw)
    print "Sending Gyroscope measurement: " +gyString
    publish("s/uc/pi",gyString)


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
    
def listenForJoystick():
    while True:
        for event in sense.stick.get_events():
          print("The joystick was {} {}".format(event.action, event.direction))
          publish("s/us","400,c8y_Joystick,{} {}".format(event.action, event.direction))

sense = SenseHat()
client = mqtt.Client(client_id=getserial())

client.username_pw_set("lhind/pi", "manage123")
client.on_message = on_message
client.on_publish = on_publish

client.connect("lhind.cumulocity.com", 1883)
client.loop_start()
publish("s/us", "100,Python MQTT,c8y_MQTTDevice", True)
publish("s/us", "110,"+getserial()+",MQTT test model,Rev0.1")
publish("s/us", "114,c8y_Message,c8y_Restart")
client.subscribe("s/ds")
client.subscribe("s/dc/pi")

joystickThread = Thread(target=listenForJoystick) 
joystickThread.start()
  
sendMeasurements()
