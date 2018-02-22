Lambda function for Route53 cleanup
===================================
Main logic is forked from [fsalum/scripts](https://github.com/fsalum/scripts), reworked a bit.

This Lambda will get the list of all HostedZones per account, iterate over them and clean up stale Route53 entries.
The stale state is defined by: 
- correlating IP addresses (private and public) of running EC2 instances with A entries in Route53
- correlating public and private DNS of EC2 intances with CNAME entries in Route53

# USAGE (as Lambda):

1. Clone the repo
2. Initialize Virtualenv (highly advised)
```
virtualenv .
```
3. Install requirements
```
pip install -r requirements.txt
```
4. Put dependencies into deployment ZIP
```
cd ./lib/python2.7/site-packages
zip -ur10 ~/<path_to_zip>/<name.zip> *
```
5. Put main.py into deployment ZIP
```
zip -u ~/<path_to_zip>/<name.zip> main.py
```
6. Register Lambda function:
```
aws lambda create-function \
--region <aws_region> \
--function-name <lambda_function_name> \
--zip-file fileb://<path_to_zip>/<name.zip> \
--role arn:aws:iam:<role_name> \
--handler main.lambda_handler \
--runtime python2.7 \
--timeout 60 \
--memory-size 128 \
--profile <profile-name>
```
7. Additionally, I'd advise setting up CloudWatch event, that will trigger Lambda on schedule.

*TODO*: move to boto3 or better Golang.
