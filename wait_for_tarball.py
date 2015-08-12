#!/usr/bin/env python
#
# Script to wait for a tarball to be generated in Jenkins
#
# Copyright 2013 Thierry Carrez <thierry@openstack.org>
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import argparse
import re
import requests
import time


def get_from_jenkins(job_url, tree=None):
    api_job_url = job_url + "api/json"
    if tree:
        api_job_url += "?tree=%s" % tree
    r = requests.get(api_job_url, verify=False)
    if r.status_code != 200:
        raise IOError("Return code %d from %s" % (r.status_code, api_job_url))
    return r.json()


def find_job_url(sha=None, retries=30, wait=30):
    retry = 0
    shaexpr = (r'https://review\.openstack\.org/gitweb\?p=.*\.git;'
               'a=commitdiff;h=(.*)$')

    while retry < retries:
        try:
            statusjson = requests.get('http://zuul.openstack.org/status.json')
        except Exception as e:
            print("Error fetching status: %s" % e)
            print("  waiting before trying again")
            time.sleep(wait)
            continue
        status = statusjson.json()
        for pipeline in status['pipelines']:
            for queue in pipeline['change_queues']:
                for head in queue['heads']:
                    for r in head:
                        for job in r['jobs']:
                            if job['name'].endswith('-tarball'):
                                if job['url'] is not None:
                                    c = re.match(shaexpr, r['url'])
                                    if c and c.group(1).startswith(sha):
                                        return job['url']
        retry += 1
        time.sleep(wait)
    else:
        raise IOError("timeout")


def wait_for_completion(job_url, retries=30, wait=30):
    retry = 0
    while retry < retries:
        job_json = get_from_jenkins(job_url)
        if not job_json['building']:
            return job_json['artifacts'][-1]['displayPath']
        retry += 1
        time.sleep(wait)
    else:
        raise IOError("timeout")


# Argument parsing
parser = argparse.ArgumentParser(description='Wait for a tarball to be built '
                                             'on Jenkins.')
parser.add_argument('sha', help='commit that will generate the tarball')
args = parser.parse_args()

print("Looking for matching job...")
job_url = find_job_url(sha=args.sha)
print("Found at %s" % job_url)
print("Waiting for job completion...")
tarball = wait_for_completion(job_url)
print("Tarball generated at %s" % tarball)
