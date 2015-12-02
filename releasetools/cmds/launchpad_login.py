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

import argparse
import sys

from releasetools import launchpadutils


def abort(code, errmsg):
    print(errmsg, file=sys.stderr)
    sys.exit(code)


def main():
    parser = argparse.ArgumentParser(description="login to launchpad")
    launchpadutils.add_cli_arguments(parser)
    args = parser.parse_args()

    # Connect to LP
    print("connecting to launchpad")
    try:
        launchpadutils.login(args)
    except Exception as error:
        abort(2, 'Could not connect to Launchpad: ' + str(error))
