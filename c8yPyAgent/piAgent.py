# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
'''
Created on 19.12.2017

@author: mstoffel
'''

from configparser import RawConfigParser
import logging
import sys
from threading import Thread
import threading


from sense_hat import SenseHat

from c8yAgent import C8yAgent


stopEvent = threading.Event()
sense = SenseHat()

config = RawConfigParser()
config.read('pi.properties')
loglevel = logging.getLevelName(config.get('device', 'INFO'))
host = config.get('host','mqtt.cumulocity.com')
port = config.get('port','1883')
reset = 0
resetMax = 3

c8y = C8yAgent(host, port, loglevel=loglevel)

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

def getrevision():
    # Extract board revision from cpuinfo file
    myrevision = "0000"
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:8]=='Revision':
                length=len(line)
                myrevision = line[11:length-1]
        f.close()
    except:
        myrevision = "ERROR0000"
    c8y.logger.debug('Found HW Version: ' + myrevision)
    return myrevision

def gethardware():
    # Extract board revision from cpuinfo file
    myrevision = "0000"
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:8]=='Hardware':
                length=len(line)
                myrevision = line[11:length-1]
        f.close()
    except:
        myrevision = "ERROR0000"
    c8y.logger.debug('Found Hardware: ' + myrevision)
    return myrevision

def on_message(client, obj, msg):
    message = msg.payload.decode('utf-8')
    c8y.logger.info("Message Received: " + msg.topic + " " + str(msg.qos) + " " + message)


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
        c8y.logger.info('Exiting sendMeasurement...')
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
                c8y.logger.info('Resetting c8y.properties initializing re-register device....')
                c8y.reset()
                runAgent(config)


def runAgent(configuration):
    # Enter Device specific values
    stopEvent.clear()
    if c8y.initialized == False:
        serial = getserial()
        c8y.registerDevice(serial,
                           "PI_" + serial,
                           configuration.get('device', 'devicetype'),
                           serial,
                           gethardware(),
                           getrevision(),
                           configuration.get('device', 'operations'))
    if c8y.initialized == False:
        exit()
    c8y.connect(on_message, list(configuration.get('device', 'subscribe')))
    sendThread = Thread(target=sendMeasurements, args=(stopEvent, 5))
    sendThread.start()

runAgent(config)
#time.sleep(100)



# time.sleep(10)
# stopEvent.set()
