#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import optparse
import os
import sys

from subprocess import check_output

GERRIT_USER = None
GERRIT_HOST = None
DRY_RUN = False

DEFAULT_REL = 'icehouse'
CODENAMES = {
    '2013.1': 'grizzly',
    '2013.2': 'havana',
    '2014.1': 'icehouse',
    '2014.2': 'juno',
    '2015.1': 'kilo',
}

PROJECTS = {}
PROJECTS['grizzly'] = [
    'nova', 'glance', 'keystone', 'neutron', 'cinder', 'horizon'
]
PROJECTS['havana'] = ['heat', 'ceilometer']
PROJECTS['havana'].extend(PROJECTS['grizzly'])
PROJECTS['icehouse'] = ['trove']
PROJECTS['icehouse'].extend(PROJECTS['havana'])
PROJECTS['juno'] = ['sahara']
PROJECTS['juno'].extend(PROJECTS['icehouse'])
PROJECTS['kilo'] = ['ironic']
PROJECTS['kilo'].extend(PROJECTS['juno'])


logging.basicConfig(level=logging.INFO)


def run_command(cmd):
    _cmd = [
        'ssh', '-p', '29418', '%s@%s' % (GERRIT_USER, GERRIT_HOST),
        'gerrit'
    ]
    _cmd += cmd
    if 'query' in _cmd:
        _cmd += ['--format', 'json']

    res = check_output(_cmd)

    if 'query' not in cmd:
        return res
    out = []
    for ln in res.split('\n'):
        try:
            out.append(json.loads(ln))
        except:
            pass
    return out


def open_reviews(projects, branch):
    cmd = ['query', '--current-patch-set',
           'branch:%s status:open ( %s )' % (branch, ' OR '.join(projects))]
    reviews = run_command(cmd)
    return [r for r in reviews if r.get('id')]


def reviews_hard_freeze(reviews):
    return [r for r in reviews if r.get('id')]


def reviews_soft_freeze(reviews):
    out = []
    for review in reviews:
        try:
            cps = review['currentPatchSet']
        except KeyError:
            continue

        approved = False
        for app in cps.get('approvals', []):
            if (app.get('description', '') == 'Workflow' and
               app.get('value') == '1'):
                logging.info('Skipping approved review %s' % review['id'])
                approved = True
                break

        if not approved:
            out.append(review)
    return out


def openstack_release(rel):
    for r, c in CODENAMES.iteritems():
        if rel.startswith(r):
            return c
    logging.error('Invalid release: %s' % rel)
    sys.exit(1)


def revision(review):
    cps = review.get('currentPatchSet')
    if not cps:
        return None
    return cps.get('revision')


class Revision(object):
    def __init__(self, change, url):
        self.change = change
        self.url = url

    def __str__(self):
        return '%s # %s' % (self.change, self.url)


FREEZE_MSG = r"""
stable/%s freeze for %s

The stable branch is frozen to allow testing before the release. Freeze
exceptions can be proposed on openstack-dev mailing list with [stable] tag in
subject. Once exception request is sent, stable-maint-core team will try to
reach consensus.

More details at: https://wiki.openstack.org/wiki/StableBranch
"""


def freeze(reviews, rel):
    logging.info('freezing %s reviews.' % len(reviews))
    msg = FREEZE_MSG % (openstack_release(rel), rel)
    frozen = []
    for review in reviews:

        _revision = revision(review)
        if not _revision:
            continue
        change = Revision(_revision, review['url'])

        cmd = ["review",
               "--message '%s' --code-review '-2' %s" % (msg, _revision)]
        if DRY_RUN:
            print 'Would run: gerrit %s' % ' '.join(cmd)
            frozen.append(change)
            continue

        try:
            if DRY_RUN:
                logging.info('Would run: gerrit %s' % cmd)
                continue
            run_command(cmd)
            frozen.append(change)
        except:
            logging.error('Failed to -2: %s' % _revision)
            continue
        logging.info('-2: %s' % change)

    return frozen


def thaw(revisions, rel):
    msg = 'stable/%s branches open' % openstack_release(rel)

    for rev in revisions:
        cmd = ["review",
               "--message '%s' --code-review '0' %s" % (msg, rev)]
        if DRY_RUN:
            print 'Would run: gerrit %s' % ' '.join(cmd)
            continue
        try:
            run_command(cmd)
            logging.info('thawed: %s' % rev)

        except:
            logging.error('Failed to thaw: %s' % rev)
        logging.info('thawed: %s' % rev)
        print ' '.join(cmd)


def parse_rev_file(f):
    _in = open(f).readlines()
    out = []
    for l in _in:
        if '#' in l:
            change = l.split('#')[0].strip()
        else:
            change = l.strip()
        out.append(change)
    return out


def get_review(change_no):
    cmd = ['query', '--current-patch-set', change_no]
    review = run_command(cmd)
    if len(review) == 1:
        logging.warning('Change %s not found' % change_no)
        return
    return review[0]


def filter_skip(reviews):
    skips = parse_rev_file('/tmp/skip')
    out = []
    for review in reviews:
        if revision(review) not in skips:
            out.append(review)
        else:
            print 'skip: %s' % revision(review)
    return out

if __name__ == '__main__':
    usage = 'usage: %prog [options] query|freeze|thaw'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-r', '--release',
                      default=None, action='store', dest='release',
                      help='Openstack release, eg 2013.1.3')
    parser.add_option('-s', '--soft-freeze',
                      default=False, action='store_true', dest='soft_freeze')
    parser.add_option('-o', '--outfile',
                      default='stable_freeze.txt', action='store',
                      dest='outfile',
                      help='File to save frozen reviews during freeze'
                           '(default: stable_freeze.txt)')
    parser.add_option('-i', '--infile',
                      default='stable_freeze.txt', action='store',
                      dest='infile',
                      help='File to read frozen reviews during thaw '
                           '(default: stable_freeze.txt)')
    parser.add_option('-d', '--dry', default=False, dest='dry_run',
                      action='store_true', help='Dry run')
    parser.add_option('-u', '--user', default=os.getenv('GERRIT_USER'),
                      dest='gerrit_user', action='store',
                      help='Gerrit username for ssh access')
    parser.add_option('-g', '--gerrit_host',
                      default=os.getenv('GERRIT_HOST', 'review.openstack.org'),
                      dest='gerrit_host', action='store',
                      help='Gerrit server hostname (default: '
                           'review.openstack.org)')
    parser.add_option('-c', '--change', default=None, dest='changes',
                      action='append',
                      help='Freeze a specific review(s) and append info to '
                            'outfile.  Use gerrit review #, space separated '
                            'for multiple')
    (opts, args) = parser.parse_args()
    if opts.dry_run:
        DRY_RUN = True

    GERRIT_HOST = opts.gerrit_host
    GERRIT_USER = opts.gerrit_user
    if not GERRIT_USER:
        logging.error('must specify gerrit ssh username')
        sys.exit(1)

    if not args or len(args) > 1:
        parser.print_help()
        sys.exit(1)

    if not opts.release:
        logging.error('must specify release')
        sys.exit(1)

    action = args[0]

    os_rel = openstack_release(opts.release)
    projects = ['openstack/%s' % p for p in PROJECTS[os_rel]]
    branch = 'stable/%s' % os_rel

    if opts.changes:
        reviews = []
        for c in opts.changes:
            r = get_review(c)
            if r:
                reviews.append(r)
    else:
        reviews = open_reviews(projects, branch)
        logging.info('Found %s open reviews for %s' % (len(reviews), branch))

    if action in ['freeze', 'query']:
        if opts.soft_freeze:
            logging.info(
                'Soft-freeze, filtering reviews that are approved but '
                'pending gate verification')
            total = len(reviews)
            to_freeze = reviews_soft_freeze(reviews)
            logging.info(
                'Skipped freezing %s reviews that are pending gate '
                'verification' % (total - len(to_freeze)))
        else:
            to_freeze = reviews

        if action == 'query':
            print '\n\n'
            logging.info('%s open reviews to be frozen: ' % len(to_freeze))
            print '\n'
            print '\n'.join([rev['id'] for rev in to_freeze])
            sys.exit(0)
        elif action == 'freeze':
            to_freeze = filter_skip(to_freeze)
            frozen = freeze(to_freeze, opts.release)

            if opts.changes:
                # if individual changes are specified, we're likely adding
                # a -2 to new post-freeze reviews. append these to the list
                # of frozen reviews.
                mode = 'a+'
            else:
                mode = 'wb'

            if not DRY_RUN:
                with open(opts.outfile, mode) as out:
                    for r in frozen:
                        out.write('%s\n' % r)
            else:
                logging.info('Would write to %s (%s):' % (opts.outfile, mode))
                for r in frozen:
                    print r

    if action in ['thaw']:
        to_thaw = []
        _in = open(opts.infile).readlines()
        for l in _in:
            if '#' in l:
                change = l.split('#')[0].strip()
            else:
                change = l.strip()
            to_thaw.append(change)
        logging.info('Will thaw %s reviews for %s' % (len(to_thaw), branch))
        thaw(to_thaw, opts.release)
