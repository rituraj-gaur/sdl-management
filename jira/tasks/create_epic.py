# Create SDL tasks for product A
import sys
import base64
import traceback
import requests
import json
import io
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define JIRA connection attributes
jira = #YOUR_JIRA_URL
conn_uri = '/rest/api/2/field'
issue_uri = "/rest/api/2/issue"
conn_url = jira + conn_uri
issue_url = jira + issue_uri

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
print('Getting the custom field ID....')
custom_fields = ['Epic Link', 'Customer Impact', 'Where Found', 'Found in Version', 'Likelihood', 'Product Impact', 'Fix Version/s']
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
fix_ver = resp['Fix Version/s']

# Get the 'found in version' field ID
proj_key = "OBSDEF"
ver_uri = '/rest/api/2/project/' + proj_key + '/version?maxResults=250&startAt=0'
ver_url = jira + ver_uri
r = requests.get(ver_url, headers=headers, verify=False)
if r.status_code == 200:
    in_ver = input('ObjectScale version : ')
    resp = r.json()
    fix_ver_id = 0
    for i in resp['values']:
        name_val = i['name']
        if name_val == in_ver:
            fix_ver_id = (i['id'])
            break


# Check if version exists in JIRA
if fix_ver_id == 0:
    print('Error: ', in_ver, 'is not a Valid version in your JIRA instance!')
    sys.exit(1)

# Parse the CSV file
with io.open("sdl_task.csv", "r", encoding="utf-8")as f1:
    data = f1.read()
    f1.close()
data = data.split("<EOL>")

# User EPIC input for creating issues
epic_key = input("Enter the EPIC KEY where these issues are to be created : ")
#where_found = input("Where Found value : ")
# Create JSON from CSV
for rows in data:
    #print(rows.split(",")[1]),
    payload = json.dumps(
        {
            "fields": {
                "project":
                    {
                        "key": proj_key
                    },
                "labels": [
                    "sdl-activity",
                    "security"
                ],
                "summary": rows.split(",")[0],
                "description": rows.split(",")[1],
                "issuetype": {
                    "name": "Story"   #These tasks will be added as jira story
                },
                "priority": {
                    "name": "P2"
                },
                epic: epic_key,
                fix_ver: [{'id': fix_ver_id}]
            }
        }
    )
    print(payload)
    response = requests.post(issue_url, headers=headers, data=payload, verify=False)
    print(response.text)
