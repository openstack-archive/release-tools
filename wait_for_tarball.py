#!/usr/bin/python
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
import requests
import time


def get_from_jenkins(task, tree=None):
    server = "jenkins.openstack.org"
    url = "https://%s/%s/api/json" % (server, task)
    if tree:
        url += "?tree=%s" % tree
    r = requests.get(url)
    if r.status_code != 200:
        raise IOError("Return code %d from %s" % (r.status_code, url))
    return r.json()


def find_job(project, sha=None, tag=None, retries=8, wait=5):
    retry = 0
    if tag:
        jobname = "job/%s-tarball" % project
    else:
        jobname = "job/%s-branch-tarball" % project

    while retry < retries:
        builds_json = get_from_jenkins(jobname, tree="builds[number]")
        for build in builds_json['builds']:
            job = "%s/%s" % (jobname, build['number'])
            job_json = get_from_jenkins(job,
                                        tree="actions[parameters[name,value]]")
            params = {}
            for param in job_json['actions'][0]['parameters']:
                params[param['name']] = param['value']
            if ((sha and params['GERRIT_REFNAME'] == "milestone-proposed" and
               params['GERRIT_NEWREV'] == sha) or
               (tag and params['GERRIT_REFNAME'] == "refs/tags/%s" % tag)):
                    return job
        retry += 1
        time.sleep(wait)
    else:
        raise IOError("timeout")


def wait_for_completion(job, retries=8, wait=10):
    retry = 0
    while retry < retries:
        job_json = get_from_jenkins(job)
        if not job_json['building']:
            return job_json['artifacts'][0]['displayPath']
        retry += 1
        time.sleep(wait)
    else:
        raise IOError("timeout")


# Argument parsing
parser = argparse.ArgumentParser(description='Wait for a tarball to be built '
                                             'on Jenkins.')
parser.add_argument('project', help='Project to look tarballs for')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--mpsha', help='Wait for a milestone-proposed tarball '
                                   'with given SHA')
group.add_argument('--tag', help='Wait for a tarball for given tag')
args = parser.parse_args()

print "Looking for matching job..."
job = find_job(args.project, sha=args.mpsha, tag=args.tag)
print "Found at %s" % job
print "Waiting for job completion..."
tarball = wait_for_completion(job)
print "Tarball generated at %s" % tarball
