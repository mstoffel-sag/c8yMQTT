#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
'''
Created on 19.12.2017

@author: mstoffel
'''

from c8yMQTT import C8yMQTT
from configparser import RawConfigParser
import logging
import sys
import os
from threading import Thread
import threading
import time
import io
import psutil
import socket
import json
from sensehat import Sense

startUp = False
stopEvent = threading.Event()
config_file = 'pi.properties'
config = RawConfigParser()
config.read(config_file)

c8y = C8yMQTT(config.get('device','host'),
               int(config.get('device','port')),
               config.getboolean('device','tls'),
               config.get('device','cacert'),
               loglevel=logging.getLevelName(config.get('device', 'loglevel')))

sense = Sense(c8y)

def sendConfiguration():
    with open(config_file, 'r') as configFile:
            configString=configFile.read()
    configString = '113,"' + configString + '"'
    c8y.logger.debug('Sending Config String:' + configString)
    c8y.publish("s/us",configString)

def getserial():
    # Extract serial from cpuinfo file can be set static by removing the try catch block
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

       
def sendCPULoad():
    tempString = "995,," + str(psutil.cpu_percent())
    c8y.logger.debug("Sending CPULoad: " + tempString)
    c8y.publish("s/uc/pi", tempString)

def sendMemory():
    tempString = "996,," +  str(psutil.virtual_memory().total >> 20) + "," + str(psutil.virtual_memory().available >> 20) + "," + str(psutil.swap_memory().total >> 20)
    c8y.logger.debug("Sending Memory: " + tempString)
    c8y.publish("s/uc/pi", tempString)


def sendMeasurements(stopEvent, interval):
    c8y.logger.info('Starting sendMeasurement with interval: '+ str(interval))
    try:
        sendCPULoad()
        sendMemory()
        sense.send()
        c8y.logger.info('sendMeasurements called')
        while not stopEvent.wait(interval):
            sendCPULoad()
            sendMemory()
            sense.send()
            c8y.logger.info('sendMeasurements called')
        c8y.logger.info('sendMeasurement was stopped..')
    except (KeyboardInterrupt, SystemExit):
        c8y.logger.info('Exiting sendMeasurement...')
        sys.exit()



def on_message_default(client, obj, msg):
    message = msg.payload.decode('utf-8')
    c8y.logger.info("Message Received: " + msg.topic + " " + str(msg.qos) + " " + message)

    if message.startswith('510'):
        Thread(target=restart).start()
    if message.startswith('513'):
        Thread(target=updateConfig,args=(message,)).start()
    if message.startswith('520'):
       c8y.logger.info('Received Config Upload. Sending config')
       sendConfiguration()
       setCommandExecuting('c8y_SendConfiguration')
       setCommandSuccessfull('c8y_SendConfiguration')
    if message.startswith('1001'):
        sense.displayMessage(message)
    if message.startswith('1003'):
        fields = message.split(",")
        tcp_host = fields[2]
        tcp_port = int(fields[3])
        connection_key = fields[4]
        c8y.logger.info('Received Remote Connect.')
        c8y.remoteConnect(tcp_host,tcp_port,connection_key,config.get('device','host'))


def on_message_startup(client, obj, msg):
    # Can be used to process messages while startup
    message = msg.payload.decode('utf-8')
    c8y.logger.info("On_Message_Startup Received: " + msg.topic + " " + str(msg.qos) + " " + message)


def setCommandExecuting(command):
    c8y.logger.info('Setting command: '+ command + ' to executing')
    c8y.publish('s/us','501,'+command)

def setCommandSuccessfull(command):
    c8y.logger.info('Setting command: '+ command + ' to successful')
    c8y.publish('s/us','503,'+command)

def setCommandFailed(command,errorMessage):
    c8y.logger.info('Setting command: '+ command + ' to failed cause: ' +errorMessage)
    c8y.publish('s/us','502,'+command+','+errorMessage)

def restart():
        if config.get('device','reboot') != '1':
            c8y.logger.info('Rebooting')
            c8y.publish('s/us','501,c8y_Restart')
            config.set('device','reboot','1')
            with open(config_file, 'w') as configfile:
                config.write(configfile)
            c8y.disconnect()
            c8y.reboot("Received restart command from platform.")
        else:
            c8y.logger.info('Received restart but already in progress')

def updateConfig(message):
        
        c8y.logger.info('UpdateConfig')
        if config.get('device','config_update') != '1':
            plain_message = c8y.getPayload(message).strip('\"')
            with open(config_file, 'w') as configFile:
                config.readfp(io.StringIO(plain_message))
                c8y.logger.info('Current config:' + str(config.sections()))
                config.set('device','config_update','1')
                config.write(configFile)
            c8y.logger.info('Sending Config Update executing')
            setCommandExecuting('c8y_Configuration')
            c8y.serviceRestart("ConfigUpdate")
        else:
            c8y.logger.info('Received Config Update but already in progress')


def runAgent():
    # Enter Device specific values
    stopEvent.clear()
    if c8y.initialized == False:
        serial = getserial()
        c8y.logger.info('Not initialized. Try to registering Device with serial: '+ serial)
        c8y.registerDevice(serial,
                           config.get('device','name') + '-' +serial ,
                           config.get('device','devicetype'),
                           getserial(),
                           gethardware(),
                           getrevision(),
                           config.get('device','operations'),
                           config.get('device','requiredinterval'),
                           config.get('device','bootstrap_pwd'))
    if c8y.initialized == False:
        c8y.logger.info('Could not register. Exiting.')
        exit()
    ## Connect Startup
    connected = c8y.connect(on_message_startup,config.get('device', 'subscribe'))
    c8y.logger.info('Connection Result:' + str(connected))

    if connected == 5:
        c8y.reset()
    if not connected == 0:
        c8y.serviceRestart("Error conncting code: " +str(connected))

    c8y.publish("s/us", "114,"+ config.get('device','operations'))
    if config.get('device','reboot') == '1':
        c8y.logger.info('reboot is active. Publishing Acknowledgement..')
        setCommandSuccessfull('c8y_Restart')
        config.set('device','reboot','0')
        with open(config_file, 'w') as configfile:
            config.write(configfile)
    if config.get('device','config_update') == '1':
        c8y.logger.info('Config Update is active. Publishing Acknowledgement..')
        setCommandSuccessfull('c8y_Configuration')
        config.set('device','config_update','0')
        with open(config_file, 'w') as configfile:
            config.write(configfile)
    c8y.createSmartRestTemplates()
    time.sleep(2)
    sendConfiguration()
    time.sleep(2)
    c8y.disconnect()
    time.sleep(2)
    c8y.connect(on_message_default,config.get('device', 'subscribe'))
    c8y.logger.info('Starting sendMeasurements.')
    sendThread = Thread(target=sendMeasurements, args=(stopEvent, int(config.get('device','sendinterval'))))
    sendThread.start()

runAgent()






