# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
'''
Created on 19.12.2017

@author: mstoffel
'''

import logging
import signal
import sys
from threading import Thread
import threading
import time

from sense_hat import SenseHat

from c8yAgent import C8yAgent

stopEvent = threading.Event()
sense = SenseHat()
c8y = C8yAgent("mqtt.iot.softwareag.com", 1883, loglevel=logging.DEBUG)

reset = 0
resetMax = 3


def sendTemperature():
    tempString = "211," + str(sense.get_temperature())
    c8y.logger.debug("Sending Temperature  measurement: " + tempString)
    c8y.publish("s/us", tempString)


def sendHumidity():
    tempString = "992,," + str(sense.get_humidity())
    c8y.logger.debug("Sending Humidity  measurement: " + tempString)
    c8y.publish("s/uc/pi", tempString)


def sendPressure():
    tempString = "994,," + str(sense.get_pressure())
    c8y.logger.debug("Sending Pressure  measurement: " + tempString)
    c8y.publish("s/uc/pi", tempString)


def sendAcceleration():
    acceleration = sense.get_accelerometer_raw()
    x = acceleration['x']
    y = acceleration['y']
    z = acceleration['z']
    accString = "991,," + str(x) + "," + str(y) + "," + str(z)
    c8y.logger.debug("Sending Acceleration measurement: " + accString)
    c8y.publish("s/uc/pi", accString)


def sendGyroscope():
    o = sense.get_orientation()
    pitch = o["pitch"]
    roll = o["roll"]
    yaw = o["yaw"]
    gyString = "993,," + str(pitch) + "," + str(roll) + "," + str(yaw)
    c8y.logger.debug("Sending Gyroscope measurement: " + gyString)
    c8y.publish("s/uc/pi", gyString)


def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6] == 'Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"
    c8y.logger.debug('Found Serial: ' + cpuserial)
    return cpuserial


def on_message(client, obj, msg):
    print("Message Received: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


def sendMeasurements(stopEvent, interval):
    try:
        while not stopEvent.wait(interval):
            listenForJoystick()
            sendTemperature()
            sendAcceleration()
            sendHumidity()
            sendPressure()
            sendGyroscope()
        c8y.logger.info('sendMeasurement was stopped..')
    except (KeyboardInterrupt, SystemExit):
        c8y.logger.info('Exiting...')
        sys.exit()


def listenForJoystick():
    for event in sense.stick.get_events():
        c8y.logger.debug("The joystick was {} {}".format(event.action, event.direction))
        c8y.publish("s/us", "400,c8y_Joystick,{} {}".format(event.action, event.direction))
        if event.action == 'pressed' and event.direction == 'middle':
            global reset
            global resetMax
            reset += 1
            if reset >= resetMax:
                stopEvent.set()
                c8y.logger.info('Resetting....')
                c8y.reset()
                runAgent()


def runAgent():
    # Enter Device specific values
    stopEvent.clear()
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
    c8y.connect(on_message, ["s/ds", "s/dc/pi", "s/e"])
    sendThread = Thread(target=sendMeasurements, args=(stopEvent, 2))
    sendThread.start()

runAgent()




# time.sleep(10)
# stopEvent.set()
