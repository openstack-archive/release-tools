#!/usr/bin/env python
#
# Add a comment on a number of Launchpad bugs
#
# Copyright 2015 Thierry Carrez <thierry@openstack.org>
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import print_function
import argparse

import launchpadlib.launchpad
import lazr.restfulclient.errors

# Parameters
parser = argparse.ArgumentParser(description="Add comment on bugs")
parser.add_argument('--subject', help='The comment subject',
                    default='Comment added by add_comment')
parser.add_argument('--content', help='The comment content',
                    default='Comment added by add_comment')
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')
parser.add_argument('bugs', type=int, nargs='+', help='Bugs to add comment to')
args = parser.parse_args()

# Connect to Launchpad
print("Connecting to Launchpad...")
launchpad = launchpadlib.launchpad.Launchpad.login_with(
    'openstack-releasing', args.test)

# Add comment
for bugid in args.bugs:
    print("Adding comment to #%d..." % bugid, end='')
    try:
        bug = launchpad.bugs[bugid]
        bug.newMessage(subject=args.subject, content=args.content)
        print (" done.")
    except lazr.restfulclient.errors.ServerError as e:
        print(" TIMEOUT during save !")
    except Exception as e:
        print(" ERROR during save ! (%s)" % e)
