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
from c8yAgent import C8yAgent
import re
import time
from daemon import runner


class PiDaemon():
    
    def __init__(self):
        
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path =  '/tmp/piAgent.pid'
        self.pidfile_timeout = 5


        self.stopEvent = threading.Event()
        self.sense = SenseHat()
        self.config_file = 'pi.properties'
        self.config = RawConfigParser()
        self.config.read(self.config_file)
        
        self.reset = 0
        self.resetMax = 3
        
        self.c8y = C8yAgent(self.config.get('device','host'),
                       int(self.config.get('device','port')),
                       self.config.getboolean('device','tls'),
                       self.config.get('device','cacert'),
                       loglevel=logging.getLevelName(self.config.get('device', 'loglevel')))

    def getPayload(self,message):
    
        pos = [s.start() for s in re.finditer(',', message)]
        print(str(pos))
        payload = message[pos[1]+1:]
        self.c8y.logger.debug('Payload: '+payload )
        return payload
    
    
    def sendTemperature(self):
        tempString = "211," + str(self.sense.get_temperature())
        self.c8y.logger.debug("Sending Temperature  measurement: " + tempString)
        self.c8y.publish("s/us", tempString)
    
    
    def sendHumidity(self):
        tempString = "992,," + str(self.sense.get_humidity())
        self.c8y.logger.debug("Sending Humidity  measurement: " + tempString)
        self.c8y.publish("s/uc/pi", tempString)
    
    
    def sendPressure(self):
        tempString = "994,," + str(self.sense.get_pressure())
        self.c8y.logger.debug("Sending Pressure  measurement: " + tempString)
        self.c8y.publish("s/uc/pi", tempString)
    
    
    def sendAcceleration(self):
        acceleration = self.sense.get_accelerometer_raw()
        x = acceleration['x']
        y = acceleration['y']
        z = acceleration['z']
        accString = "991,," + str(x) + "," + str(y) + "," + str(z)
        self.c8y.logger.debug("Sending Acceleration measurement: " + accString)
        self.c8y.publish("s/uc/pi", accString)
    
    
    def sendGyroscope(self):
        o = self.sense.get_orientation()
        pitch = o["pitch"]
        roll = o["roll"]
        yaw = o["yaw"]
        gyString = "993,," + str(pitch) + "," + str(roll) + "," + str(yaw)
        self.c8y.logger.debug("Sending Gyroscope measurement: " + gyString)
        self.c8y.publish("s/uc/pi", gyString)
    
    def sendConfiguration(self):
        with open(self.config_file, 'r') as configFile:
                configString=configFile.read()
        configString = '113,"' + configString + '"'
        self.c8y.logger.debug('Sending Config String:' + configString)
        self.c8y.publish("s/us",configString)
    
    def getserial(self):
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
        self.c8y.logger.debug('Found Serial: ' + cpuserial)
        return cpuserial
    
    def getrevision(self):
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
        self.c8y.logger.debug('Found HW Version: ' + myrevision)
        return myrevision
    
    def gethardware(self):
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
        self.c8y.logger.debug('Found Hardware: ' + myrevision)
        return myrevision
    
           
    
    
    
    def sendMeasurements(self,stopEvent, interval):
        try:
            while not stopEvent.wait(interval):
                self.listenForJoystick()
                self.sendTemperature()
                self.sendAcceleration()
                self.sendHumidity()
                self.sendPressure()
                self.sendGyroscope()
            self.c8y.logger.info('sendMeasurement was stopped..')
        except (KeyboardInterrupt, SystemExit):
            self.c8y.logger.info('Exiting sendMeasurement...')
            sys.exit()
    
    
    def listenForJoystick(self):
        for event in self.sense.stick.get_events():
            self.c8y.logger.debug("The joystick was {} {}".format(event.action, event.direction))
            self.c8y.publish("s/us", "400,c8y_Joystick,{} {}".format(event.action, event.direction))
            if event.action == 'pressed' and event.direction == 'middle':
                
                self.resetMax
                self.reset += 1
                if reset >= self.resetMax:
                    self.stopEvent.set()
                    self.c8y.logger.info('Resetting c8y.properties initializing re-register device....')
                    self.c8y.reset()
                    self.runAgent()
    
    
    
    def on_message(self,client, obj, msg):
        message = msg.payload.decode('utf-8')
        self.c8y.logger.info("Message Received: " + msg.topic + " " + str(msg.qos) + " " + message)
        if message.startswith('1001'):
            messageArray =  shlex.shlex(message, posix=True)
            messageArray.whitespace =',' 
            messageArray.whitespace_split =True 
            self.sense.show_message(list(messageArray)[-1])
            self.sense.clear
        if message.startswith('510'):
            self.c8y.logger.info('Rebooting')
            self.config.set('device','reboot','1')
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            self.c8y.publish('s/us','501,c8y_Restart')
    #        os.system('sudo reboot')
        if message.startswith('513'):
            self.c8y.logger.info('Received new configuration:' + message)
            plain_message = self.getPayload(message).strip('\"')
            with open(self.config_file, 'w') as configFile:
                configFile.write(plain_message)
                self.config.read(self.config_file)
            self.c8y.publish('s/us','501,c8y_Configuration')
            time.sleep(4)
            self.c8y.publish('s/us','503,c8y_Configuration')
    
     

    def run(self):
        self.stopEvent.clear()
        self.reset=0
        if self.c8y.initialized == False:
            serial = self.getserial()
            self.c8y.registerDevice(serial,
                           "PI_" + serial,
                           self.config.get('device','devicetype'),
                           self.getSerial(),
                           self.gethardware(),
                           self.getrevision(),
                           self.config.get('device','operations'),
                           self.config.get('device','requiredinterval'))
            if self.c8y.initialized == False:
                exit()

        self.c8y.connect(self.on_message, self.config.get('device', 'subscribe').split(','))
        self.c8y.publish("s/us", "114,"+ self.config.get('device','operations'))
        if self.config.get('device','reboot') == '1':
            self.c8y.logger.info('reboot is active. Publishing Acknowledgement..')
            self.c8y.publish('s/us','503,c8y_Restart')
            self.config.set('device','reboot','0')
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
        self.sendConfiguration()
    
        sendThread = Thread(target=self.sendMeasurements, args=(self.stopEvent, int(self.config.get('device','sendinterval'))))
        sendThread.start()
class DaemonRunner(object):

    self.parse_args()
    self.app = app
    self.daemon_context = DaemonContext()
    self.daemon_context.stdin = open(app.stdin_path, 'r') 
    # for linux /dev/tty must be opened without buffering and with b
    self.daemon_context.stdout = open(app.stdout_path, 'wb+',buffering=0)
    #  w+ -> wb+
    self.daemon_context.stderr = open(
    app.stderr_path, 'wb+', buffering=0)


pi_daemon = PiDaemon()
daemon_runner = runner.DaemonRunner(pi_daemon)
daemon_runner.do_action()

