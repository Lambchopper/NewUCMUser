Cisco UC New User Automation

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