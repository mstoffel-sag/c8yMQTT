import requests
import os
from requests.auth import HTTPBasicAuth 
import json
import sys
from time import sleep

c8y_user = os.environ.get('C8Y_USER')
c8y_pwd = os.environ.get('C8Y_PWD')
c8y_url = os.environ.get('C8Y_URL')
c8y_tenant = os.environ.get('C8Y_TENANT')


def delete_device (externalId):
    r = requests.get(c8y_url + '/identity/externalIds/c8y_Serial/' + externalId,auth=HTTPBasicAuth(c8y_user, c8y_pwd))
    try:
        internal_id = r.json() ['managedObject']['id']
        r = requests.delete(c8y_url + '/user/' + c8y_tenant+ '/users/device_' + externalId,auth=HTTPBasicAuth(c8y_user, c8y_pwd))
        print("Delete User response: " + str(r.status_code))
        r = requests.delete(c8y_url + '/inventory/managedObjects/'+ internal_id,auth=HTTPBasicAuth(c8y_user, c8y_pwd))
        print("Delete Device: " + str(r.status_code))
    except:
        print ('Error fetching id')


def accept_registration(externalId):
    for i in range(10):
        r = requests.put(c8y_url + '/devicecontrol/newDeviceRequests/' + externalId,auth=HTTPBasicAuth(c8y_user, c8y_pwd),json={"status" : "ACCEPTED"})
        print("Accept Registration response: " + r.text)
        sleep(1)
   
def create_registration(externalId):
    r = requests.post(c8y_url + '/devicecontrol/newDeviceRequests',auth=HTTPBasicAuth(c8y_user, c8y_pwd),json={"id" : externalId})
    print("Create Registration response: " + r.text)

if __name__ == '__main__':
    globals()[sys.argv[1]](sys.argv[2])
