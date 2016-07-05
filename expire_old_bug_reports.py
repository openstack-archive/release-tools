#!/usr/bin/env python
#
# Closes Launchpad bug reports which are older than the oldest stable release
# (usually 18 months, see DAYS_SINCE_CREATED). It ignores bug reports which:
# * have a special comment (see STILL_VALID_FLAG).
# * have the status "In Progress"
# * have the importance "Wishlist"
#
# example execution:
#     $ python expire_old_bug_reports.py nova --no-dry-run
#
#
# Copyright 2016 Markus Zoeller (mzoeller@linux.vnet.ibm.com)
# Copyright 2016 Steven Hardy (shardy@redhat.com)
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


import argparse
import datetime
import logging
import os
from prettytable import PrettyTable
import sys
import time

from launchpadlib.launchpad import Launchpad
import lazr.restfulclient.errors

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
LOG = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Expire old bug reports.")
parser.add_argument('project_name',
                    help='The Launchpad project name (nova, cinder, ...).')
parser.add_argument('--verbose', '-v',
                    help='Enable debug logging.',
                    action="store_true")
parser.add_argument('--no-dry-run',
                    dest='no_dry_run',
                    help='Execute the expiration for real.',
                    action='store_true')
parser.add_argument('--credentials-file', '-c',
                    dest='lp_creds_file',
                    default=os.environ.get('LP_CREDS_FILE'),
                    help=('plain-text credentials file, '
                          'defaults to value of $LP_CREDS_FILE'))
args = parser.parse_args()
LOG.info(args)


PROJECT_NAME = args.project_name
if args.verbose:
    LOG.setLevel(logging.DEBUG)


DAYS_SINCE_CREATED = 30 * 18  # 18 months
STILL_VALID_FLAG = "CONFIRMED FOR: %(release_name)s"  # UPPER CASE
SUPPORTED_RELEASE_NAMES = []  # UPPER CASE

BUG_TASK_STATUS_AFTER_RUN = "Expired"
BUG_TASK_ASSIGNEE_AFTER_RUN = None
BUG_TASK_IMPORTANCE_AFTER_RUN = "Undecided"


class BugReport(object):

    def __init__(self, link, title, age, bug_task):
        self.link = link
        self.title = title.encode('ascii', 'replace')
        self.age = age
        self.bug_task = bug_task

    def __str__(self):
        data = {'link': self.link, 'title': self.title, 'age': self.age}
        return "{link} ({title}) - ({age} days)".format(**data)

    def __cmp__(self, other):
        return cmp(self.age, other.age)


def get_project_client():
    cache_dir = os.path.expanduser("~/.launchpadlib/cache/")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, 0o700)

    def no_credential():
        LOG.error("Can't proceed without Launchpad credential.")
        sys.exit()

    launchpad = Launchpad.login_with(
        application_name=PROJECT_NAME + '-bugs',
        service_root='production',
        launchpadlib_dir=cache_dir,
        credential_save_failed=no_credential,
        credentials_file=args.lp_creds_file)
    project = launchpad.projects[PROJECT_NAME]
    return project


def fill_supported_release_names(lp_project):
    LOG.info("filling supported release names...")
    for s in lp_project.series:
        if s.active:
            # stable branch names
            SUPPORTED_RELEASE_NAMES.append(s.name.upper())
    # master name
    SUPPORTED_RELEASE_NAMES.append(lp_project.development_focus.name.upper())
    LOG.info("filled supported release names: %s", SUPPORTED_RELEASE_NAMES)


def bug_is_still_valid(bug):
    for message in bug.messages:
        for release_name in SUPPORTED_RELEASE_NAMES:
            flag = STILL_VALID_FLAG % {'release_name': release_name}
            if flag in message.content:
                return True
    return False


def get_expired_reports(lp_project):
    LOG.info("getting potentially expired reports...")
    bug_tasks = lp_project.searchTasks(
        status=["New", "Confirmed", "Triaged"],
        importance=["Unknown", "Undecided", "Critical", "High", "Medium",
                    "Low"],  # ignore 'wishlist'; they get special treatment
        omit_duplicates=True,
        order_by="datecreated")
    today = datetime.datetime.today()
    expired = []

    for bug_task in bug_tasks:
        # remove the timezone info as it disturbs the calculation of the diff
        diff = today - bug_task.date_created.replace(tzinfo=None)
        if diff.days < DAYS_SINCE_CREATED:
            break
        if bug_is_still_valid(bug_task.bug):
            continue
        expired.append(BugReport(link=bug_task.web_link,
                                 title=bug_task.bug.title,
                                 age=diff.days,
                                 bug_task=bug_task))
    LOG.info("got %d potentially expired reports." % len(expired))
    return expired


def expire_bug_report(bug_report):
    subject = "Cleanup EOL bug report"
    comment = """
This is an automated cleanup. This bug report has been closed because it
is older than %(mm)d months and there is no open code change to fix this.
After this time it is unlikely that the circumstances which lead to
the observed issue can be reproduced.

If you can reproduce the bug, please:
* reopen the bug report (set to status "New")
* AND add the detailed steps to reproduce the issue (if applicable)
* AND leave a comment "CONFIRMED FOR: <RELEASE_NAME>"
  Only still supported release names are valid (%(supported_releases)s).
  Valid example: CONFIRMED FOR: %(valid_release_name)s
""" % {'mm': DAYS_SINCE_CREATED / 30,
       'supported_releases': ', '.join(SUPPORTED_RELEASE_NAMES),
       'valid_release_name': SUPPORTED_RELEASE_NAMES[0]}

    bug_task = bug_report.bug_task
    bug_task.status = BUG_TASK_STATUS_AFTER_RUN
    bug_task.assignee = BUG_TASK_ASSIGNEE_AFTER_RUN
    bug_task.importance = BUG_TASK_IMPORTANCE_AFTER_RUN
    try:
        if args.no_dry_run:
            bug_task.lp_save()
            bug_task.bug.newMessage(subject=subject, content=comment)
        LOG.debug("expired bug report %s" % bug_report)
    except lazr.restfulclient.errors.ServerError as e:
        LOG.error(" - TIMEOUT during save ! (%s)" % e, end='')
    except Exception as e:
        LOG.error(" - ERROR during save ! (%s)" % e, end='')


def write_expired_table_to_file(expired_reports, file_name):
    x = PrettyTable()
    x.field_names = ["Bug #", "Title", "Age (d)"]
    x.align["Bug #"] = "r"
    x.align["Title"] = "l"
    x.align["Age (d)"] = "r"
    for r in expired_reports:
        x.add_row([r.bug_task.bug.id, r.title, r.age])
    with open(file_name, 'w') as w:
        w.write(str(x))


def main():
    if args.no_dry_run:
        LOG.info("This is not a drill! Bug reports will be closed for real!")
        time.sleep(4)  # in case you wanna ctrl-c this
    else:
        LOG.info("This is just a dry-run, nothing will happen.")
    lp_project = get_project_client()
    fill_supported_release_names(lp_project)
    expired_reports = get_expired_reports(lp_project)
    LOG.info("starting expiration...")
    for e in expired_reports:
        expire_bug_report(e)
    LOG.info("expired %d bug reports", len(expired_reports))
    LOG.info("writing an ASCII table for notification purposes...")
    file_name = "expired_bug_reports_%s" % datetime.datetime.now().isoformat()
    write_expired_table_to_file(expired_reports, file_name)
    LOG.info("wrote ASCII table to file %s", file_name)


if __name__ == '__main__':
    LOG.info("starting script...")
    main()
    LOG.info("end script")
