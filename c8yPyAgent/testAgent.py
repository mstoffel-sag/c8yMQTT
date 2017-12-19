'''
Created on 05.12.2017

@author: mstoffel

Example implementation of the c8yAgent class. Can be adjusted to any device.
'''

import threading
from threading import Thread
import random
import sys
import time

from c8yAgent import C8yAgent
import logging




stopEvent = threading.Event()

def on_message(client, obj, msg):
    print("Message Received: " +msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


def sendMeasurements(stopEvent,interval):
    try:
         while not stopEvent.wait(interval):
            temp = random.uniform(10.0,45.5)
            c8y.publish("s/us", "211,"+ str(temp))

    except (KeyboardInterrupt, SystemExit):
        print 'Exinting...'
        sys.exit()
        
def testThead(stopEvent,interval):
    try:
        while not stopEvent.wait(interval):
                print 'waiting 20'
                time.sleep(20)  
        print 'Stopped...'
    except (KeyboardInterrupt, SystemExit):
        print 'Exinting...'
        sys.exit()      

c8y = C8yAgent("mqtt.iot.softwareag.com", 1883,loglevel=logging.DEBUG)

if c8y.initialized == False:
    c8y.registerDevice("marcodevice", 
                       "Marcos Test device", 
                       "c8y_TestDevice", 
                       "serialNumberTest", 
                       "Meine Hardware Nummer", 
                       "reversion 1234",
                       "c8y_Restart,c8y_Message")

if c8y.initialized == False:
    exit()
   
c8y.connect(on_message,["s/ds","s/dc/pi","s/e"])

Thread(target = sendMeasurements, args=(stopEvent,4)).start()
Thread(target = testThead, args=(stopEvent,2)).start()
time.sleep(10)
stopEvent.set()