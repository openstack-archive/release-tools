#!/usr/bin/env python
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

"""
This StoryBoard tool is used to tag stories.
"""

import argparse
import requests
import sys

STORY_PREFIX = "storyboard:"


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Tag stories with a tag.')
    parser.add_argument(
        '--token', required=True,
        help='Authentication token, available from ' +
        'https://storyboard.openstack.org/#!/profile/tokens')
    parser.add_argument(
        'tag', help='Tag to use')
    return parser.parse_args()


def _tag_story(token, story_id, tag):
    data = {"tags": tag}
    headers = {"Authorization": "Bearer " + token}
    r = requests.put("https://storyboard.openstack.org/api/v1/tags/%s" %
                     story_id, data=data, headers=headers)
    if r.status_code == requests.codes.unauthorized:
        print("Authorization failure, incorrect token?")


def main():
    args = _parse_args()
    stories = [line.strip()[len(STORY_PREFIX):]
               for line in sys.stdin.readlines()
               if line.startswith(STORY_PREFIX)]
    for story in stories:
        _tag_story(args.token, story, args.tag)


if __name__ == '__main__':
    main()
