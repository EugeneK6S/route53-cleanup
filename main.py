#!/usr/bin/env python

# title          : route53-cleanup.py
# description    : Searches all Route53 entries and match with EC2 Public/Private IP addresses
#                : and public/private DNS addresses. Return IP DNS records and CNAME DNS records
#                : not found on EC2 instances to be cleaned
#                :
# usage          : route53-cleanup.py --help
# requirements   : Python Boto and credentials set in .boto config file or environment variables
# python_version : 2.6+
#

import sys
import argparse
import re
import boto.ec2
from boto.ec2 import regions
from boto.route53.connection import Route53Connection
from boto.route53.exception import DNSServerError
from boto.route53.record import ResourceRecordSets
from collections import defaultdict
import pprint

description = 'Route53 Cleanup Reporter'
version = '%(prog)s 1.0'
usage = '%(prog)s --zoneid <ZoneID>'


def options():
    parser = argparse.ArgumentParser(usage=usage, description=description)
    # parser.add_argument('-d', '--dry-run', dest='dryrun', action='store')
    parser.add_argument('-d', '--dry', help='Dry run', action='store_true')
    args = parser.parse_args()
    return args

class CommandArgs(object):
    zoneid = ""
    region = ""
    
    def __init__(self, zoneid, region):
        self.zoneid = zoneid
        self.region = region

def get_ec2(args):
    ec2_ips = defaultdict(dict)

    # Connect the region
    for r in regions():
        if r.name == args.region:
            region = r
            break
    else:
        print "Region %s not found." % args.region
        sys.exit(1)

    print "Retrieving EC2 records..."
    conn = boto.connect_ec2(region=region)
    reservations = conn.get_all_reservations()

    for reservation in reservations:
        instances = reservation.instances
        for instance in instances:
            if instance.state == 'running' or instance.state == 'stopped':
                ec2_ips[instance.id]['private_ip'] = instance.private_ip_address
                ec2_ips[instance.id]['public_ip'] = instance.ip_address
                ec2_ips[instance.id]['private_dns'] = instance.private_dns_name
                ec2_ips[instance.id]['public_dns'] = instance.public_dns_name

    return ec2_ips


def get_route53(args):
    route53_ips = {}
    conn = Route53Connection()

    try:
        conn.get_hosted_zone(args.zoneid)
    except DNSServerError:
        print "%s zone not found" % args.zoneid
        sys.exit(1)
    print "Retrieving Route53 records..."
    records = conn.get_all_rrsets(args.zoneid)

    for record in records:
        if record.type == 'A':
            route53_ips[record.name] = record.resource_records[0]
        elif (record.type == 'CNAME' and (record.resource_records[0].endswith('.compute.amazonaws.com') or record.resource_records[0].endswith('.internal'))):
            route53_ips[record.name] = record.resource_records[0]
    return route53_ips


def lambda_handler():
    conn = Route53Connection()
    zones = conn.get_all_hosted_zones()
    for zone in zones['ListHostedZonesResponse']['HostedZones']:
        zone_id = zone['Id'].replace('/hostedzone/', '')
        args = CommandArgs(zone_id, 'eu-central-1')
        option = options()

        print "Working with %s" % zone_id

        route53_ips = get_route53(args)
        ec2_ips = get_ec2(args)
        report_ips = {}
        
        changes = ResourceRecordSets(conn, args.zoneid)
        print 'Following records will be deleted: '
        for name, ip in route53_ips.items():
            match = 0
            for ec2_id in ec2_ips:
                if ip in ec2_ips[ec2_id].values():
                    match = 1
            if match == 0:
                report_ips[name] = ip

        print report_ips.items()
        # print option.dry

        if len(report_ips) != 0:
            for name, ip in sorted(report_ips.items()):
                if re.match('[\d\.]+', ip):
                    print "A;%s;%s" % (ip, name)
                    change = changes.add_change("DELETE", str(name), "A", 60)
                    change.add_value(ip)
                else:
                    print "CNAME;%s;%s" % (ip, name)
            if not option.dry: 
                print 'Deleting records...'
                changes.commit()
        print 'Deleted records: '
        pprint.pprint(changes)

if __name__ == '__main__':
    lambda_handler()