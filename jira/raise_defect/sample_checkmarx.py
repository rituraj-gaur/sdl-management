import sys
import base64
import traceback
import requests
import json
import io
import urllib3

# Suppress insecure connection warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define JIRA connection attributes
jira = #YOUR JIRA URL

print('Connecting to JIRA instance : ' + jira + '\n')
conn_uri = '/rest/api/2/field'
issue_uri = "/rest/api/2/issue"
conn_url = jira + conn_uri
issue_url = jira + issue_uri
issue_log = 'issue_key.txt'
src_csv = 'issue_cx.csv'

# create the authorization header
user_name = input('Your JIRA username : ')
user_pass = input('Your JIRA pass : ')
sample_string = user_name + ':' + user_pass
sample_string_bytes = sample_string.encode("ascii")
base64_bytes = base64.b64encode(sample_string_bytes)
auth_string = base64_bytes.decode("ascii")
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Basic " + auth_string
}

# check JIRA connection
try:
    r = requests.get(conn_url, headers=headers, verify=False)
    # r.raise_for_status()
    status = r.status_code
    if status == 200:
        print('Connection Successful to JIRA...')
    elif status == 401:
        print('Unauthorized, please check the username and password. Aborting....')
        sys.exit(1)
    else:
        print(status + ' returned while connecting.Aborting.....')
        sys.exit(1)
except Exception as err:
    print(err)
    print('Aborting.....')
    sys.exit(1)

# Get the custom field ID
#print('Getting the custom field ID....')
custom_fields = ['Epic Link', 'Customer Impact', 'Where Found', 'Found in Version', 'Likelihood', 'Product Impact']
resp = dict()
try:
    r = requests.get(conn_url, headers=headers, verify=False)
    if r.status_code == 200:
        results = r.json()
        for r in results:
            if r['name'] in custom_fields:
                resp.update({r['name']: r['id']})
    else:
        print("[!] Error getting custom fields")
        sys.exit(1)
except Exception as ex:
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)

# Assign the custom field ID for your JIRA
epic = resp['Epic Link']
likelihood = resp['Likelihood']
prod_impact = resp['Product Impact']
cust_impact = resp['Customer Impact']
found_ver = resp['Found in Version']
found_at = resp['Where Found']
'''
print(epic)
print(likelihood)
print(cust_impact)
print (prod_impact)
print (found_ver)
print(found_at)
'''
# Get the 'found in version' field ID
sev = input("Enter the SEVERITY of issues to created (High/Medium): ")
proj_key = input("Enter the PROJECT KEY: ")
ver_uri = '/rest/api/2/project/' + proj_key + '/version?maxResults=250&startAt=0'
ver_url = jira + ver_uri
r = requests.get(ver_url, headers=headers, verify=False)
if r.status_code == 200:
    in_ver = input('Enter the version in which these issues were found : ')
    resp = r.json()
    found_ver_id = 0
    for i in resp['values']:
        name_val = i['name']
        if name_val == in_ver:
            found_ver_id = (i['id'])
            break

# Check if version exists in JIRA
if found_ver_id == 0:
    print('Error: ', in_ver, 'is not a Valid version in your JIRA instance!')
    sys.exit(1)

# Parse the CSV file
with io.open(src_csv, "r", encoding="utf-8")as f1:
    data = f1.read()
    f1.close()
data = data.split("<EOL>")

# User EPIC input for creating issues
epic_key = input("Enter the EPIC KEY where these issues are to be created : ")
priority = input("Enter the Issue Priority (P1/P2/P3/P4) : ")


# set headers for description
#rec_head = '*Recommendation:* '
cat_head = '*OWASP Category:* '
loc_head = ('*File lines with issue:* ' + '\n' )

# Create JSON from CSV
for rows in data:
    # print(rows.split(",")[1]),
    #desc_1 = (rows.split(",")[3] + '\n')
    desc_2 = (rows.split(",")[3] + '\n')
    desc_3 = (cat_head + rows.split(",")[0] + '\n')
    desc_4 = (loc_head + rows.split(",")[4] + '\n')
    desc_5 = ('*Scanner Tool:* ' + 'Checkmarx' + '\n')
    desc_6 = ('*Finding Link:* ' + rows.split(",")[5] + '\n')
    desc = desc_2 + desc_3 + desc_4 + desc_5 + desc_6
    payload = json.dumps(
        {
            "fields": {
                "project":
                    {
                        "key": proj_key
                    },
                "components": [{
                    "name": rows.split(",")[2],
                }],
                "labels": [
                    "scan",
                    "sdl-activity",
                    "checkmarx",
                    "sec-must-fix",
                    "security"
                ],
                "summary": rows.split(",")[1],
                "description": desc,
                "issuetype": {
                    "name": "Defect"
                },
                "priority": {
                    "name": priority
                },
                epic: epic_key,
                likelihood: {'value': 'Reasonably Probable'},
                prod_impact: {'value': sev},
                cust_impact: {'value': sev},
                found_at: {'value': 'Development'},
                found_ver: {'id': found_ver_id}
            }
        }
    )
    print('---------------------------------SENDING THE BELOW PAYLOAD TO JIRA-----------------------------------------')
    print(payload)
    response = requests.post(issue_url, headers=headers, data=payload, verify=False).json()
    # print(response.text)
    print('RESPONSE FROM JIRA : ')
    print(response)
    try:
        file1 = open(issue_log, "a")
        file1.write(response["key"]+'\n')
        file1.close()
    except Exception as err:
        file1 = open(issue_log, "a")
        file1.write('Error: No Issue Key created. \n')
        file1.close()

    print('--------------------------------------------------------------------------------------------------------\n\n')
