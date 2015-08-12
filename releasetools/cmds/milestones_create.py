#!/usr/bin/env python
#
# Idenpotent script to bulk-create milestones on Launchpad
#
# Copyright 2011-2013 Thierry Carrez <thierry@openstack.org>
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
import sys
import yaml

from launchpadlib.launchpad import Launchpad


def abort(code, errmsg):
    print >> sys.stderr, errmsg
    sys.exit(code)


# Argument parsing
parser = argparse.ArgumentParser(description='Create milestones on LP')
parser.add_argument('configfile', help='YAML file describing milestones')
parser.add_argument('--createseries', action='store_true',
                    help="Create series if it's missing")
args = parser.parse_args()

with open(args.configfile) as f:
    config = yaml.load(f)

# Connect to LP
print("Connecting to Launchpad...")
try:
    launchpad = Launchpad.login_with('openstack-releasing', 'production')
except Exception as error:
    abort(2, 'Could not connect to Launchpad: ' + str(error))

# Run through projects and milestones
for projectname in config['projects']:
    print("Project:", projectname)

    # Retrieve project
    try:
        project = launchpad.projects[projectname]
    except KeyError:
        abort(2, '  Could not find project: %s' % projectname)

    # Retrieve series
    series = project.getSeries(name=config['series'])
    if series is None:
        if args.createseries:
            summary = 'This is the "%s" series.' % config['series']
            series = project.newSeries(name=config['series'],
                                       summary=summary)
            series.status = 'Future'
            series.lp_save()
        else:
            abort(2, '  Could not find series %s in project %s' % (
                  config['series'], projectname))

    # Check each milestone in config file
    for m, d in config['milestones'].iteritems():
        mymilestone = series.name + "-" + m
        print("  Milestone: ", mymilestone)

        for milestone in series.all_milestones:
            if milestone.name == mymilestone:
                if str(milestone.date_targeted)[0:10] == d:
                    print("    OK")
                else:
                    print("    Exists but wrong date...",)
                    milestone.date_targeted = d
                    milestone.lp_save()
                    print("fixed")
                break
        else:
            print("    Does not exist yet...",)
            if m.startswith("rc"):
                code_name = m.upper()
            else:
                code_name = series.name[0:1] + m
            series.newMilestone(name=series.name + "-" + m,
                                date_targeted=d or None,
                                code_name=code_name)
            print("created")
