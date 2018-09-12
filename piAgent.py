#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
'''
Created on 19.12.2017

@author: mstoffel
'''

from configparser import RawConfigParser
import logging
import sys
import os
from threading import Thread
import threading
import shlex
from sense_hat import SenseHat
from c8yMQTT import C8yMQTT
import time
import io

stopEvent = threading.Event()
sense = SenseHat()
config_file = 'pi.properties'
config = RawConfigParser()
config.read(config_file)

reset = 0
resetMax = 3

c8y = C8yMQTT(config.get('device','host'),
               int(config.get('device','port')),
               config.getboolean('device','tls'),
               config.get('device','cacert'),
               loglevel=logging.getLevelName(config.get('device', 'loglevel')))


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

def sendConfiguration():
    with open(config_file, 'r') as configFile:
            configString=configFile.read()
    configString = '113,"' + configString + '"'
    c8y.logger.debug('Sending Config String:' + configString)
    c8y.publish("s/us",configString)

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
                runAgent()



def on_message(client, obj, msg):
    message = msg.payload.decode('utf-8')
    c8y.logger.info("Message Received: " + msg.topic + " " + str(msg.qos) + " " + message)
    if message.startswith('1001'):
        Thread(target=setCommandExecuting,args=('c8y_Message',)).start()
        messageArray =  shlex.shlex(message, posix=True)
        messageArray.whitespace =',' 
        messageArray.whitespace_split =True 
        sense.show_message(list(messageArray)[-1])
        sense.clear
        Thread(target=setCommandSuccessfull,args=('c8y_Message',)).start()
    if message.startswith('510'):
        Thread(target=restart).start()
    if message.startswith('513'):
        Thread(target=updateConfig,args=(message,)).start()
#    if message.startswith('520'):
#        c8y.logger.info('Received Config Upload. Sending config')
#        sendConfiguration() 

def setCommandExecuting(command):
    c8y.logger.info('Setting command: '+ command + ' to executing')
    c8y.publish('s/us','501,'+command)

def setCommandSuccessfull(command):
    c8y.logger.info('Setting command: '+ command + ' to successful')
    c8y.publish('s/us','503,'+command)

def restart():
        if config.get('device','reboot') != '1':
            c8y.logger.info('Rebooting')
            c8y.publish('s/us','501,c8y_Restart')
            config.set('device','reboot','1')
            with open(config_file, 'w') as configfile:
                config.write(configfile)
            c8y.disconnect()
            os.system('sudo reboot')
  #          os.system('sudo service c8y restart')
        else:
            c8y.logger.info('Received Reboot but already in progress')

def updateConfig(message):
        
        c8y.logger.info('UpdateConfig')
        if config.get('device','config_update') != '1':
            plain_message = c8y.getPayload(message).strip('\"')
            with open(config_file, 'w') as configFile:
                config.readfp(io.StringIO(plain_message))
                c8y.logger.debug('Current config:' + str(config.sections()))
                config.set('device','config_update','1')
                config.write(configFile)
            c8y.logger.info('Sending Config Update executing')
            c8y.publish('s/us','501,c8y_Configuration')
            c8y.disconnect()
            c8y.logger.info('Restarting Service')
            os.system('sudo service c8y restart')
        else:
            c8y.logger.info('Received Config Update but already in progress')




def runAgent():
    # Enter Device specific values
    stopEvent.clear()
    global reset
    reset=0
    if c8y.initialized == False:
        serial = getserial()
        c8y.logger.info('Not initialized. Try to registering Device with serial: '+ serial)
        c8y.registerDevice(serial,
                           "RPI_" + serial,
                           config.get('device','devicetype'),
                           getserial(),
                           gethardware(),
                           getrevision(),
                           config.get('device','operations'),
                           config.get('device','requiredinterval'),
                           config.get('device','bootstrap_pwd'))
    if c8y.initialized == False:
        exit()

    c8y.connect(on_message, config.get('device', 'subscribe').split(','))
    if c8y.connected:

        c8y.publish("s/us", "114,"+ config.get('device','operations'))
        if config.get('device','reboot') == '1':
            c8y.logger.info('reboot is active. Publishing Acknowledgement..')
            c8y.publish('s/us','503,c8y_Restart')
            config.set('device','reboot','0')
            with open(config_file, 'w') as configfile:
                config.write(configfile)
        if config.get('device','config_update') == '1':
            c8y.logger.info('Config Update is active. Publishing Acknowledgement..')
            c8y.publish('s/us','503,c8y_Configuration')
            config.set('device','config_update','0')
            with open(config_file, 'w') as configfile:
                config.write(configfile)
        sendConfiguration()
    
        sendThread = Thread(target=sendMeasurements, args=(stopEvent, int(config.get('device','sendinterval'))))
        sendThread.start()

    #time.sleep(100)

runAgent()



# time.sleep(10)
# stopEvent.set()
