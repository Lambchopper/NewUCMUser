#===================Setup The Script ===================
#Import Stuff for basic functionality
#Note, this is to auto load Server and User IDs
#This will be removed from Production Script
import os
from dotenv import load_dotenv
load_dotenv()

#Import Stuff for flow cotrol
import sys

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

#===================Read the Template File from Disk===================
#Read the JSON Template File
#Template Selection Logic to be added later
filename = "StandardUserTemplate.JSON"

with open(filename, 'r') as file:
    templatedata = json.load(file)

#===================Setup Variables===================
#Setup Variables for the script
global newUserPhone
listConfiguredDevices = []

#Collect new user specifics
#This will be replaced by logic to prompt for this data
UserFirstName = "John"
UserLastName = "Dough"
UserID = "jdough"
Extension = "5775"
newUserPhone = "SEP111122223333"
EmailAddress = "jdough@convergedtechgroup.com"

UserFullName = UserFirstName + " " + UserLastName

if templatedata["configurations"]["SNR"]:
    print("="*75)
    print("This template has Single Number Reach Enabled.")
    print("Please provide the user's Cell Phone Number.")
    print("The number should be entered as dialed: EG 916318675309")
    print("="*75)
    mobileNum = input("Cell Number: ")
    print("="*75)

#If the template says to configure CCX and the the template is configured
#to not use the Primary Line as the Agent line (E.G. not use a second extension)
#then prompt the user for the New IPCC extension
if templatedata["configurations"]["CCX"]:
    if not templatedata["ccxParameters"]["agentLineUsePrimary"]:
        print("="*75)
        print("This template is enabled for a CCX Agent Extension.")
        print("Please provide the extension we should configure for CCX.")
        print("="*75)
        ccxExtension = input("Agent Extension: ")
        print("="*75)


#===================Configuring the User Account===================

#Add the basic new user info to the template dictionary Variable
templatedata["user"]["firstName"] = UserFirstName
templatedata["user"]["displayName"] = UserFullName
templatedata["user"]["lastName"] = UserLastName
templatedata["user"]["userid"] = UserID
templatedata["user"]["mailid"] = EmailAddress
templatedata["user"]["directoryUri"] = EmailAddress
templatedata["user"]["userIdentity"] = EmailAddress
templatedata["user"]["nameDialing"] = UserLastName + UserFirstName
templatedata["user"]["telephoneNumber"] = Extension
templatedata["user"]["selfService"] = Extension

#Check to see if the user account exists
print("="*75)
print("Checking UCM for User ID: " + UserID)
print("="*75)

#If we get a valid response without a Zeep Failure the User Exists
#Otherwise if Zeep returns an Exception, user does not
try:
    response = service.getUser(userid=UserID)
    UserExists = True
except:
    print("="*75)
    print("User Does Not Exist.")
    print("="*75)
    print("If this should be an LDAP Sychronized Account, Select (N)o and correct that.")
    print("Otherwise select (Y)es to add the user as a UCM Local User")
    print("="*75)
    AddLocalUser = input("Y or N: ")
    AddLocalUser = AddLocalUser.lower()
    UserExists = False
    
    #Validate User Input
    for i in range(1, 4):

        #Three strikes and you're outta here!
        if i == 3:
            print("Incorrect Input, must be Y or N")
            print("Failed too many times, terminating script")
            print("="*75)
            sys.exit()

        #if the user entered the correct value, exit loop
        #Else make them do it again.
        if AddLocalUser == "y" or AddLocalUser == "n":
            break
        else:
            AddLocalUser = input("Y or N: ")
            AddLocalUser = AddLocalUser.lower()

    #If the user selected No, Terminate Script    
    if AddLocalUser == "n":
        print("Terminating Script")
        print("="*75)
        sys.exit()
    
    #if we get here we are adding a new Local User
    print("="*75)
    print("Creating Enabled Local User: " + templatedata["user"]["displayName"])
    print("="*75)
    response = service.addUser(templatedata["user"])

#If the user Exists we need to see if the user is LDAP Synced Or Not because not 
# all fields are editable for an LDAP User Account.
if UserExists:
    if response["return"]["user"]["ldapDirectoryName"]["_value_1"] is None:
        print("="*75)
        print(UserID + " exists as a Local End User in UCM")
        print("="*75)

    else:
        print("="*75)
        print( UserID + "is synced from the " + response["return"]["user"]["ldapDirectoryName"]["_value_1"] + " LDAP Directory.")
        print("="*75)
        #We need to remove all Keys from the Dictionary that are not editable for LDAP users
        templatedata["user"].pop("lastName")
        templatedata["user"].pop("firstName")
        templatedata["user"].pop("displayName")
        templatedata["user"].pop("title")
        templatedata["user"].pop("directoryUri")
        templatedata["user"].pop("telephoneNumber")
        templatedata["user"].pop("homeNumber")
        templatedata["user"].pop("mobileNumber")
        templatedata["user"].pop("pagerNumber")
        templatedata["user"].pop("mailid")
        templatedata["user"].pop("department")
        templatedata["user"].pop("manager")

#===================Define Function used to add Phone objects===================
def ConfigurePhone(devType, UID, UFullName, Extn, template):
    #If we're not configuring a physical phone, we must be configuring Jabber soft phones
    if not devType == "phone":
        #Define the Device name so that it is the Template Prefix + the UserID in Caps
        jabberDevPrefix = template[devType]["name"]
        jabberDevPrefix = jabberDevPrefix.upper()
        jabberDeviceName = jabberDevPrefix.strip() + UserID.upper()
        template[devType]["name"] = jabberDeviceName
    else:
        template[devType]["name"] = newUserPhone
        
    #Setup the rest of the user specific settings at the device Level
    template[devType]["description"] = UserFullName + template[devType]["description"]
    template[devType]["ownerUserName"]["_value_1"] = UserID
    template[devType]["mobilityUserIdName"]["_value_1"] = UserID

    #If Logged Out Extension is True, we're configuring a generic extension on the Physical Phone for EM
    #Else we are putting the user's extension directly on the phone
    if template["configurations"]["loggedOutExtension"] and devType == "phone":
        template[devType]["lines"]["line"][0]["label"] = template["loggedOutExtension"]["label"]
        template[devType]["lines"]["line"][0]["display"] = template["loggedOutExtension"]["label"]
        template[devType]["lines"]["line"][0]["displayAscii"] = template["loggedOutExtension"]["label"]
        template[devType]["lines"]["line"][0]["e164Mask"] = template["loggedOutExtension"]["e164Mask"]
        template[devType]["lines"]["line"][0]["dirn"]["pattern"] = template["loggedOutExtension"]["pattern"]
        template[devType]["lines"]["line"][0]["dirn"]["routePartitionName"]["_value_1"] = template["loggedOutExtension"]["routePartitionName"]
        template[devType]["lines"]["line"][0].pop("associatedEndusers")

    else:
        template[devType]["lines"]["line"][0]["label"] = UFullName + template[devType]["lines"]["line"][0]["label"]
        template[devType]["lines"]["line"][0]["display"] = UFullName + template[devType]["lines"]["line"][0]["display"]
        template[devType]["lines"]["line"][0]["displayAscii"] = UFullName + template[devType]["lines"]["line"][0]["displayAscii"]
        template[devType]["lines"]["line"][0]["dirn"]["pattern"] = Extn
        template[devType]["lines"]["line"][0]["associatedEndusers"]["enduser"]["userId"] = UID

    #Find if the phone object exists yet
    response = service.listPhone(searchCriteria={'name': template[devType]["name"]}, returnedTags={'name': ''})
    
    #if the phone object does not exist, use the addPhone API call to add it
    #Else, remove the read-only elements and use the updatePhone API call to update the existing object
    if not response['return']:
        print("="*75)
        print("The Device Type " + devType + ": " + template[devType]["name"] + " does not exist, we will add it")
        print("="*75)
        
        #Debug Command, Remove in final tool
        #print(json.dumps(template[devType], indent=4, separators=(',', ': ')))

        response = service.addPhone(phone=template[devType])
    else:
        print("="*75)
        print("The Device Type " + devType + ": " + template[devType]["name"] + " exists, we will be updating it")
        print("="*75)
        
        #Remove Keys that are only supported by the addPhone method
        template[devType].pop("product")
        template[devType].pop("protocol")
        template[devType].pop("class")

        #For some reason, the dictionary needs to use the ** to pass
        # the elements to the AXL Update Method.  Referencing phone=template["phone"]
        # generates a type error.  Other AXL Methods seem to work (list and add methods)
        response = service.updatePhone(**template[devType])
    
    #Return the device name when the function is complete
    return str(template[devType]["name"])

#===================Directory Number===================
#Amend the Directory Number settings if the extension does not exist
#add it.  This must be done first in order for the Line Appearences to work
#when configuring phones. If the DN is not present, changing the Line Appearences
#will generate an error.
templatedata["line"]["pattern"] = Extension
templatedata["line"]["description"] = UserFullName + templatedata["line"]["description"]
templatedata["line"]["alertingName"] = UserFullName + templatedata["line"]["alertingName"]
templatedata["line"]["asciiAlertingName"] = UserFullName + templatedata["line"]["asciiAlertingName"]

#Check UCM to see if Extension Exists already
response = service.listLine(searchCriteria={'pattern': Extension}, returnedTags={'pattern': ''})

#If it doesn't exist, add it, otherwise update it.
if not response['return']:
    print("="*75)
    print("The Directory Number " +  templatedata["line"]["pattern"] + " does not exist, we will add it")
    print("="*75)
    response = service.addLine(line=templatedata["line"])

else:
    print("="*75)
    print("The Directory Number " +  templatedata["line"]["pattern"] + " exists, we will be updating it")
    print("="*75)

    #Remove Dictionary Key used to add a line, but is not used in the Update Method
    templatedata["line"].pop("usage")

    #For some reason, the dictionary needs to use the ** to pass
    # the elements to the AXL Update Method.  Referencing pattern=templatedata["line"]
    # generates a type error.  Other AXL Methods seem to work (list and add methods)
    response = service.updateLine(**templatedata["line"]) 
        
#===================Add/Update Phone Objects===================
#Phones, Use above function to insert all Phone Types
#And collect the device name returned for later association

#Physical Phone
if templatedata["configurations"]["phoneSettings"]: 
    result = ConfigurePhone("phone", UserID, UserFullName, Extension, templatedata)    
    listConfiguredDevices.append(result)

#Jabber Soft Phone
if templatedata["configurations"]["jabberCSF"]:
    result = ConfigurePhone("jabberCSF", UserID, UserFullName, Extension, templatedata)
    listConfiguredDevices.append(result)

#Jabber Android Soft Phone
if templatedata["configurations"]["jabberAndroid"]:
    result = ConfigurePhone("jabberAndroid", UserID, UserFullName, Extension, templatedata)
    listConfiguredDevices.append(result)

#Jabber iPhone Soft Phone
if templatedata["configurations"]["jabberiPhone"]:
    result = ConfigurePhone("jabberiPhone", UserID, UserFullName, Extension, templatedata)
    listConfiguredDevices.append(result)

#Jabber Tablet Soft Phone
if templatedata["configurations"]["jabberTablet"]:
    result = ConfigurePhone("jabberTablet", UserID, UserFullName, Extension, templatedata)
    listConfiguredDevices.append(result)

#Associate the Devices that were just created with the End User Account
print("="*75)
print("Associating phones and extension with " + UserID + ".")
print("="*75)

#Create a Dictionary for the phones we need associate
DevicesToAdd = {
    "device": []
}

#Loop through the list and add the phones to the dictionary variable
for item in listConfiguredDevices:
    DevicesToAdd["device"].append(item)

#Define a list variable with the extension info for the Primary Line
#this has to be done after the phones are created
ExtensionToAdd = [{"pattern": templatedata["line"]["pattern"],"routePartitionName": templatedata["line"]["routePartitionName"]["_value_1"]}]

#Send it to UCM to associate the phones and set the Primary extension with the user ID
response = service.updateUser(userid=UserID,associatedDevices=DevicesToAdd,primaryExtension=ExtensionToAdd)

#===================Add Extension Mobility Profile===================
#Amend user specific settings to Device Profile settings
if templatedata["configurations"]["deviceProfile"]: 
    templatedata["deviceProfile"]["name"] = templatedata["deviceProfile"]["name"] + UserFullName
    templatedata["deviceProfile"]["description"] = UserFullName + " " + templatedata["deviceProfile"]["description"]
    templatedata["deviceProfile"]["lines"]["line"][0]["label"] = UserFullName + templatedata["deviceProfile"]["lines"]["line"][0]["label"]
    templatedata["deviceProfile"]["lines"]["line"][0]["display"] = UserFullName + templatedata["deviceProfile"]["lines"]["line"][0]["display"]
    templatedata["deviceProfile"]["lines"]["line"][0]["displayAscii"] = UserFullName + templatedata["deviceProfile"]["lines"]["line"][0]["displayAscii"]
    templatedata["deviceProfile"]["lines"]["line"][0]["dirn"]["pattern"] = Extension
    templatedata["deviceProfile"]["lines"]["line"][0]["associatedEndusers"]["enduser"]["userId"] = UserID

    print("="*75)
    print("Configuring the " + templatedata["deviceProfile"]["name"] + " Extension Mobility Profile.")
    print("="*75)

    response = service.addDeviceProfile(deviceProfile=templatedata["deviceProfile"])

    #Associate Profile with End User account
    #Create a Dictionary with just the items we need and pass them to the updateUser Method
    ProfileToAdd = [{"profileName": templatedata["deviceProfile"]["name"]}]

    response = service.updateUser(userid=UserID,phoneProfiles=ProfileToAdd)

#===================Add Single Number Reach===================
if templatedata["configurations"]["SNR"]:
   
    #Configure the Remote Destination Profile
    templatedata["remoteDestinationProfile"]["name"] = templatedata["remoteDestinationProfile"]["name"] + UserFullName
    templatedata["remoteDestinationProfile"]["description"] = UserFullName
    templatedata["remoteDestinationProfile"]["userId"] = UserID
    templatedata["remoteDestinationProfile"]["lines"]["line"][0]["label"] = UserFullName + \
        templatedata["remoteDestinationProfile"]["lines"]["line"][0]["label"]

    templatedata["remoteDestinationProfile"]["lines"]["line"][0]["display"] = UserFullName + \
        templatedata["remoteDestinationProfile"]["lines"]["line"][0]["display"]

    templatedata["remoteDestinationProfile"]["lines"]["line"][0]["displayAscii"] = UserFullName + \
        templatedata["remoteDestinationProfile"]["lines"]["line"][0]["displayAscii"]

    templatedata["remoteDestinationProfile"]["lines"]["line"][0]["dirn"]["pattern"] = Extension
    templatedata["remoteDestinationProfile"]["lines"]["line"][0]["associatedEndusers"]["enduser"]["userId"] = UserID

    #Configure the Remote Destination
    templatedata["remoteDestination"]["name"] = templatedata["remoteDestination"]["name"] + UserFullName
    templatedata["remoteDestination"]["destination"] = mobileNum
    templatedata["remoteDestination"]["remoteDestinationProfileName"] = templatedata["remoteDestinationProfile"]["name"]
    templatedata["remoteDestination"]["ownerUserId"] = UserID
    templatedata["remoteDestination"]["lineAssociations"]["lineAssociation"]["pattern"] = Extension
    templatedata["remoteDestination"]["lineAssociations"]["lineAssociation"]["routePartitionName"] = \
        templatedata["line"]["routePartitionName"]["_value_1"]

    #Debug Command, Remove in final tool
    #print(json.dumps(templatedata["remoteDestination"], indent=4, separators=(',', ': ')))

    #User ID must have Mobility enabled before SNR can be configured
    response = service.updateUser(userid=UserID,enableMobility="true")

    print("="*75)
    print("Configuring the " + templatedata["remoteDestinationProfile"]["name"] + " Remote Destination Profile.")
    print("="*75)

    response = service.addRemoteDestinationProfile(templatedata["remoteDestinationProfile"])

    print("="*75)
    print("Configuring the " + templatedata["remoteDestination"]["name"] + " Remote Destination.")
    print("="*75)

    #Had to modify the 12.0 Schema to fix this bug
    #https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvj13354
    #https://community.cisco.com/t5/management/minoccurs-settings-for-remotedestinationprofilename-and/td-p/3448674
    #Line 17421 and 17436 in AXLSoap.xsd file refernced in the AXL config at the top of this script.
    response = service.addRemoteDestination(templatedata["remoteDestination"])

#===================CCX Directory Number===================
#Configure the user for CCX if the template says to
if templatedata["configurations"]["CCX"]:

    if templatedata["ccxParameters"]["agentLineUsePrimary"]:
        #Configure the extension we added as the primary line to also function as the Agent Line
        #We will assume that the alerting and display names are all set when the primary line is defined above
        #So we just need to set the IPCC extension on the user account and assign the phone to the RMCM Account

        #Send it to UCM to associate the phones and set the Primary extension with the user ID
        response = service.updateUser(userid=UserID,ipccExtension=templatedata["line"]["pattern"],\
            ipccRoutePartition=templatedata["line"]["routePartitionName"]["_value_1"])

    else:
        templatedata["ccxline"]["pattern"] = ccxExtension
        templatedata["ccxline"]["description"] = UserFullName + templatedata["ccxline"]["description"]
        templatedata["ccxline"]["alertingName"] = UserFullName + templatedata["ccxline"]["alertingName"]
        templatedata["ccxline"]["asciiAlertingName"] = UserFullName + templatedata["ccxline"]["asciiAlertingName"]
    
        #Check UCM to see if Extension Exists already
        response = service.listLine(searchCriteria={'pattern': ccxExtension}, returnedTags={'pattern': ''})
        
        #If it doesn't exist, add it, otherwise update it.
        if not response['return']:
            print("="*75)
            print("The Directory Number " +  templatedata["ccxline"]["pattern"] + " does not exist, we will add it")
            print("="*75)
            response = service.addLine(line=templatedata["ccxline"])
    
        else:
            print("="*75)
            print("The Directory Number " +  templatedata["ccxline"]["pattern"] + " exists, we will be updating it")
            print("="*75)
    
            #Remove Dictionary Key used to add a line, but is not used in the Update Method
            templatedata["line"].pop("usage")
    
            #For some reason, the dictionary needs to use the ** to pass
            # the elements to the AXL Update Method.  Referencing pattern=templatedata["line"]
            # generates a type error.  Other AXL Methods seem to work (list and add methods)
            response = service.updateLine(**templatedata["ccxline"]) 
        
        #Create a dictionary for the IPCC Line Appearence that we are going to configure
        templatedata["ccxParameters"]["lineLabelTxt"] = templatedata["ccxParameters"]["lineLabelTxt"] + ccxExtension
        templatedata["ccxParameters"]["lineDisplayName"] = UserFullName + templatedata["ccxParameters"]["lineDisplayName"]

        #Note: Maxcalls 2, busytrigger 1 is a CCX Requirement for an IPCC extension.
        ipccLine = {
                    "label": templatedata["ccxParameters"]["lineLabelTxt"],
                    "display": templatedatatemplatedata["ccxParameters"]["lineDisplayName"],
                    "dirn": {
                        "pattern": ccxExtension,
                        "routePartitionName": {
                            "_value_1": templatedata["ccxline"]["routePartitionName"]["_value_1"]
                        }
                    },
                    "displayAscii": templatedatatemplatedata["ccxParameters"]["lineDisplayName"],
                    "e164Mask": templatedata["ccxParameters"]["e164Mask"],
                    "maxNumCalls": 2,
                    "busyTrigger": 1
        }

        #Adding a line to a device wipes out existing lines so we need to get the current phone settings
        #and apply the new IPCC line to the phone as line 2
        #https://community.cisco.com/t5/management/axl-update-device-profile-line-appearance/m-p/4062936#M3374
        
        #A CCX Agent Line can only be assigned to one device, it cannot be a shared line appearence
        #So we will need to add it to the device type defined in the Template
        ccxDeviceType = str(templatedata["ccxParameters"]["ipccDevType"]).upper

        if templatedata["configurations"]["deviceProfile"] and ccxDeviceType == "EMP":
            #Collect the Device Profile Information
            ipccDevice = service.getDeviceProfile(name=templatedata["deviceProfile"]["name"])
            
            #Add the IPCC Line Appearence to the dictionary returned by the AXL call
            ipccDevice["return"]["deviceProfile"]["lines"]["line"].append

            #Update the Line appearence
            response = service.updateDeviceProfile(deviceProfile=ipccDevice["deviceProfile"])
        
        elif ccxDeviceType == "CSF":
            #Collect the Device Profile Information
            csfProfileName = ccxDeviceType + UserID.upper()
            ipccDevice = service.getPhone(name=csfProfileName)

            #Add the IPCC Line Appearence to the dictionary returned by the AXL call
            ipccDevice["return"]["phone"]["lines"]["line"].append

            #For some reason, the dictionary needs to use the ** to pass
            # the elements to the AXL Update Method.  Referencing phone=template["phone"]
            # generates a type error.  Other AXL Methods seem to work (list and add methods)
            response = service.updatePhone(**ipccDevice["return"]["phone"])

        else:
            #Collect the Device Profile Information
            ipccDevice = service.getPhone(name=newUserPhone)

            #Add the IPCC Line Appearence to the dictionary returned by the AXL call
            ipccDevice["return"]["phone"]["lines"]["line"].append

            #For some reason, the dictionary needs to use the ** to pass
            # the elements to the AXL Update Method.  Referencing phone=template["phone"]
            # generates a type error.  Other AXL Methods seem to work (list and add methods)
            response = service.updatePhone(**ipccDevice["return"]["phone"])

