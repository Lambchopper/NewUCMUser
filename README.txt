================================================================================
Cisco UC New User Automation
================================================================================
This tool is being designed so that new hires can be inserted in to Cisco Call Manager in a controlled and 
automated way maintaining naming convension stanadards.  The goal is consistancy of deployment so that new
user accounts are not configured incorrectly requiring immediate troubleshooting.

Additionally, we strive to templatize the deployments so that templates can be built for different types of
users or different sites.  The intent is to make it easy for administrators to create templates for their
needs without needing to know how to program Python.

Ideally, a Help Desk user with suffient priviledges would be able to:
1: Execute the script
2: Be prompted with a list of templates to choose
3: Be prompted for the UserID, the Extension and one or two other peices of information
4: The script will then configure Call Manager based on the template stanadard.

Since we are using the Zeep Python Library to engage with Cisco's AXL API and that library converts the
SOAP objects in to a JSON format, we will be using JSON as our template file storage medium.

This allows us to dump the Zeep results from a simple AXL query for use in building templates and extending
script functionality later as required.

================================================================================
Miscellaneous Notes
================================================================================
---------------
Note 1:
---------------
The GIT Repository does not include the JSON Files or the .env file. this is to protect confidential
configuration data.  The .env file is used to store the UCM server URL and Credentials and will be replaced
with login prompts in the final version.  A sanitized sample JSON file will be added to the last commit
for reference.

Cisco's AXL Git repo has more info on using .env for passing credentials:
https://github.com/CiscoDevNet/axl-python-zeep-samples

---------------
Note 2:
---------------
The dumpucmconfig.py is a rough script used to execute AXL queries for configuration items and dump them
to JSON files for use in building templates.  Modify this script with an object of interest and the
appropriate AXL Get or List Method.

More info on the AXL API can be found here, including the full Schema reference:
https://developer.cisco.com/docs/axl/

---------------
Note 3:
---------------
There is a bug that generates an error when attempting to insert the Remote Destination for an SNR
configuration.
    
I had to modify the 12.0 Schema to fix this bug
https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvj13354
https://community.cisco.com/t5/management/minoccurs-settings-for-remotedestinationprofilename-and/td-p/3448674
Line 17421 and 17436 in AXLSoap.xsd file where modified to set minOccurs="0" the default is 1
The AXLSoap.xsd file to be modified will be the one referenced in the same folder as:
wsdl = os.path.abspath('axlsqltoolkit/schema/current/AXLAPI.wsdl')

This line may need to be changed due to the version of UCM you are using.  The current folder will house
the schema of the UCM version that the API was downloaded from.  The version packaged with this script
came from 12.0 of UCM.  The schema can be downloaded from:
Cisco Unified CM Administration > Applications > Plugins > Cisco AXL Toolkit	
	

================================================================================
Required Modules:
================================================================================
Zeep		Soap Client for AXL interactions
urllib3		Used for the HTTPS interactions with UCM
json		Used for retrieving and utilizing stored templates (Zeep formats the Soap data in to a JSON compatible format)

================================================================================
Template file Configurations:
================================================================================
The Configurations section at tthe top of the template files is used to define which UCM configuration
elements will be configured.  The template contains each configuration as a section.

# Definitions:
"configurations": {
	"deviceProfile": [true|false]
		Use the "deviceProfile" section to configure an Extension Mobility Profile.  This will only
		add a new device profile.
	"loggedOutExtension": [true|false]
		This will trigger the script to use the settings in the loggedOutExtension for the physical
		phone if set to true.  False will set the user's extension passed to the script.  To be used
		in environments where Extension mobility is used and the Physical phone requires a non-routable
		or generic hoteling extension.
	"directoryNumber": [true|false]
		Used for testing to enable/disable directory number changes.  WILL BE CHANGED IN FINAL SCRIPT
		TO USE TO DETERMINE IF USER EXTENSION OR GENERIC EXTENSION IS CONFIGURED ON PYSICAL PHONE FOR
		CASES WHERE THEY ARE DIFFERENT (EG: EXTENSION MOBILITY)
	"phoneSettings": [true|false]
		Use the "phone" section to configure a physical phone.  Configuring a physical phone may not be
		necessary in environments that rely on extension mobility.
	"jabberCSF": [true|false]
		Use the "jabberCSF" section to configure a Jabber Soft Phone Profile.
	"jabberAndroid": [true|false]
		Use the "jabberAndroid" section to configure a Jabber Soft Phone Profile for Android (BOT).
	"jabberiPhone": [true|false]
		Use the "jabberiPhone" section to configure a Jabber Soft Phone Profile for iPhone (TCT).
	"jabberTablet": [true|false]
	"SNR": [true|false]
	"speeddials": [true|false]
	"CCX": [true|false]
	},