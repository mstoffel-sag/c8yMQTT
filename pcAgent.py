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
from c8yMQTT import C8yMQTT
import time
import io
import platform
import psutil


config_file = 'pi.properties'

#Configure Serial will be used for device Registration.
serial = '0123456789'

# Configure Model
model = 'MyPcModel'

config = RawConfigParser()
config.read(config_file)

reset = 0
resetMax = 3
stopEvent = threading.Event()
c8y = C8yMQTT(config.get('device','host'),
               int(config.get('device','port')),
               config.getboolean('device','tls'),
               config.get('device','cacert'),
               loglevel=logging.getLevelName(config.get('device', 'loglevel')))


def sendCPULoad():
    tempString = "995,," + str(psutil.cpu_percent())
    c8y.logger.debug("Sending CPULoad: " + tempString)
    c8y.publish("s/uc/pi", tempString)

def sendMemory():
    tempString = "996,," +  str(psutil.virtual_memory().total >> 20) + "," + str(psutil.virtual_memory().available >> 20) + "," + str(psutil.swap_memory().total >> 20)
    c8y.logger.debug("Sending Memory: " + tempString)
    c8y.publish("s/uc/pi", tempString)


def sendConfiguration():
    with open(config_file, 'r') as configFile:
            configString=configFile.read()
    configString = '113,"' + configString + '"'
    c8y.logger.debug('Sending Config String:' + configString)
    c8y.publish("s/us",configString)



def sendMeasurements(stopEvent, interval):
    try:
        while not stopEvent.wait(interval):
            sendCPULoad()
            sendMemory()
        c8y.logger.info('sendMeasurement was stopped..')
    except (KeyboardInterrupt, SystemExit):
        c8y.logger.info('Exiting sendMeasurement...')
        sys.exit()



def on_message(client, obj, msg):
    message = msg.payload.decode('utf-8')
    c8y.logger.info("Message Received: " + msg.topic + " " + str(msg.qos) + " " + message)
 
    if message.startswith('510'):
        Thread(target=restart).start()

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
        c8y.logger.info('Not initialized. Try to registering Device with serial: '+ serial)
        c8y.registerDevice(serial,
                           platform.system() + '_'+ serial,
                           config.get('device','devicetype'),
                           serial,
							model,
                           ' '.join(platform.linux_distribution()),
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


runAgent()
