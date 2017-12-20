'''
Created on 05.12.2017

@author: mstoffel
'''
from configparser import ConfigParser
import logging
from logging.handlers import RotatingFileHandler
import os, time, threading, ssl
import sys

import paho.mqtt.client as mqtt


class C8yAgent(object):
    '''
    Cumulocity Python Agent
    Usage Example:
    Create a new Agent Object by providing
    c8y = C8yAgent("mqtt.iot.softwareag.com", 1883)
    if c8y.initialized == False:
      c8y.registerDevice("testdevice", "Test device", "c8y_TestDevice", "serialNumberTest", "Meine Hardware Nummer", "reversion 1234","c8y_Restart,c8y_Message")
    '''
    
    
    def __init__(self,mqtthost,mqttport, loglevel=logging.INFO):
        '''
        Read Configuration file
        Connect to configured tenant
        do device onboarding if not already registered
        '''
        self.logger = logging.getLogger('C8yAgent')
        self.logger.setLevel(loglevel)
        self.logHandler = RotatingFileHandler('c8yAgent.log', maxBytes=2*1024*1024,backupCount=5)
        self.logger.addHandler(self.logHandler)
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        
        self.config = ConfigParser()
        self.configFile = 'c8y.properties'
        self.mqtthost = mqtthost
        self.mqttport = mqttport
        
        if not os.path.exists(self.configFile):
            self.initialized = False
            self.logger.error('Config file does not exist, please call registerDevice() of edit Config: '+ self.configFile)
            return 


        self.config.read(self.configFile)
        self.tenant= self.config.get('credentials', 'tenant')
        self.user= self.config.get('credentials', 'user')
        self.clientId= self.config.get('credentials', 'clientid')
        self.password= self.config.get('credentials', 'password')
        
        if self.password == '' or self.user == '' or self.tenant == '' or self.clientId == '':
            self.logger.error('Coould not  initialize Agent. Missing Values in c8y.properties')
            self.initialized = False
        else:
            self.logger.info('Successfully initialized.')
            self.initialized = True
            
    def on_connect(self,client, userdata, flags, rc):
        self.logger.debug("connect: " + str(rc))

    def on_publish(self,client, obj, mid):
        self.logger.debug("publish: " + str(mid))

    def on_subscribe(self,client, obj, mid, granted_qos):
        self.logger.debug("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_log(self,client, obj, level, string):
        self.logger.debug("Log: " +string)
    
    def connect(self,on_message,topics):
        
        ''' Will connect to the mqtt broker
            
            Keyword Arguments:
            on_message -- has to be a method that will be called for new messages distributed to a subscribed topic
            topics -- a list of topics strings like s/ds to subscribe to
        
        ''' 
        if self.initialized == False:
            self.logger.error('Not initialized, please call registerDevice() of edit c8y.properties file')
            return
        self.client = mqtt.Client(client_id=self.clientId)
        self.client.username_pw_set(self.tenant+'/'+ self.user, self.password)
        self.client.on_message = on_message
        self.client.on_publish = self.on_publish
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_log = self.on_log
        self.client.connect(self.mqtthost, self.mqttport)
        self.client.loop_start()
        self.client.subscribe('s/ds', 2)
        
        for t in topics:
            self.client.subscribe(t, 2)
            self.logger.debug('Subscribing to topic: ' + t)

#        self.client.publish("s/us", "100,My Python Client,c8y_TestDevice",2)

    def registerDevice(self,clientId,deviceName,deviceType,serialNumber,hardwareModel,reversion,operationString):
        
        '''
        Will register a new device to the c8y platform.
        Please create a device registration on the platfomrm bevorhand
        
        Keyword Arguments:
        clientId -- external Id of the device
        deviceName -- Device Name (displayed in the UI)
        deviceType -- Device Type
        serialNumber -- Serial of the device
        hardwareModel -- Hardware Model of the device
        reversion -- Hardware Reversion of the device
        operationString -- Comma seperated string which operations the device supports e.g 'c8y_Message,c8y_Restart
        
        '''
        self.clientId = clientId
        self.deviceName = deviceName
        self.deviceType = deviceType
        self.serialNumber = serialNumber
        self.hardwareModel = hardwareModel
        self.reversion = reversion
        
        self.client = mqtt.Client(client_id=self.clientId)
        self.client.username_pw_set('management/devicebootstrap', 'Fhdt1bb1f')
        self.client.on_message = self.__on_messageRegistration
        self.client.on_publish = self.on_publish
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_log = self.on_log
        self.client.connect(self.mqtthost, self.mqttport)
        self.client.loop_start()
        self.client.subscribe("s/dcr")
        self.client.subscribe("s/e")
        
        for x in range(0,5):
            if self.initialized == False:
                self.client.publish("s/ucr", "", 2)
                time.sleep(5)
            else:
                self.initialized = True
                break
        self.client.loop_stop(True)
        self.client.disconnect()
            
        if self.initialized == False:
            self.logger.error( 'Could not register device. Exiting')
            exit
            
        self.logger.debug( 'Reconnection with received creds')
        self.client.username_pw_set(self.tenant+'/'+self.user,self.password)
        self.client.connect(self.mqtthost, self.mqttport)
        self.client.loop_start()
        self.logger.debug( 'Publishing Device Meta Data...')
        self.client.publish("s/us", "100,"+self.deviceName+","+self.deviceType,2)
        self.client.publish("s/us", "110,"+self.serialNumber+","+self.hardwareModel+","+ self.reversion,2)
        self.client.publish("s/us", "114,"+ operationString,2)
        
        self.logger.debug( 'Stop Loop')
        self.client.loop_stop(True)
        self.client.disconnect()


    def publish(self,topic,payload):
        self.client.publish(topic,payload,2)
        
    def reset(self):
        self.client.loop_stop(force=True)
        self.client.disconnect()
        os.remove(self.configFile)
          
    def __on_messageRegistration(self,client,userdata,message):
        self.logger.debug("Received Registration Message: " + message.payload)
        if (message.payload.startswith("70")):
            self.logger.info("Got Device Credentials")
            messageArray = message.payload.split(',')
            self.tenant = list(messageArray)[1]
            self.user = list(messageArray)[2]
            self.password = self.__getPassword(message.payload,3)
            self.config.add_section('credentials')
            self.config.set('credentials', 'user', self.user)
            self.config.set('credentials', 'tenant', self.tenant)
            self.config.set('credentials', 'password', self.password)
            self.config.set('credentials', 'clientid', self.clientId)
            self.config.write(open(self.configFile, 'w'))
            self.logger.debug('Config file written:')
            self.initialized = True
            
    def __getPassword(self,text,maxcount):
        pos=0
        count=0
        for char in text:
            if char==',':
                count += 1
                if count==maxcount:
                    break
            pos += 1
        pwd = text[pos+1:]
        self.logger.debug('got password: ' + pwd)
        return(pwd)


        
        
        
        
