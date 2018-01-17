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
import sys

from storyboardclient._apiclient.exceptions import BadRequest
from storyboardclient.v1 import client

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


def _tag_story(sb, story_id, tag):
    try:
        sb.stories.get(story_id).tags_manager.update(tag)
    except BadRequest:
        # Story alread had a tag, ignoring
        pass


def main():
    args = _parse_args()

    sb = client.Client("https://storyboard.openstack.org/api/v1", args.token)

    stories = [line.strip()[len(STORY_PREFIX):]
               for line in sys.stdin.readlines()
               if line.startswith(STORY_PREFIX)]
    for story in stories:
        _tag_story(sb, story, args.tag)


if __name__ == '__main__':
    main()
