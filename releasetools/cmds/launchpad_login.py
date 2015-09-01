#!/usr/bin/env python
#
# Test the launchpad login without taking any real action.
#
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

from __future__ import print_function
from __future__ import unicode_literals

import sys

from launchpadlib.launchpad import Launchpad


def abort(code, errmsg):
    print(errmsg, file=sys.stderr)
    sys.exit(code)


def main():
    # Connect to LP
    print("connecting to launchpad")
    try:
        Launchpad.login_with('openstack-releasing', 'production')
    except Exception as error:
        abort(2, 'Could not connect to Launchpad: ' + str(error))
