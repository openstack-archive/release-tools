#!/usr/bin/env python
#
# Script to upload an OpenStack release to Launchpad
#
# Copyright 2011-2013 Thierry Carrez <thierry@openstack.org>
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

from __future__ import print_function
import argparse
import datetime
import os.path
import subprocess
import sys
import tempfile
import time

from six.moves.urllib import request as urlreq

import launchpadlib.launchpad


def abort(code, errmsg):
    print(errmsg, file=sys.stderr)
    sys.exit(code)


# Argument parsing
parser = argparse.ArgumentParser(description='Grab tarball and release it '
                                             'on LP as milestone or version.')
parser.add_argument('project', help='LP project to publish release for (nova)')
parser.add_argument('version', help='Version under development (2015.1.0)')
parser.add_argument("--milestone", help='Milestone to publish (kilo-2)')
parser.add_argument("--deliverable", help='Project name in the tarball. '
                    'Defaults to project')
parser.add_argument("--nop", action='store_true',
                    help='Only create release, do not upload tarball')
parser.add_argument("--tarball",
                    help='Tarball to fetch (defaults to version[~milestone])')
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')
args = parser.parse_args()

if args.milestone is None:
    milestone = args.version
else:
    milestone = args.milestone

if args.deliverable is None:
    args.deliverable = args.project

# Connect to LP
print("Connecting to Launchpad...")
try:
    launchpad = launchpadlib.launchpad.Launchpad.login_with('openstack-releasing', args.test)
except Exception as error:
    abort(2, 'Could not connect to Launchpad: ' + str(error))

# Retrieve milestone
print("Checking milestone...")
try:
    lp_proj = launchpad.projects[args.project]
except KeyError:
    abort(2, 'Could not find project: %s' % args.project)

for lp_milestone in lp_proj.all_milestones:
    if lp_milestone.name == milestone:
        if lp_milestone.release:
            print('Milestone %s is already released' % milestone)
            if args.deliverable != args.project:
                print('We are probably just trying to add %s to LP %s.' %
                      (args.deliverable, args.project))
            else:
                abort(2, 'That looks like an error!')
        if args.milestone:
            short_ms = lp_milestone.code_name.lower()
            if not short_ms.startswith("rc"):
                preversion = ".0b" + args.milestone[-1:]
            else:
                preversion = ".0" + short_ms
        else:
            preversion = ""
        break
else:
    abort(2, 'Could not find milestone: %s' % milestone)

if not args.nop:
    # Retrieve tgz, check contents and MD5
    print("Downloading tarball...")
    tmpdir = tempfile.mkdtemp()
    if args.tarball is None:
        base_tgz = ("%s-%s%s.tar.gz" %
                    (args.deliverable, args.version, preversion))
    else:
        base_tgz = ("%s-%s.tar.gz" %
                    (args.deliverable, args.tarball))
    url_tgz = ("http://tarballs.openstack.org/%s/%s" %
               (args.deliverable, base_tgz))
    tgz = os.path.join(tmpdir, base_tgz)

    (tgz, message) = urlreq.urlretrieve(url_tgz, filename=tgz)

    try:
        subprocess.check_call(['tar', 'ztvf', tgz])
    except subprocess.CalledProcessError as e:
        abort(2, '%s is not a tarball. Bad revision specified ?' % base_tgz)

    md5 = subprocess.check_output(['md5sum', tgz]).split()[0]

    # Sign tgz
    print("Signing tarball...")
    sig = tgz + '.asc'
    if not os.path.exists(sig):
        print('Calling GPG to create tgz signature...')
        subprocess.check_call(
            ['gpg', '--armor', '--sign', '--detach-sig', tgz])

    # Read contents
    with open(tgz) as tgz_file:
        tgz_content = tgz_file.read()
    with open(sig) as sig_file:
        sig_content = sig_file.read()

# Mark milestone released
print("Marking milestone released...")
if args.nop:
    rel_notes = ""
else:
    if args.milestone:
        rel_notes = ("This is another milestone (%s) on the road to %s %s." %
                     (args.milestone, args.project.capitalize(), args.version))
    else:
        rel_notes = ("This is %s %s release." %
                     (args.project.capitalize(), args.version))

if lp_milestone.release:
    lp_release = lp_milestone.release
else:
    lp_release = lp_milestone.createProductRelease(
        date_released=datetime.datetime.utcnow(),
        release_notes=rel_notes)

# Mark milestone inactive
print("Marking milestone inactive...")
lp_milestone.is_active = False
lp_milestone.lp_save()

if not args.nop:
    # Upload file
    print("Uploading release files...")
    final_tgz = ("%s-%s%s.tar.gz" %
                 (args.deliverable, args.version, preversion))
    if args.milestone:
        description = ('%s "%s" milestone' %
                       (args.deliverable.capitalize(), args.milestone))
    else:
        description = ('%s %s release' %
                       (args.deliverable.capitalize(), args.version))

    lp_file = lp_release.add_file(file_type='Code Release Tarball',
                                  description=description,
                                  file_content=tgz_content,
                                  filename=final_tgz,
                                  signature_content=sig_content,
                                  signature_filename=final_tgz + '.asc',
                                  content_type="application/x-gzip; "
                                               "charset=binary")

    # Check LP-reported MD5
    print("Checking MD5s...")
    time.sleep(2)
    result_md5_url = ("http://launchpad.net/%s/+download/%s/+md5" %
                      (lp_release.self_link[30:], final_tgz))
    result_md5_file = urlreq.urlopen(result_md5_url)
    result_md5 = result_md5_file.read().split()[0]
    result_md5_file.close()
    if md5 != result_md5:
        abort(3, 'MD5sums (%s/%s) do not match !' % (md5, result_md5))

    # Finished
    print(md5)

print("Done!")
