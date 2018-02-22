Lambda function for Route53 cleanup
===================================

This Lambda will get the list of all HostedZones per account, iterate over them and clean up stale Route53 entries.
The stale state is defined by: 
- correlating IP addresses (private and public) of running EC2 instances with A entries in Route53
- correlating public and private DNS of EC2 intances with CNAME entries in Route53

Main part is forked from [fsalum/scripts](https://github.com/fsalum/scripts), reworked a bit.

*TODO*: move to boto3 or better Golang.
