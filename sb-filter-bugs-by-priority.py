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
This StoryBoard tool is used to filter out bugs of specified priority.
"""

import argparse
import requests
import sys

SB_URL = "https://storyboard.openstack.org/api/v1/"
STORY_PREFIX = "storyboard:"
VALID_PRIORITIES = ('low', 'medium', 'high')


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Filter out bugs of specified priority.')
    parser.add_argument(
        'project', help='Project name')
    parser.add_argument(
        '--priority',
        nargs='?', choices=VALID_PRIORITIES,
        help='Bug priority to filter (default: none)')
    return parser.parse_args()


def _get_project_id(project_name):
    r = requests.get(SB_URL + "projects",
                     {"name": project_name})
    for project in r.json():
        if (project_name == project["name"].split("/")[1]):
            return project["id"]
    print("%s: no matching project" % project_name)
    sys.exit(1)


def _filter_stories(project_id, priority, story_ids):
    result = []
    for story_id in story_ids:
        # Check if story is a bug
        r = requests.get(SB_URL + "stories/%s"
                         % story_id)
        if not r.json()["is_bug"]:
            next
        # Check priority and project id on tasks
        r = requests.get(SB_URL + "stories/%s/tasks"
                         % story_id)
        for task in r.json():
            if (task["project_id"] == project_id and
               task["priority"] != priority):
                result.append(STORY_PREFIX + story_id)
                break
    return result


def main():
    args = _parse_args()

    project_id = _get_project_id(args.project)
    stories = [line.strip()[len(STORY_PREFIX):]
               for line in sys.stdin.readlines()
               if line.startswith(STORY_PREFIX)]
    for story in _filter_stories(project_id, args.priority, stories):
        print(story)


if __name__ == '__main__':
    main()
