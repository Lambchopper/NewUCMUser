#===================Setup The Script ===================
#Import Stuff for basic functionality
#Note, this is to auto load Server and User IDs
#This will be removed from Production Script
import os
from dotenv import load_dotenv
load_dotenv()

#Import Stuff for data processing
import json

#Import Stuff for AXL API Interactions
import os.path as abspath
import requests
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep import helpers
from zeep.cache import SqliteCache
from zeep.transports import Transport
#===================Setup The Script ===================

#===================Setup Zeep Soap Client===================
#Collect path to the UCM AXL Schema
#The schema files are downloaded from UCM > Applications > Plugins > Cisco AXL Toolkit
wsdl = os.path.abspath('axlsqltoolkit/schema/current/AXLAPI.wsdl')
#location = 'https://{host}:8443/axl/'.format(host=strUCMIP)
location = 'https://{host}:8443/axl/'.format(host=os.getenv('CUCM_ADDRESS'))
binding = "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding"

# Define http session and allow insecure connections
session = Session()
session.verify = False
requests.packages.urllib3.disable_warnings()

#Next Lines are used so I don't have to type passwords for each test
#session.auth = HTTPBasicAuth(strUCMAdmUserID, strUCMAdmPassword)
session.auth = HTTPBasicAuth(os.getenv('AXL_USERNAME'), os.getenv('AXL_PASSWORD'))

#Define a SOAP client
transport = Transport(cache=SqliteCache(), session=session, timeout=20)
client = Client(wsdl=wsdl, transport=transport)
service = client.create_service(binding, location)
#===================Setup Zeep Soap Client===================


#===================Test Logic Below===================

#Read the JSON Template File
#Template Selection Logic to be added later
filename = "StandardUserTemplate.JSON"

with open(filename, 'r') as file:
    templatedata = json.load(file)

#Collect new user specifics, this will be replaced
#by logic to prompt for this data
UserFullName = "John Dough"
UserID = "jdough"
Extension = "5775"
global newUserPhone = "SEP111122223333"

def ConfigurePhone(devType, UID, UFullName, Extn, template)
    #If we're not configuring a Phone, we must be configuring Jabber Soft Phones
    if not devType = "phone":
        #Define the Device name so that it is the Template Prefix + the UserID in Caps
        jabberDevPrefix = template[devType]["name"]
        jabberDevPrefix = jabberDevPrefix.upper()
        jabberDeviceName = jabberDevPrefix.strip() + UserID.upper()
        template[devType]["name"] = jabberDeviceName
    else:
        template[devType]["name"] = newUserPhone

    #Setup the rest of the user specific settings at the device Level
    template[devType]["ownerUserName"]["_value_1"] = UserID
    template[devType]["mobilityUserIdName"]["_value_1"] = UserID

    #If Logged Out Extension is True, we're configuring a generic extension on the Physical Phone for EM
    #Else we are putting the user's extension directly on the phone
    if template["configurations"]["loggedOutExtension"]:
        template[devType]["lines"]["line"][0]["label"] = template["configurations"]["loggedOutExtension"]["label"]
        template[devType]["lines"]["line"][0]["display"] = template["configurations"]["loggedOutExtension"]["label"]
        template[devType]["lines"]["line"][0]["displayAscii"] = template["configurations"]["loggedOutExtension"]["label"]
        template[devType]["lines"]["line"][0]["e164Mask"] = template["configurations"]["loggedOutExtension"]["e164Mask"]
        template[devType]["lines"]["line"][0]["dirn"]["pattern"] = template["configurations"]["loggedOutExtension"]["pattern"]
        template[devType]["lines"]["line"][0]["dirn"]["routePartitionName"]["_value_1"] = \
            template["configurations"]["loggedOutExtension"]["routePartitionName"]

    else:
        template[devType]["lines"]["line"][0]["label"] = UFullName
        template[devType]["lines"]["line"][0]["display"] = UFullName
        template[devType]["lines"]["line"][0]["displayAscii"] = UFullName
        template[devType]["lines"]["line"][0]["dirn"]["pattern"] = Extn
        template[devType]["lines"]["line"][0]["associatedEndusers"]["enduser"]["userId"] = UID

    #Find if the phone object exists yet
    response = service.listPhone(searchCriteria={'name': template[devType]["name"]}, returnedTags={'name': ''})
    
    #if the phone object does not exist, use the addPhone API call to add it
    #Else, remove the read-only elements and use the updatePhone API call to update the existing object
    if not response['return']:
        print("*"*75)
        print("The phone entered does not exist, we will add it")
        print("*"*75)
        response = service.addPhone(phone=template[devType])
    else:
        print("="*75)
        print("The phone entered exists, we will be updating it")
        print("="*75)
        
        #Remove Keys that are only supported by the addPhone method
        template[devType].pop("product")
        template[devType].pop("protocol")
        template[devType].pop("class")

        #Debug Command, Remove in final tool
        #print(json.dumps(template["phone"], indent=4, separators=(',', ': ')))

        #For some reason, the dictionary needs to use the ** to pass
        # the elements to the AXL Update Method.  Referencing phone=template["phone"]
        # generates a type error.  Other AXL Methods seem to work (list and add methods)
        response = service.updatePhone(**template[devType])

#Amend the Directory Number settings to Line Profile settings
if templatedata["configurations"]["directoryNumber"]:
    templatedata["line"]["pattern"] = Extension
    templatedata["line"]["description"] = UserFullName
    templatedata["line"]["alertingName"] = UserFullName
    templatedata["line"]["asciiAlertingName"] = UserFullName

    #Debug Command, Remove in final tool
    #print(json.dumps(templatedata["line"], indent=4, separators=(',', ': ')))

    #Check UCM to see if Extension Exists already
    response = service.listLine(searchCriteria={'pattern': Extension}, returnedTags={'pattern': ''})
    
    #If it doesn't exist, add it, otherwise update it.
    if not response['return']:
        print("*"*75)
        print("The Line entered does not exist, we will add it")
        print("*"*75)
        response = service.addLine(line=templatedata["line"])
    else:
        print("="*75)
        print("The Line entered exists, we will be updating it")
        print("="*75)

        #Remove Dictionary Key used to add a line, but is not used in the Update Method
        templatedata["line"].pop("usage")

        #For some reason, the dictionary needs to use the ** to pass
        # the elements to the AXL Update Method.  Referencing pattern=templatedata["line"]
        # generates a type error.  Other AXL Methods seem to work (list and add methods)
        response = service.updateLine(**templatedata["line"]) 
    

#Amend user specific settings to Device Profile settings
if templatedata["configurations"]["deviceProfile"]: 
    templatedata["deviceProfile"]["name"] = templatedata["deviceProfile"]["name"] + UserFullName
    templatedata["deviceProfile"]["description"] = UserFullName + templatedata["deviceProfile"]["description"]
    templatedata["deviceProfile"]["lines"]["line"][0]["label"] = UserFullName
    templatedata["deviceProfile"]["lines"]["line"][0]["display"] = UserFullName
    templatedata["deviceProfile"]["lines"]["line"][0]["displayAscii"] = UserFullName
    templatedata["deviceProfile"]["lines"]["line"][0]["dirn"]["pattern"] = Extension
    templatedata["deviceProfile"]["lines"]["line"][0]["associatedEndusers"]["enduser"]["userId"] = UserID

    print("="*75)
    print(templatedata["deviceProfile"])
    response = service.addDeviceProfile(deviceProfile=templatedata["deviceProfile"])

#Physical Phones
#If the template wants to change phone settings then
#Check if Phone Exists update Phone, If Phone Does Not Exist add it
if templatedata["configurations"]["phoneSettings"]: 
    ConfigurePhone("phone", UserID, UserFullName, Extension, templatedata)    

#Jabber Soft Phone
if templatedata["configurations"]["jabberCSF"]:
    ConfigurePhone("jabberCSF", UserID, UserFullName, Extension, templatedata)
