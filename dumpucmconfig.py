
#===================Setup The Script ===================
#Import Stuff for basic functionality
#Note, this is to auto load Server and User IDs
#This will be removed from Production Script
import os
from dotenv import load_dotenv
load_dotenv()

#Imports Needed for the Soap Connections
from os.path import abspath
import requests
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep import helpers
from zeep.cache import SqliteCache
from zeep.transports import Transport

#imports for other stoof
import time
from lxml import etree
import json


#===================Setup Zeep Soap Client===================
#Collect path to the UCM AXL Schema
#The schema files are downloaded from UCM > Applications > Plugins > Cisco AXL Toolkit
wsdl = abspath('axlsqltoolkit/schema/current/AXLAPI.wsdl')
location = 'https://{host}:8443/axl/'.format(host=os.getenv('CUCM_ADDRESS'))
binding = "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding"

# Define http session and allow insecure connections
session = Session()
session.verify = False
requests.packages.urllib3.disable_warnings()
session.auth = HTTPBasicAuth(os.getenv('AXL_USERNAME'), os.getenv('AXL_PASSWORD'))

#Define a SOAP client
transport = Transport(cache=SqliteCache(), session=session, timeout=20)
client = Client(wsdl=wsdl, transport=transport)
service = client.create_service(binding, location)
#===================Setup Zeep Soap Client===================

#===================Test UCM Queries===================
##UCM AXL Call to retrieve Phone Device Specific Settings
print("="*50)
print("Collect UCM Object")
print("="*50)

#Change Object Type for personal Reference
ucmObjectType = "DN"
#Set ucmObject Variable for your needs
#ucmObject = '{4826E8A0-2143-0653-7EBF-1ECF441E3097}'
ucmObject = 'RDI-Steve Drgon'

#uncomment as neessary (List Line to get UUID, Get Line to dump full DN results)
#response = service.getLine(uuid=ucmObject)
#response = service.listLine(searchCriteria={'pattern': ucmObject},returnedTags={'pattern': True,'description': True})
#response = service.getPhone(name=ucmObject)
response = service.listRemoteDestination(name=ucmObject)

print("="*50)
print("Convert From Zeep Object to Dictionary")
print("="*50)

#Silly Cisco, you should have consistant output
#The vendor config from phone devices needs special handling
#We don't typically set these values during a MACD, so we will ignore them
try:
    del response["return"]["phone"]["vendorConfig"]
except:
    pass

print(response)

ucmDict = helpers.serialize_object(response)


print("="*50)
print("Save Dictionary as JSON")
print("="*50)

filename = ucmObjectType + "-Template.json"
with open(filename, 'w') as file:
    json.dump(ucmDict, file, indent=4, separators=(',', ': '))

print("="*50)
print("Dictionary Post Helper Conversion")
print("="*50)

