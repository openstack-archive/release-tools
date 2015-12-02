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

import os.path

import launchpadlib.launchpad


def add_cli_arguments(parser):
    """Add command line arguments for launchpad to the argument parser

    Given an argparse.ArgumentParser instance, add options
    to let the user control how they interact with launchpad.
    """
    lp_grp = parser.add_argument_group('launchpad')
    lp_grp.add_argument(
        "--test",
        action='store_const',
        dest='lp_service_root',
        const='staging',
        default='production',
        help='Use LP staging server to test',
    )
    lp_grp.add_argument(
        '--credentials-file', '-c',
        dest='lp_creds_file',
        default=os.environ.get('LP_CREDS_FILE'),
        help=('plain-text credentials file, '
              'defaults to value of $LP_CREDS_FILE'),
    )


def login(parsed_args):
    """Return a live launchpad connection

    Given the results of parsing command line arguments,
    open a connection to launchpad using the values
    specified by the user and return the handle.
    """
    return launchpadlib.launchpad.Launchpad.login_with(
        application_name='openstack-releasing',
        service_root=parsed_args.lp_service_root,
        credentials_file=parsed_args.lp_creds_file,
    )
