#!/usr/bin/env python

from __future__ import print_function

import argparse
import json
import os
import subprocess

# import httplib2
# httplib2.debuglevel = 1
from launchpadlib.launchpad import Launchpad

CLIENT_NAME = 'OpenStack Stable Backport Search'
LP_INSTANCE = 'production'
CACHE_DIR = os.path.expanduser('~/.cache/launchpadlib/')


# NOTE: This *should* be gerrit.Gerrit().bulk_query() from gerritlib
def gerrit_query(project, message):
    # NOTE: Can't use gerritlib as it uses paramiko which doesn't work on MacOS
    cmd = ["ssh", "-p", "29418", "review.openstack.org", "gerrit",
           "query", "--format=JSON"]

    cmd.append("project:%s" % project)
    # FIXME: Better linkage
    cmd.append("message:%s" % message)
    # cmd.append("~status:abandoned")

    (out, err) = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
    lines = out.split('\n')
    reviews = []
    for line in lines:
        # Gerrit includes helpful summary data and at least 1 blank line.
        # Don't process them.
        if (line and 'status' in line):
            review = json.loads(line)
            # Ideally this would be done as part of the query but that doesn't
            # behave as expected, so filter here.
            if review['status'].lower() != 'abandoned':
                reviews.append(review)
    return reviews


def main(args):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    tags = ['%s-backport-potential' % args.branch,
            '-in-stable-%s' % args.branch]
    branch = 'stable/%s' % args.branch
    project = 'openstack/%s' % args.project

    lp = Launchpad.login_anonymously(CLIENT_NAME, LP_INSTANCE, CACHE_DIR)
    bugs = lp.projects[args.project].searchTasks(tags_combinator='All',
                                                 tags=tags,
                                                 status=["Fix Committed",
                                                         "Fix Released"])
    work_needed = []
    backport_available = []
    for bug in bugs:
        branches = set()
        for review in gerrit_query(project, bug.bug.id):
            if review['status'].lower() == 'merged':
                branches.add(review['branch'])
            elif review['branch'] == branch:
                backport_available.append(bug)
        if ('master' in branches and branch not in branches):
            work_needed.append(bug)

    # FIXME: remove backported bugs from work_needed
    work_needed = [x for x in work_needed if x not in backport_available]
    print("Found %d bugs" % len(bugs))
    print("Work needed on %d bugs" % len(work_needed))
    for bug in work_needed:
        print(u"%s %s %s" % (bug.web_link, bug.title, bug.status))
    print("Backports available for %d bugs" % len(backport_available))
    for bug in backport_available:
        print(u"%s %s %s" % (bug.web_link, bug.title, bug.status))


if __name__ == '__main__':
    defaults = {'branch': 'liberty',
                'project': 'nova'}

    parser = argparse.ArgumentParser(description='Fetch bugs from launchpad')
    parser.set_defaults(**defaults)
    # FIXME: Add support for caching LP query result
    # FIXME: Add log helptext
    parser.add_argument('-b', '--branch',
                        help=("Which tag to query LP for.  " +
                              "The default is %s" % defaults['branch']))
    parser.add_argument('-p', '--project',
                        help=("Which project to query LP for.  " +
                              "The default is %s" % defaults['project']))
    args = parser.parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        pass
