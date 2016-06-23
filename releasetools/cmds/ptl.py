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
import argparse

from releasetools import governance

_TEMPLATE = '''
Name        : {name}
IRC Nick    : {irc}
IRC Channel : {irc_channel}
Email       : {email}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'team',
        help='the team name',
    )
    args = parser.parse_args()

    team_data = governance.get_team_data()
    # Allow for case-insensitive search
    teams = {
        n.lower(): i
        for n, i in team_data.items()
    }

    try:
        team = teams[args.team.lower()]
    except KeyError:
        print('ERROR: No team {!r}'.format(args.team))
    else:
        ptl = team['ptl']
        print(_TEMPLATE.format(
            name=ptl.get('name'),
            irc=ptl.get('irc'),
            email=ptl.get('email'),
            irc_channel=team.get('irc-channel'),
        ))
