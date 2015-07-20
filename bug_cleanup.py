#!/usr/bin/env python
#
# Copyright 2015 Markus Zoeller <mzoeller@de.ibm.com>
# All Rights Reserved.
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


# +-----+ 1         1..* +----------+
# | bug +----------------> bug_task |
# +--+--+                +-----+----+
#    |                         |
#    |                         |
#    |       +---------+       |
#    +-------> project <-------+
#       1..* +---------+ 1
#
# One bug has at least 1 bug_task.
# One bug_task belongs to exactly one bug.
# One bug can affect multiple projects
# One bug_task is specific to one project


from argparse import ArgumentParser
from launchpadlib.launchpad import Launchpad
import logging
import os


# Parameters
parser = ArgumentParser(description="Cleanup Launchpad (LP) Bugs")
parser.add_argument('projectname', help='The project to act on')
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')
parser.add_argument("--newbugs", action="store_true",
                    help="Cleanup inconsistencies in new bugs")
parser.add_argument('exceptions', type=int, nargs='*', help='Bugs to ignore')
parser.add_argument('--dryrun', action='store_true',
                    help='Do not actually do anything')
parser.add_argument("-v", "--verbose", action="store_true",
                    help="increase output verbosity")
args = parser.parse_args()


class LaunchpadCleanup(object):
    '''
    Triggers specific cleanups in Launchpad
    '''

    def __init__(self, project_name, server="staging", dryrun=True,
                 ignoreable_bug_ids=[]):
        self.project_name = project_name
        self.client = self._create_launchpad_client(server)
        self.dryrun = dryrun
        self.ignoreable_bug_ids = ignoreable_bug_ids
        logger.info("Created launchpad client for server '%s'", server)
        if self.dryrun:
            logger.info("That's a dry run, nothing will happen")

    def _create_launchpad_client(self, server):
        cachedir = os.path.expanduser("~/.launchpadlib/cache/")
        if not os.path.exists(cachedir):
            os.makedirs(cachedir, 0700)
        return Launchpad.login_with('openstack-cleanup', server, cachedir)

    def cleanup_new_bugs_with_assignee(self):
        """ A new bug with an assignee is in progress"""
        logger.info("Cleanup new bugs with an assignee")

        message = "@%s:\n\nSince you are set as assignee, I switch the " \
                  "status to 'In Progress'."
        subject = "Cleanup"

        project = self.client.projects[self.project_name]
        bug_tasks = project.searchTasks(status=['New'],
                                        omit_duplicates=True)
        switched_bugs = []

        for t in bug_tasks:
            bug_id = t.bug.id
            if bug_id in self.ignoreable_bug_ids:
                logger.debug("Ignore bug '%s'. ", bug_id)
                continue
            logger.debug("Checking bug '%s'", bug_id)
            assignee = t.assignee
            if assignee is None:
                continue
            t.status = 'In Progress'
            switched_bugs.append(bug_id)
            content = message % assignee.display_name
            if self.dryrun:
                logger.debug("DRYRUN: I would switch bug '%s'", bug_id)
                continue
            logger.debug("Switching status of bug '%s'", bug_id)
            t.lp_save()
            t.bug.newMessage(content=content, subject=subject)

        logger.info("Switched bugs: '%s'", switched_bugs)

    def cleanup_incomplete_bugs_without_response(self):
        """ There should be a response of the reporter to incomplete bugs

            change status to invalid and make a comment
        """
        raise NotImplementedError("not yet done")

    def cleanup_in_progress_bugs_without_patches(self):
        """ If a bug is in progress but does not provide a patch set
            it is not in progress

            * Remove assignee
            * move back to last state (probably confirmed)
        """
        raise NotImplementedError("not yet done")


def create_logger():
    logger = logging.getLogger("os.bug.cleanup")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - '
                                  '%(levelname)s - %(message)s')
    file_handler = logging.FileHandler("os.bug.cleanup.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_level = logging.DEBUG if args.verbose else logging.INFO
    stream_handler.setLevel(stream_level)
    logger.addHandler(stream_handler)
    return logger

if __name__ == '__main__':
    logger = create_logger()
    logger.info("Started for project '%s'", args.projectname)

    cleanup = LaunchpadCleanup(args.projectname, args.test, args.dryrun)
    logger.info("Found project '%s'", args.projectname)

    if args.newbugs:
        cleanup.cleanup_new_bugs_with_assignee()

    logger.info("Finished for project '%s'", args.projectname)
