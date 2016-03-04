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
import csv
import sys

from releasetools import governance

MILESTONE = 'release:cycle-with-milestones'
INTERMEDIARY = 'release:cycle-with-intermediary'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--project-list',
        default=governance.PROJECTS_LIST,
        help='a URL pointing to a projects.yaml file, defaults to %(default)s',
    )
    parser.add_argument(
        '--format', '-f',
        choices=['csv', 'etherpad'],
        default='etherpad',
    )
    args = parser.parse_args()

    team_data = governance.get_team_data()
    teams = {
        n: governance.Team(n, i)
        for n, i in team_data.items()
    }

    # Organize deliverables by their release model, whether they are
    # managed, and the team that owns them.
    deliverables_by_model = {
        MILESTONE: {
            'managed': {},
            'unmanaged': {},
        },
        INTERMEDIARY: {
            'managed': {},
            'unmanaged': {},
        },
    }
    for t in teams.values():
        for dn, di in t.deliverables.items():
            for model in deliverables_by_model.keys():
                if model in di.tags:
                    if 'release:managed' in di.tags:
                        managed = 'managed'
                    else:
                        managed = 'unmanaged'
                    dbm_team = deliverables_by_model[model][managed].setdefault(
                        di.team.name, [])
                    dbm_team.append(di)
                    break

    # Dump the dashboard data
    if args.format == 'csv':
        writer = csv.writer(sys.stdout)
        writer.writerow(
            ('Release Model',
             'Managed',
             'Team',
             'PTL Nick',
             'IRC Channel',
             'Deliverable Type',
             'Deliverable Name',
         ))
        for model in [MILESTONE, INTERMEDIARY]:
            for managed in ['managed', 'unmanaged']:
                dbm_teams = sorted(deliverables_by_model[model][managed].items())
                for team_name, team_deliverables in dbm_teams:
                    team = teams[team_name]
                    for d in sorted(team_deliverables, key=lambda d: d.name):
                        writer.writerow(
                            (model,
                             managed,
                             team.name,
                             team.data['ptl']['irc'],
                             team.data.get('irc-channel'),
                             d.type,
                             d.name,
                         ))
    else:
        for model in [MILESTONE, INTERMEDIARY]:
            print('{}\n'.format(model))
            for managed in ['managed', 'unmanaged']:
                print('  * {}\n'.format(managed))
                dbm_teams = sorted(deliverables_by_model[model][managed].items())
                for team_name, team_deliverables in dbm_teams:
                    team = teams[team_name]
                    print('    * {}'.format(team_name))
                    print('      * PTL: {}'.format(team.data['ptl']['irc']))
                    print('      * IRC: {}'.format(team.data.get('irc-channel', '')))
                    print('      * Deliverables')
                    for d in sorted(team_deliverables, key=lambda d: d.name):
                        print('        * {d.name} ({d.type})'.format(d=d))
                    print()
