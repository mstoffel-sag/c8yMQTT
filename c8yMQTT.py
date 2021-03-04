'''
Created on 05.12.2017

@author: mstoffel
'''
from configparser import RawConfigParser
import logging
from logging.handlers import RotatingFileHandler
import os, time, threading, ssl
import sys
import re
import paho.mqtt.client as mqtt
import smartrest
from threading import Thread
import threading
import time

class C8yMQTT(object):
    '''
    Cumulocity Python Agent
    Usage Example:
    Create a new Agent Object by providing
    c8y = C8yAgent("mqtt.iot.softwareag.com", 1883)
    if c8y.initialized == False:
      c8y.registerDevice("testdevice", "Test device", "c8y_TestDevice", "serialNumberTest", "Meine Hardware Nummer", "reversion 1234","c8y_Restart,c8y_Message")
    '''
    def readCredentials(self):
        self.config.read(self.configFile)
        self.tenant= self.config.get('credentials', 'tenant')
        self.user= self.config.get('credentials', 'user')
        self.clientId= self.config.get('credentials', 'clientid')
        self.password= self.config.get('credentials', 'password')
        #self.logger = logging.getLogger('readCredentials')
    
    def __init__(self,clientId, mqtthost,mqttport,tls,cacert,cert_auth,client_cert,client_key,loglevel=logging.INFO):
        '''
        Read Configuration file
        Connect to configured tenant
        do device onboarding if not already registered
        '''
        self.refresh_token_interval = 60
        self.stop_event = threading.Event()
        self.stop_event.clear()
        self.clientId = clientId
        self.ackpub = -1
        self.lastpub = -1
        self.connected = -1
        self.logger = logging.getLogger('C8yAgent')
        self.logger.setLevel(loglevel)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        self.logHandler = RotatingFileHandler('c8yAgent.log', maxBytes=1*1024*1024,backupCount=5)
        self.logHandler.setFormatter(formatter) 

        self.logHandlerStOut = logging.StreamHandler(sys.stdout)
        self.logHandlerStOut.setFormatter(formatter)

        self.logger.addHandler(self.logHandlerStOut)

        self.logger.addHandler(self.logHandler)
        
        self.topic_ack=[]
        self.config = RawConfigParser()
        self.configFile = 'c8y.properties'
        self.mqtthost = mqtthost
        self.mqttport = mqttport
        self.cacert = cacert
        self.tls = tls
        self.cert_auth = cert_auth
        self.client_cert = client_cert
        self.client_key = client_key
        
        self.token = None
        
        self.templates = smartrest.templates

        if not self.cert_auth:

            if not os.path.exists(self.configFile):
                self.initialized = False
                self.logger.error('Config file does not exist, please call registerDevice() of edit Config: '+ self.configFile)
                return 

            self.readCredentials()
            
            if (self.password == '' or self.user == '' or self.tenant == '' or self.clientId == '') and not self.cert_auth:
                self.logger.error('Coould not  initialize Agent. Missing Values in c8y.properties')
                self.initialized = False
            else:
                self.logger.info('Successfully initialized.')
                self.initialized = True

        else:
            self.logger.info('Using certificate authentication. Successfully initialized.')
            self.initialized = True

    def on_connect(self,client, userdata, flags, rc):
        self.logger.info("on_connect result: " + str(rc))
        self.connected=rc
        if self.cert_auth:
            self.logger.info("Starting refresh token thread ")
            refresh_token_thread = Thread(target=self.refresh_token)
            refresh_token_thread.start()
   


    def check_subs(self):
        wcount=0
        while wcount<10: #wait loop
            self.logger.info('Check Subtopic_ack:' +str(self.topic_ack))
            if len(self.topic_ack)==0:
                self.logger.info('Successfuly Subscribed')
                return True
            time.sleep(1)
            wcount+=1
        return False

    def publish(self,topic,payload,qos=1):
        ret=self.client.publish(topic,payload,qos)
        self.logger.debug('publish ret:' + str(ret))
        return ret
        # self.lastpub = ret[1]
        # maxtry
        # count = 0
        # while self.lastpub != self.ackpub:
        #     count += count
        # return True

    def on_publish(self,client, obj, mid):
        self.logger.debug("publish: " + str(mid))
        self.ackpub = mid

    def subscribe_topics(self,topics,qos=0):
        self.topic_ack = []
        topics = topics.split(',')
        if self.cert_auth:
            topics.append('s/dat')
        self.logger.info("topics to subscribe: " +str(topics))
   
        for t in topics:
            try:
                self.logger.debug("Subscribing to topic "+str(t)+" qos: " + str(qos))
                r=self.client.subscribe(t,qos)
                if r[0]==0:
                    self.logger.debug("subscribed to topic "+str(t)+" return code" +str(r) + 'r[1] ' + str(r[1]))
                    self.topic_ack.append(r[1]) #keep track of subscription
                else:
                    self.logger.error("error on subscribing: " + t + ' return code:'+str(r))

            except Exception as e:
                self.logger.error("Exception on subscribe"+str(e))

    def refresh_token(self):
        while True:
            self.logger.info("Refreshing Token")
            self.client.publish("s/uat", "",2)
            if self.stop_event.wait(timeout=self.refresh_token_interval):
                self.logger.info("Exit Refreshing Token Thread")
                break

            
        self.logger.info("Refresh token thread stopped")

    def on_subscribe(self,client, obj, mid, granted_qos):
        
        """removes mid valuse from subscribe list"""
        if len(self.topic_ack)==0:
            self.logger.info('Sucessfully  Subscribed')
            return
        for index,t in enumerate(self.topic_ack):
            #self.logger.info('Index: ' + str(index) + ' t:' + str(t) + ' mid:' +str(mid))
            if t==mid:
             #   self.logger.info('Removing sub ' + str(mid))
                self.topic_ack.pop(index)#remove it

    def on_log(self,client, obj, level, string):
        self.logger.debug("on_log: " +string)
    
    def on_disconnect(self,client, userdata, rc):
        self.logger.debug("on_disconnect rc: " +str(rc))
        # if rc==5:
        #     self.reset()
        #     return
        if rc!=0:
            self.logger.error("Disconnected! Try to reconnect: " +str(rc))
            self.client.reconnect()
        if self.cert_auth:
            self.logger.error("Stopping refresh token thread")
            self.stop_event.set
        

    def connect(self,on_message,topics):
        self.connected=-1
        ''' Will connect to the mqtt broker
            
            Keyword Arguments:
            on_message -- has to be a method that will be called for new messages distributed to a subscribed topic
            topics -- a list of topics strings like s/ds to subscribe to
        
        ''' 
        if self.initialized == False:
            self.logger.error('Not initialized, please call bootstrap() of edit c8y.properties file. Alternatively you can use cert auth.')
            return

        self.client = mqtt.Client(client_id=self.clientId)

        if self.tls:
            if self.cert_auth:
                self.client.tls_set(self.cacert,
                                    certfile=self.client_cert,
                                    keyfile=self.client_key,
                                    tls_version=ssl.PROTOCOL_TLSv1_2,
                                    cert_reqs= ssl.CERT_NONE
                                    )
                                    
            else:
                self.client.tls_set(self.cacert) 
                self.client.username_pw_set(self.tenant+'/'+ self.user, self.password)
        else:
            self.client.username_pw_set(self.tenant+'/'+ self.user, self.password)

        
        self.client.on_message = on_message
        self.client.on_publish = self.on_publish
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_log = self.on_log
        if self.cert_auth:
            self.logger.debug('Using certificate authenticaiton' )
        else:
            self.logger.debug('Using Basic Authentication withe Creds: ' + self.tenant + '/' + self.user + ' pwd: ' + self.password )
        self.logger.info('Connecting to: ' + self.mqtthost + ':' + str(self.mqttport) )
        self.client.connect(self.mqtthost, self.mqttport,keepalive=60)
        self.client.loop_start()
        while self.connected == -1:
            self.logger.debug('Waiting for Connect.' + str(self.connected))
            time.sleep(2)
        self.logger.debug('After Waiting for Connect.' + str(self.connected))
        if not self.connected == 0:
            self.logger.debug('Connect not successfull return to client. Code:' + str(self.connected))
            self.client.disconnect()
            return self.connected
        self.subscribe_topics(topics)
        if not self.check_subs():
            self.logger.error("Could not subscribe to: " + topics)
            return 17
        

        return self.connected

    def initDevice(self,deviceName,deviceType,serialNumber,hardwareModel,reversion,operationString,requiredInterval):
        '''
        deviceName -- Device Name (displayed in the UI)
        deviceType -- Device Type
        serialNumber -- Serial of the device
        hardwareModel -- Hardware Model of the device
        reversion -- Hardware Reversion of the device
        operationString -- Comma seperated string which operations the device supports e.g 'c8y_Message,c8y_Restart
        requiredInterval -- indicates in which interval the device must talk to the platform
        '''

        self.deviceName = deviceName
        self.deviceType = deviceType
        self.serialNumber = serialNumber
        self.hardwareModel = hardwareModel
        self.reversion = reversion
        self.requiredInterval = requiredInterval
        self.operationString = operationString

        self.logger.info( 'Initialize Device')
        self.client.publish("s/us", "100,"+self.deviceName+","+self.deviceType,2).wait_for_publish()
        self.client.publish("s/us", "110,"+self.serialNumber+","+self.hardwareModel+","+ self.reversion,2)
        self.client.publish("s/us", "117,"+ self.requiredInterval,2)
        self.client.publish("s/us", "114,"+ self.operationString,2)
        self.client.publish("s/us", "118,c8yAgent",2)

        self.logger.info( 'Device created')

    def bootstrap(self,bootstrap_password):
        
        '''
        Will register a new device to the c8y platform.
        Please create a device registration on the platfomrm bevorhand
        
        Keyword Arguments:
        clientId -- external:wq
        Id of the device
        '''


        self.user ='devicebootstrap' 
        self.password = bootstrap_password
        self.tenant = 'management'
        self.initialized = True
        self.connect(self.__on_messageRegistration,'s/e,s/dcr')
        self.initialized = False
        while True:
            if self.initialized == False:
                self.logger.info('Waiting for Credentials')
                self.client.publish("s/ucr", "", 2)
                time.sleep(2)
            else:
                self.logger.info('Credentials Received')
                break
        self.disconnect()

    def createSmartRestTemplates(self):
        self.logger.info("Creating SmartResetTemplates.")
        self.client.publish(smartrest.id, smartrest.templates,2)

    
    def reset(self):
        self.initialized = False
        self.logger.info('resetting')
        self.logger.debug('loop stopped')
        self.disconnect()
        self.logger.debug('client disconnected')
        if os.path.isfile(self.configFile):
            os.remove(self.configFile)
            self.logger.debug('config file removed')
        else:
            self.logger.debug('config file already missing')

    def disconnect(self):

        self.logger.info('Disconnect')
        self.client.disconnect()
        self.client.loop_stop()
        self.connected=False

    def __on_messageRegistration(self,client,userdata,message):
        message = message.payload.decode('utf-8')
        self.logger.info("Received Registration Message: " + message)
        if (message.startswith("70")):
            self.logger.info("Got Device Credentials")
            messageArray = message.split(',')
            self.tenant = list(messageArray)[1]
            self.user = list(messageArray)[2]
            self.password = self.__getPassword(message,3)
            self.config = RawConfigParser()
            self.config.add_section('credentials')
            self.config.set('credentials', 'user', self.user)
            self.config.set('credentials', 'tenant', self.tenant)
            self.config.set('credentials', 'password', self.password)
            self.config.set('credentials', 'clientid', self.clientId)
            self.config.write(open(self.configFile, 'w'))
            self.logger.info('Config file written:')
            self.initialized = True

    def __on_message_createdevice(self,client,userdata,message):
        message = message.payload.decode('utf-8')
        self.logger.info("__on_message_createdevice Received Registration Message: " + message)

            
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


    def getPayload(self,message):

        pos = [s.start() for s in re.finditer(',', message)]
        print(str(pos))
        payload = message[pos[1]+1:]
        self.logger.debug('Payload: '+payload )
        return payload
    




        
        
        
