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
This StoryBoard tool is used to filter out stories of specified priority.
"""

import argparse
import sys

from storyboardclient.v1 import client

STORY_PREFIX = "storyboard:"
VALID_PRIORITIES = ('low', 'medium', 'high')


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Filter out stories of specified priority.')
    parser.add_argument(
        'project', help='Project name')
    parser.add_argument(
        '--bugs-only', '-b',
        action='store_true',
        default=False,
        help='List only stories marked as bugs')
    parser.add_argument(
        '--priority',
        nargs='?', choices=VALID_PRIORITIES,
        help='Story priority to filter (default: none)')
    return parser.parse_args()


def _get_project_id(sb, project_name):
    projects = sb.projects.get_all(name=project_name)
    for project in projects:
        if (project_name == project.name.split("/")[1]):
            return project.id
    raise ValueError("%s: no matching project" % project_name)


def _filter_stories(sb, project_id, bugs_only, priority, story_ids):
    for story_id in story_ids:
        # Check if story is a bug
        story = sb.stories.get(story_id)
        if bugs_only and not story.is_bug:
            next
        # Check priority and project id on tasks
        for task in story.tasks.get_all():
            if task.project_id == project_id and task.priority != priority:
                yield STORY_PREFIX + story_id
                break


def main():
    args = _parse_args()

    sb = client.Client("https://storyboard.openstack.org/api/v1")

    project_id = _get_project_id(sb, args.project)
    stories = [line.strip()[len(STORY_PREFIX):]
               for line in sys.stdin.readlines()
               if line.startswith(STORY_PREFIX)]
    for story in _filter_stories(sb, project_id, args.bugs_only,
                                 args.priority, stories):
        print(story)


if __name__ == '__main__':
    main()
