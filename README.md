# OpenVic2 Requirements GoogleSheet to Github Project Issues 
## Introduction
This document details the usage of the sheets_to_project python script. This script is designed to take the requirements as detailed in the OpenVic2 Googlesheets document and covert them into Github Project issues. 

## Script Summary
The script in summary works like this:
1. Parse gSheet for requirements and convert them into a data structure that can be used to create Github Issues. 
2. Create the issues in a Github repository. 
3. Assign the issues to a Github Project and update the Project Custom Fields for each issue. 

## Prerequisites 
The following items will need to be installed prior to running the script:
* Python 3.10.5 or higher. 
* Install required modules. `pip install -r requirements.txt`
* Github Repo
* Github Project
* Github Project Custom Fields of 'Type', 'Priority' & 'ID'

### Google OAuth2.0 Credential
To use the Google API to access gsheets requires an authentication token. The module `pygsheets` currently only supports authentication with the Google API via Service Accounts or OAuth2.0 Tokens. This script is written for OAuth 2.0 Credential in mind and the following steps will need to be follow to create a token of this type:
1. Login to [Google Cloud](https://console.cloud.google.com/welcome?project=alien-range-306609).
2. Create a New Project. 
3. Go to APIs & Services > OAuth concent screen
4. For User Type select External. 
5. Click Create. 
6. Git your app a name, user support email & developer contact email. This information will only be used if you publish the app.
7. Click Save & Continue. 
8. On the Scopes page click Add or Remove Scopes. 
9. Add the following scopes:
   * `/auth/drive.file`
   * `/auth/spreadsheets`
   * `/auth/spreadsheets.readonly`
   * `/auth/drive`
   * `/auth/drive.readonly`
10. At the Test users page click Add Users and enter an email address. 
11. Click Save and create. 
12. Go to APIs & Services > Credentials
13. Click Create Credentials > OAuth client ID. 
14. In the Application type drop down select Desktop App.
15. Give it name and then click Create. In the popup that appears, download the json token file. 
16. Rename the file to `client_secret.json` and place it in the same directory as the script. 
* This credentials will only exist for 7 days. Unless you publish the app you will need to create a new one every 7 days. 

### Github Personal Access Tokens (Classic)
The Github API Supports the usage of Personal Access Token for interaction to both the Classic API & GraphQL API. To create a token that enables this script, follow the instructions below:
1. Login to Github. 
2. Click on your User Profile Icon > Settings
3. Click Developer Settings > Personal access tokens > Tokens (classic). 
4. Click Generate new token. 
5. Name the token and add the following scopes:
   * `public_repo`
   * `project`
6. Note the token secret that is generated. This will only appear **once**!

## How to run the script:
The script needs the following arguments:
```
Usage: sheets_to_project.py args...
-t, --github_token          = <Github Token>
-s, --googlesheet_id        = <Google Sheet ID>
-p, --github_project_id     = <Github Project ID>
-f, --github_project_fields = <List of Github Project Fields>
-r, --github_repo_id        = <Github Repo ID>
```
Note that the `github_project_fields` argument takes a dictionary. That dictionary is expected to have key:values of the following:
```
"Type":"Github Project Custom Field ID",
"Priority":"Github Project Custom Field ID"",
"ID":"Github Project Custom Field ID"
```
To get the information needed for the github specific arguments, there is a [Github GraphQL API Explorer tool](https://docs.github.com/en/graphql/overview/explorer), that can be used to query information from the API, that is not accessible through the UI. 

### List Github Projects by User
```
script='query {
  user(login: \"<USER>\") {
    projectsV2(first: 10) {
      edges {
        node {
          title
          id
        }
      }
    }
  }
}'

script="$(echo $script)"

curl --request POST \
--url https://api.github.com/graphql \
--header 'Authorization: bearer <TOKEN>' \
--data "{ \"query\": \"$script\"}"
```

### List Github Custom Project Fields by Project Name
```
script='query {
user(login: \"<USER>\") {
  projectsV2(first: 1, query:\"<PROJECT_NAME>\") {
    nodes {
      fields(first: 100) {
        edges {
          node {
            ... on ProjectV2Field {
              id
              name
            }
          }
        }
      }
    }
  }
}
}'

script="$(echo $script)"

curl --request POST \
--url https://api.github.com/graphql \
--header 'Authorization: bearer <TOKEN>' \
--data "{ \"query\": \"$script\"}"
```
### List Github Repos Owned by User
```
script='{
  user(login: \"<USER>\") {
    repositories(first: 10) {
      edges {
        node {
          id
          name
        }
      }
    }
  }
}'

script="$(echo $script)"

curl --request POST \
--url https://api.github.com/graphql \
--header 'Authorization: bearer <TOKEN>' \
--data "{ \"query\": \"$script\"}"
```