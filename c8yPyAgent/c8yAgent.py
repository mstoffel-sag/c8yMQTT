'''
Created on 05.12.2017

@author: mstoffel
'''
from ConfigParser import SafeConfigParser
import os, time, threading, ssl

import paho.mqtt.client as mqtt


class C8yAgent(object):
    '''
    Cumulocity Python Agent
    '''
    def __init__(self,mqtthost,mqttport):
        '''
        Read Configuration file
        Connect to configured tenant
        do device onboarding if not already registered
        '''
        self.config = SafeConfigParser()
        self.configFile = 'c8y.properties'
        self.mqtthost = mqtthost
        self.mqttport = mqttport
        
        if not os.path.exists(self.configFile):
            self.initialized = False
            print('Config file does not exist, please call registerDevice() of edit Config: '+ self.configFile)
            return 


        self.config.read(self.configFile)
        self.tenant= self.config.get('credentials', 'tenant')
        self.user= self.config.get('credentials', 'user')
        self.clientId= self.config.get('credentials', 'clientid')
        self.password= self.config.get('credentials', 'password')
        
        if self.password == '' or self.user == '' or self.tenant == '' or self.clientId == '':
            self.initialized = False
        else:
            self.initialized = True
            
    def on_connect(self,client, userdata, flags, rc):
        print("rc: " + str(rc))

    def on_publish(self,client, obj, mid):
        print("mid: " + str(mid))

    def on_subscribe(self,client, obj, mid, granted_qos):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_log(self,client, obj, level, string):
        print("Log: " +string)
    
    def connect(self,on_message,topics):
        if self.initialized == False:
            print('Not initialized, please call registerDevice() of edit c8y.properties file')
            return
        self.client = mqtt.Client(client_id=self.clientId)
        self.client.username_pw_set(self.tenant+'/'+ self.user, self.password)
        self.client.on_message = on_message
        self.client.on_publish = self.on_publish
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_log = self.on_log
        self.client.connect(self.mqtthost, self.mqttport)
#        self.client.loop_forever(1)
        self.client.loop_start()
        self.client.subscribe('s/ds', 2)
        
        for t in topics:
            self.client.subscribe(t, 2)

#        self.client.publish("s/us", "100,My Python Client,c8y_TestDevice",2)

    def registerDevice(self,clientId,deviceName,deviceType,serialNumber,hardwareModel,reversion,operationString):
        
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
        print 'after initialize loop'
        self.client.loop_stop(True)
        self.client.disconnect()
            
        if self.initialized == False:
            print 'Could not register device. Exiting'
            exit
            
        print 'Reconnection with received creds...'
        self.client.username_pw_set(self.tenant+'/'+self.user,self.password)
        self.client.connect(self.mqtthost, self.mqttport)
        self.client.loop_start()
        print 'Publishing Device Meta Data...'
        self.client.publish("s/us", "100,"+self.deviceName+","+self.deviceType,2)
        self.client.publish("s/us", "110,"+self.serialNumber+","+self.hardwareModel+","+ self.reversion,2)
        self.client.publish("s/us", "114,"+ operationString,2)
        
        print 'Stop Loop'
        self.client.loop_stop(True)
        self.client.disconnect()


    def publish(self,topic,payload):
        self.client.publish(topic,payload,2)
        

          
    def __on_messageRegistration(self,client,userdata,message):
        print("Received Registration Message: " + message.payload)
        if (message.payload.startswith("70")):
            print("Got Device Credentials")
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
            print('Config file written:')
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
        return(text[pos+1:])


        
        
        
        