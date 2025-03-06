# CICD Documentation 
## Test deploy
**JenkinsFile:** Jenkinsfile.test_deploy
- **Checkout stage:** Clones gpt-api repo by ssh to windows machine agent (Credentials: `env.SSH_BITBUCKET_CRED`)
- **Deploy verifications:** Checks that pipeline is being executed for branch meant to be deployed in test environment (`env.TEST_BRANCH`)
- **Update ssm documents** Updates all documents in `ssm-documents` content in AWS.
- **Deploy** Sends deploy document to ec2 testing instance (`env.EC2_ID`)
- **Validate deploy** Test endpoints `env.TEST_API` that works with no issues
- **Mark as blue deploy** Only executed if no issues are present, this creates a new blue branch for rolling back in the future
- **Rollback** Executed if there are issues present in deployment, this goes to blue branch and deploys that version. 

**Changes to this pipeline** should require pointing to sandbox instance or any other copy instance for testing the pipeline and not having the actual ec2 testing instance not running correctly

## Sandbox deploy
**JenkinsFile:** Jenkinsfile.test_deploy
- **Checkout stage:** Clones gpt-api repo by ssh to windows machine agent (Credentials: `env.SSH_BITBUCKET_CRED`)
- **Initial setup:** Configures aws credentials 
- **Starts sandbox ec2:** Start environment 
- **Update ssm documents** Updates sandbox document in `ssm-documents` content in AWS.
- **Deploy** Sends deploy document to ec2 testing instance (`env.EC2_ID`)
- **Wait for manual testing** Jenkins inputs that will for person who triggered pipeline to indicate that the manual testing is done so instance can be stopped automatically (If no response is indicated after two hours, then ec2 will be stopped automatically ) 

## Requirements of EC2 Testing
- **SSM:** Connection with Test EC2 instance is done through aws ssm due to proxy, EC2 must have **EC2 SSM role attached** and **ssm agent installed** https://docs.aws.amazon.com/systems-manager/latest/userguide/agent-install-ubuntu-64-snap.html (You must be able to connect to ec2 through ssm in dashboard before it works in pipeline)
- **AWS CLI:** https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

# Jenkins controller
https://rb-jmaas.de.bosch.com/BGSWMX_JMAAS/job/GPT-API/

## Agent maintenance 
### Tokens updates
#### Jenkins controllers tokens
Management link: https://rb-jmaas.de.bosch.com/BGSWMX_JMAAS/manage/credentials/

- PROXY_CRED - bosch_user_proxy - Bosch Password for GIM1GA user for proxy - Can be any bosch user 
- SSH_BITBUCKET_CRED - SSH Credential set up in agent for accessing social coding repository
- gim1ga_bitbucket_admin_bosch - HTTPS social coding repository token
#### AWS Systems manager parameter store
Management link: 
https://us-east-2.console.aws.amazon.com/systems-manager/parameters/?region=us-east-2&tab=Table

- /gpt-api/social-coding-gim1ga-token - HTTP Token for social coding for gim1ga user

### Agent information 
Jenkins agent label: **Windows_GA2VM00012**

Agent type: **Windows Bosch Machine within BCN**

Agent: **ga2vm00012.us.bosch.com**

Windows agent user: **rbadmin_app1**

### Agent requirements

- **AWS CLI** installed and configured
- **PX Proxy** installed and configured

### PX Configuration
Download px .exe for windows: https://github.com/genotrance/px/releases

Use powershell to run following commands 

```
px --username=<username> --password
```

Create px.ini

Example of px.ini file:
```
[proxy]
server = rb-proxy-na.bosch.com:8080
pac = 
pac_encoding = utf-8
port = 3129
listen = 
gateway = 0
hostonly = 1
allow = 
useragent = 
username = gim1ga
auth = 
noproxy = 127.0.0.*,10.*.*.*,192.168.*.*

[client]

[settings]
workers = 2
threads = 8
idle = 30
socktimeout = 20.0
proxyreload = 60
foreground = 0
log = 0
```

px should be configured as a service 