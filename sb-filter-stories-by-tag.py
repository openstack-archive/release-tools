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
This StoryBoard tool is used to filter out stories by tag.
"""

import argparse
import sys

from storyboardclient.v1 import client

STORY_PREFIX = "storyboard:"


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Filter out stories with specified tag.')
    parser.add_argument(
        '--bugs-only', '-b',
        action='store_true',
        default=False,
        help='List only stories marked as bugs')
    parser.add_argument(
        'tag', nargs='?',
        help='Tag to filter')
    return parser.parse_args()


def _filter_stories(sb, bugs_only, tag, story_ids):
    for story_id in story_ids:
        story = sb.stories.get(story_id)
        if bugs_only and not story.is_bug:
            next
        if tag not in story.tags:
                yield STORY_PREFIX + story_id


def main():
    args = _parse_args()

    sb = client.Client("https://storyboard.openstack.org/api/v1")

    stories = [line.strip()[len(STORY_PREFIX):]
               for line in sys.stdin.readlines()
               if line.startswith(STORY_PREFIX)]
    for story in _filter_stories(sb, args.bugs_only, args.tag, stories):
        print(story)


if __name__ == '__main__':
    main()
