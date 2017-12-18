'''
Created on 05.12.2017

@author: mstoffel
'''

from thread import start_new_thread
import random
import sys
import time

from c8yAgent import C8yAgent


def on_message(client, obj, msg):
    print("Message Received: " +msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    


def sendMeasurements():
    try:
        while True:
            temp = random.uniform(10.0,45.5)
            c8y.publish("s/us", "211,"+ str(temp))
            time.sleep(5)
    except (KeyboardInterrupt, SystemExit):
        print 'Exinting...'
        sys.exit()
        

c8y = C8yAgent("mqtt.iot.softwareag.com", 1883)

if c8y.initialized == False:
    print 'Not initialized. Try to register'
    c8y.registerDevice("marcodevice", "Marcos Test device", "c8y_TestDevice", "serialNumberTest", "Meine Hardware Nummer", "reversion 1234","c8y_Restart,c8y_Message")

if c8y.initialized == False:
    print 'could not register device.'
    exit
   
c8y.connect(on_message,["s/ds","s/dc/pi","s/e"])
start_new_thread(sendMeasurements())