#!/usr/bin/env python
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

"""Watch the zuul status output and report on release-related jobs.
"""

from __future__ import print_function

import argparse
import datetime
import json
import os.path
import time

import requests


INTERESTING_PIPELINES = set([
    'pre-release',
    'release',
    'release',
    'release-post',
    'tag',
])


def report(data):
    print(datetime.datetime.now())
    pipelines = data['pipelines']

    for pipeline in pipelines:
        pname = pipeline['name']
        if pname not in INTERESTING_PIPELINES:
            continue
        print(pname)

        for queue in pipeline['change_queues']:
            print('  {name}'.format(name=queue['name']))
            for head in queue['heads']:
                for h in head:
                    print('    {id}: {project}'.format(**h))
                    for job in h['jobs']:
                        print('      {name}: {result}'.format(**job))
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--source', '-s',
        default='http://zuul.openstack.org/status.json',
        help='The source for the status info.',
    )
    parser.add_argument(
        '--pause', '-p',
        default=5,
        type=int,
        help='The number of seconds to pause between downloads. (%(default)s)',
    )
    args = parser.parse_args()

    if os.path.exists(args.source):
        with open(args.source, 'r') as f:
            data = json.loads(f.read())
        report(data)
    else:
        while True:
            try:
                data = requests.get(args.source).json()
            except Exception as e:
                print(datetime.datetime.now(), e)
            else:
                report(data)
            time.sleep(args.pause)


if __name__ == '__main__':
    main()
