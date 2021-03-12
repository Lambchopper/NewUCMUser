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
json		Used for retrieving and utilizing stored templates (Zeep formats the Soap data in to a JSON 
			compatible format)
dotenv		This can be used to automate the UCM authentication.  It requires a text file that hard codes
			the UCM UID and PWD.  For security purposes this should only be used in testing. This script
			will prompt for user IDs and PWDs in its final form, but the presence of this module is there
			to speed debugging.  More information and exammples can be found here:
			https://github.com/CiscoDevNet/axl-python-zeep-samples

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
		Enables Mobility on the User account and creates the Remote Destination and Remote Destination Profile
	"speeddials": [true|false]
		The script only adds Speed dials to the Phone or the EM Profile.
		
		If the EM Profile is enabled this is where the speed dial will be setup, otherwise the will
		be configured on the phone
		
		The index value for each indicates the order it will appear on the phone in top down fashion, where
		1 is the top most speed dial.
	
	"secondLine": [true|false]
		This will be used to add an additional, non CCX line appearance to the phone, EM Profile and/or Jabber
		
	"CCX": [true|false]
		Configures the new user for CCX.  You must configure the ccxLine section of the template if your 
		environment uses a seperate Agent Extension.  This will be configured as the Second line appearence
		on the phone or Jabber Multiline Profile.
		
		You must also configure the ccxParameters Section:
			"agentLineUsePrimary":
				false = Will add the CCX line as a second Agent Line on the phone.
				true = Use if your design calls for the agent's Primary Line to be set as the CCX Agent Line.  
					If True the Alerting and Display Names will be configured by the line appearence settings
					under the Phone configuration section of the template.
			"jtapiRMCMUser":
				The value should be the UCM application user used by CCX for Resource Management.
				In CCX Navigate to Unified CCX Administration > System > Cisco Unified CM Configuration and 
				use the User ID in the RmCm Subsystem section.
			"e164Mask":
				The External Phone Number Mask for the CCX Agent Line Appearence
			"lineLabelTxt":
				The Prefix to add to the Line Label Text, this will use the extension as the suffix
			"lineDisplayName":
				See Below for Line appearence fields
			"ipccDevType":
				The Agent Line cannot be a Shared Line, this is a restriction for CCX. This field is used
				to set which device will get  the agent line.  For users with a need for mobility, this
				is typically defined on the Extension Mobility Profile so they can log in anyware.
	
				The Phone template defined in the template for the device you are adding a second line to
				must have two lines.  If it doesn't manually changing the Button template on the phone will
				add the new line.
				
				This parameter is only used if the agentLineUsePrimary is set to False.
				
					Set the values exactly as follows:
						SEP = This will assign the CCX Agent Line to the Physical Phone
						EMP = This will assign the CCX Agent Line to the Extension Mobility Device Profile
							if EM is enabled in the Template.
						CSF = This will assign the CCX Agent Line to the Jabber for Windows CSF Profile.
							this requires that the cluster supports Jabber Multiline.  Refer to Cisco
							documentation on Jabber Multiline Support.
			
			"lineAppearanceNum":
				This parameter takes a number value and is used when only used if the agentLineUsePrimary 
				is set to False.  This parameter defines which button the CCX Agent line should be on.
				
				Setting this to two, will set the line on button 2, setting it to 3 places it on button 3.
				
				Since the primary line will be another number, setting this to 1, will be ignored and the
				line will appear on button 2.
				
				Please be sure that the Phone template defined in the template for the device you are adding
				a second line to must have enough lines to support the number of extensions being configured.
				

Configuration Item Names (E.G. Device Profiles, Mobility Profiles) will add the template contents as
as a prefix with the user's full name:
For Example if the Template is configured like this:
    "deviceProfile": {
        "name": "EM-",

The for the user John Dough, the result will be a Device Profile with the name:
	EM-John Dough

For Line Appearence Fields like ASCII Text, Line Lable Alerting Name and Display name, the template will
add a suffix.  These fields can be left at "" to just have these fields result in the full user name.
For Example:
    	"lines": {
            "line": [
			    {
                    "index": 1,
                    "label": " Agent Line",
                    "display": " Agent Line",
					
Results in:
	"John Dough Agent Line"