## Deploy Instructions
### 1. Set up AWS account
Go to https://aws.amazon.com and register a new AWS account. You will have a unique account ID. You should by default be a "root" user. \
It'd ask your for credit card. Don't worry. All AWS resources we use have free tier which should be good for basic use.

### 2. Setup necessary AWS resources
Set up AWS resources in this order:
#### IAM Identity Center: manage SSO and run/test Lambda from your local machine
- After enabled, you should see "AWS access portal URL" in the form of `https://d-{some_id}.awsapps.com/start`. This will be used as `sso_start_url` below.
- Add a new IAM user with your email. Name it with `nt-tool`. This will be used as `profile` below. Give this user `AdministratorAccess` permission.
#### Elastic Container Registry: store the docker image used by Lambda
- Add a new repository named `nt-tool-cron`. You will find the URI of this image.
#### Lambda: a serverless way to run your code on-demand
- Add a new function named `nt-tool-cron`.
- Use container image and fill in the URI above.
- Go to "Configuration" and set timeout to 15min.
- You'd need to create an IAM role for it to access DynamoDB and SES. To keep things simple, just give it `AmazonDynamoDBFullAccess` and `AmazonSESFullAccess`
#### EventBridge: schedule Lambda to be run periodically
- Add a new schedule named `nt-tool-cron`, and set target to Lambda `nt-tool-cron`.
- You'd need to create an IAM role for this new schedule to allow it to access our Lambda function.
- You can set it to run at a fixed rate of every 15 minutes.
#### DynamoDB: a database which saves routes and dates you want to search
- Add a new table named `flight_queries`.
#### Simple Email Service: send email for alerts
- Add a new identity with your email and verify it. Our cron job automatically uses the first verified email as sender.

### 3. Install local tools
- Install [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- Install [docker engine](https://docs.docker.com/engine/install/)

### 4. Setup AWS SSO via CLI
Setting up AWS SSO allows you to access AWS resources from local machine. \
Use any text editor and create a new file at `~/.aws/config`. Paste the following information.
```
[profile nt-tool]
sso_start_url = https://d-{some_id}.awsapps.com/start
sso_region = us-west-2
sso_account_id = {aws_account_id}
sso_role_name = AdministratorAccess
```

### 5. Add routes to search
Go to `cron/run_local.py` and follow the instructions in the code. \
You can use this command to run it
```
PYTHONPATH=cron:src python cron/run_local.py
```

### 6. Deploy docker to ECR
Login SSO via AWS CLI.
```
aws sso login --profile nt-tool
```
Login docker to ECR.
```
aws ecr get-login-password --region us-west-2 --profile nt-tool | docker login --username AWS --password-stdin {aws_account_id}.dkr.ecr.us-west-2.amazonaws.com
```
Build docker locally.
```
docker build . -t nt-tool-cron -f cron/Dockerfile
```
Tag the newly built docker image as "latest".
```
docker tag nt-tool-cron:latest {aws_account_id}.dkr.ecr.us-west-2.amazonaws.com/nt-tool-cron:latest
```
Push the newly built docker image to ECR.
```
docker push {aws_account_id}.dkr.ecr.us-west-2.amazonaws.com/nt-tool-cron:latest
```
Then optionally, you can remove the old docker image on ECR to avoid being charged.

### 7. Deploy new image and run Lambda
Go to your Lambda function and click "Deploy new image". The next run will use the new docker image.