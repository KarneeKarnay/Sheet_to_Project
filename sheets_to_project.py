"""Module providingFunction printing python version."""

import json
import sys
import time
import getopt
import pygsheets
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def create_gh_proj_issues(project_id, repo_id, field_ids, client, title, type, id, priority, body=" "):
    
    print('------')
    print(title)
    print(body)
    print(type)
    print(id)
    print(priority)
    print('------')   
    
    # Create the Issue in the set repo
    create_issue_mutation = gql(
    """
    mutation MyMutation($body: String!, $repositoryId: ID!, $title: String!) {
        createIssue(input: {repositoryId: $repositoryId, title: $title, body: $body}) {
            clientMutationId
            issue {
                id
                title
                number
            }
        }
    }
    """
    )
    
    response = False
    while response is False:
        print("trying...")
        try:
            cim_response = client.execute(create_issue_mutation, variable_values={
                "repositoryId": repo_id,
                "title": title,
                "body": body
                }
            )
            response = True
        except Exception as ex:
            print(ex)
            print("Waiting a min for Git Content Creation Limit to reset")
            time.sleep(60)

    
    # Capture the created issue's id
    issue_id = cim_response["createIssue"]["issue"]["id"]
    # Get the issue number. This is needed for tasklists as they use the number as ref to the issue
    issue_number = cim_response["createIssue"]["issue"]["number"]
    
    # Assign issue to Project
    assign_issue_to_project_mutation = gql(
    """
    mutation ($projectId: ID!, $contentId: ID!){
        addProjectV2ItemById(input:{projectId:$projectId, contentId:$contentId}) {
            clientMutationId
            item {
            id
            }
        }
    }
    """
    )
    
    aitm_response = client.execute(assign_issue_to_project_mutation, variable_values={
        "projectId": project_id,
        "contentId": issue_id,
        }
    )
    
    # Get issue project item id
    item_id = aitm_response["addProjectV2ItemById"]["item"]["id"]

    print(issue_id)
    print(issue_number)
    
    # Update Issue Type Field
    update_custom_gh_proj_field(project_id, client, item_id, field_ids["Type"], type)
    # Update Priority Field
    update_custom_gh_proj_field(project_id, client, item_id, field_ids["Priority"], priority)
    # Update Issue ID Field
    update_custom_gh_proj_field(project_id, client, item_id, field_ids["ID"], id)
    
    return {"id": issue_id, "issue_number": issue_number}

def prep_body(desc=" ", ac=" ", uplinks=" ", downlinks=" "):
    
    uplinks_fmt = ""
    downlinks_fmt = ""
    
    if uplinks != []:
        uplinks_fmt ="- [ ] #" + "\n- [ ] #".join(map(str,uplinks))
    else:
        uplinks_fmt = " "
    
    if downlinks != []:
        downlinks_fmt ="- [ ] #" + "\n- [ ] #".join(map(str,downlinks))
    else:
        downlinks_fmt = " "
    
    return f"Description: {desc}\n\nAcceptance Criteria: {ac}\n\nUplinks:\n{uplinks_fmt}\n\nDownlinks:\n{downlinks_fmt}\n"

def update_custom_gh_proj_field(project_id, client, id, field_id, value):
    update_draft_issue_mutation = gql(
    """
    mutation ($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!){
        updateProjectV2ItemFieldValue(input:{projectId:$projectId, itemId:$itemId, fieldId:$fieldId, value:$value}) {
            clientMutationId
            projectV2Item {
                id
            }
        }
    }
    """
    )
    
    params = {
    "projectId": project_id,
    "itemId": id,
    "fieldId": field_id,
    "value": { "text": value} 
    }
    
    response = client.execute(update_draft_issue_mutation, variable_values=params)
    
    print(response)

def get_reqs( worksheets):
    
    req_list = []
    
    for sheet in worksheets()[:5]:       
        if sheet.title == 'Test Scripts':
            break

        sheet_reqs = list(
            filter(
                lambda i: i['Type'] != '', sheet.get_all_records(empty_value="", numericise_data=False)
            )
        )
        
        for req in sheet_reqs:
            req_list.append(
                {
                    "title": (req['Text'] if req['Text'] != "-" else " "), 
                    "type": (req['Type'] if req['Type'] != "-" else " "), 
                    "id": (req['ID'] if req['ID'] != "-" else " "), 
                    "ac": (req['Acceptance Criteria'] if req['Acceptance Criteria'] != "-" else " "),
                    "dls": (req['Downlinks'] if req['Downlinks'] != "-" else " "),
                    "uls": (req['Uplinks'] if req['Uplinks'] != "-" else " "),
                    "priority": (req['Priority'] if req['Priority'] != "-" else " "), 
                    "origin sheet": sheet.title,
                    "issue_id": "",
                    "issue_number": ""
                }
            )       
            
    return req_list

def sheets_to_project(token, sheet_id, gh_project_id, gh_repo_id, gh_fields):
    gc = pygsheets.authorize()
    openvic2_req_worksheet = gc.open_by_key(sheet_id)

    transport = RequestsHTTPTransport(url="https://api.github.com/graphql", 
                                    headers={'Authorization': 'Bearer ' + token })

    client = Client(transport=transport)
    parsed_req = get_reqs(openvic2_req_worksheet.worksheets)

    # EXAMPLE
    # parsed_req = [{
    # "title":"The user shall be able to open the game application",
    # "type":"User Req",
    # "id":"SS-3",
    # "ac":"The user can see the application is open",
    # "dls":"UI-17, UI-13",
    # "uls":" ",
    # "priority":"M - Must Have",
    # "origin sheet":"System Specification (SS)",
    # "issue_id":" ",
    # "issue_number": 1
    # },
    # {
    # "title":"A UI panel for housing loading screen content that shall be presented when application is opened but before application is loaded",
    # "type":"Functional",
    # "id":"UI-17",
    # "ac":"The UI element for this requirement is present",
    # "dls":" ",
    # "uls":"SS-3",
    # "priority":"M - Must Have",
    # "origin sheet":"User Interface (UI)",
    # "issue_id":" ",
    # "issue_number": 2
    # },
    # {
    # "title":"A UI panel for housing main menu content that shall be presented after the game is fully loaded",
    # "type":"Functional",
    # "id":"UI-13",
    # "ac":"The UI element for this requirement is present",
    # "dls":" ",
    # "uls":"SS-3",
    # "priority":"M - Must Have",
    # "origin sheet":"User Interface (UI)",
    # "issue_id":" ",
    # "issue_number": 3
    # }]

    # Loop through all the gartherd reqs creating them 
    # and adding their created issue id to their req dict
    for req in parsed_req:
        # Recommended by Github to implement a 3s pause between posts. https://github.com/cli/cli/issues/4801#issuecomment-1431590968
        # If this is still hitting issues change this to 24s. 
        time.sleep(3)
        issue_data = create_gh_proj_issues(
            project_id=gh_project_id,
            repo_id=gh_repo_id,
            field_ids=gh_fields,
            client=client,
            title=req['title'], 
            type=req['type'], 
            id=req['id'], 
            priority=req['priority']
        )
        req["issue_id"] = issue_data["id"]
        req["issue_number"] = issue_data["issue_number"]

    # For each issue add the body. 
    # This is done here as while a body of an issue can be created at creation
    # functioning task lists require already existing issues. 
    # You end up in a chicken and the egg scenario and the best case 
    # the task list won't render. 
    for issue in parsed_req:
        set_issue_body_mutation = gql(
        """
        mutation ($body: String!, $id: ID!) {
            updateIssue(input: {body:$body, id: $id}) {
                clientMutationId
                issue {
                    updatedAt
                }
            }
        }
        """
        )
        
        # Handle Uplinks & Downlinks
        uls_list = []
        dls_list = []

        if bool(issue['uls'].strip()):
            if ',' in issue['uls']:
                uplinks_list = issue['uls'].replace(',','').split()
                for uls_issue_id in uplinks_list:
                    for p_req in parsed_req:
                        if p_req["id"] == uls_issue_id:
                            uls_list.append(p_req["issue_number"])   
            else:
                for p_req in parsed_req:
                    if p_req["id"] == issue['uls']:
                        uls_list.append(p_req["issue_number"])  
                        
        if bool(issue['dls'].strip()):
            if ',' in issue['dls']:
                downlinks_list = issue['dls'].replace(',','').split()
                for dls_issue_id in downlinks_list:
                    for p_req in parsed_req:
                        if p_req["id"] == dls_issue_id:
                            dls_list.append(p_req["issue_number"])  
            else:
                for p_req in parsed_req:
                    if p_req["id"] == issue['dls']:
                        dls_list.append(p_req["issue_number"])  
        
        client.connect_sync
        response = client.execute(set_issue_body_mutation, variable_values={
            "body": prep_body(
                ac=issue['ac'],
                uplinks=uls_list,
                downlinks=dls_list
                ),
            "id": issue['issue_id'],
            }
        )
            


if __name__ == "__main__":
    
    argv = sys.argv[1:]
    
    gh_token = None
    gsheet_id = None
    gh_proj_id = None
    gh_fields = None
    gh_repo_id = None
    
    try:
        opts, args = getopt.getopt(argv, "ht:s:p:f:r:",
                                   ["github_token =",
                                   "googlesheet_id =",
                                   "github_project_id ="
                                   "github_project_fields =",
                                   "github_repo_id ="])
    except Exception as ex:
        print(ex)
    
    for opt, arg in opts:
        if opt  == '-h':
            print("""
Usage: sheets_to_project.py args...
-t, --github_token          = <Github Token>
-s, --googlesheet_id        = <Google Sheet ID>
-p, --github_project_id     = <Github Project ID>
-f, --github_project_fields = <List of Github Project Fields>
-r, --github_repo_id        = <Github Repo ID>
                  """)
        if opt in ['-t', '--github_token']:
            gh_token = arg
        if opt in ['-s', '--googlesheet_id']:
            gsheet_id = arg
        if opt in ['-p', '--github_project_id']:
            gh_proj_id = arg
        if opt in ['-f', '--github_project_fields']:
            # Python or vscode is stripping the quotes from strings when passed as arguments.
            # This should cover both vscode debugger and cmdln. 
            try:
                gh_fields = json.loads(arg)
            except Exception as ex:
                if isinstance(ex, json.JSONDecodeError):
                    gh_fields = json.loads(
                        arg.replace("{", "{ \"")
                            .replace("}", "\" }")
                            .replace(":", "\": \"")
                            .replace(",", "\", \"")
                    )
                else:
                    print(ex)
        if opt in ['-r', '--github_repo_id']:
            gh_repo_id = arg
    
    sheets_to_project(gh_token, gsheet_id, gh_proj_id, gh_repo_id, gh_fields)
