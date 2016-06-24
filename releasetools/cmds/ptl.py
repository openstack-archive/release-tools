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
import itertools

from releasetools import governance

import mwclient


_TEMPLATE = '''
Name        : {name}
IRC Nick    : {irc}
IRC Channel : {irc_channel}
Email       : {email}
Liaison     : {liaison_name}
              {liaison_irc}
'''


def get_page_section(page_content, section):
    "Return iterable of lines making up a section of a wiki page."
    section_start = u'== {} =='.format(section).lower()
    lines = page_content.splitlines()
    lines = itertools.dropwhile(
        lambda x: x.lower() != section_start,
        lines,
    )
    lines.next()  # skip the section heading
    lines = itertools.takewhile(
        lambda x: not x.startswith('== '),
        lines,
    )
    return lines


def get_wiki_table(page_content, section):
    """Return iterable of dicts making up rows of a wiki table.

    Assumes there is only one table per section.

    """
    lines = get_page_section(page_content, section)
    lines = itertools.dropwhile(
        lambda x: x != '{| class="wikitable"',
        lines,
    )
    headings = []
    for line in lines:
        if line == '|-':
            continue
        elif line.startswith('!'):
            headings = [h.strip() for h in line.lstrip('!').split('!!')]
        elif line.startswith('|'):
            items = [i.strip() for i in line.lstrip('|').split('||')]
            row = {
                h: i
                for (h, i) in itertools.izip(headings, items)
            }
            yield row
        elif line == '}':
            # end of table
            break


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

    # Check for liaison information.
    site = mwclient.Site('wiki.openstack.org')
    page = site.Pages['CrossProjectLiaisons']
    table = get_wiki_table(page.text(), 'Release management')
    liaisons = {
        row['Project'].lower(): row
        for row in table
    }
    team_liaison = liaisons.get(args.team.lower(), {})

    try:
        team = teams[args.team.lower()]
    except KeyError:
        print('No official team {!r}'.format(args.team))
        team = {}

    ptl = team['ptl']
    print(_TEMPLATE.format(
        name=ptl.get('name'),
        irc=ptl.get('irc'),
        email=ptl.get('email'),
        irc_channel=team.get('irc-channel'),
        liaison_name=team_liaison.get('Liaison'),
        liaison_irc=team_liaison.get('IRC Handle'),
    ))
