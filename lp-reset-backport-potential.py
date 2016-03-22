#!/usr/bin/env python

"""
This Launchpad tool is used to reset <release>-backport-potential tags once
backports are merged.
"""

import argparse

from launchpadlib.launchpad import Launchpad


RELEASES = ('juno', 'kilo', 'liberty', 'mitaka')


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Reset -backport-potential tags for closed bugs.')
    parser.add_argument(
        'projects', metavar='N', type=str, nargs='+',
        help='Launchpad project names')
    return parser.parse_args()


def _cleanup_project(lp, project):
    print('Processing project %s...' % project)
    for release in RELEASES:
        in_tag = 'in-stable-%s' % release
        potential_tag = '%s-backport-potential' % release

        for task in lp.projects[project].searchTasks(tags=[potential_tag]):
            bug = task.bug
            tags = bug.tags

            if in_tag in tags:
                print("Removing %s tag for %s" % (potential_tag, bug))
                tags.remove(potential_tag)
                bug.tags = tags
                bug.lp_save()


def main():
    args = _parse_args()

    lp = Launchpad.login_with('reset-backport-potential', 'production')

    for project in args.projects:
        _cleanup_project(lp, project)


if __name__ == '__main__':
    main()
