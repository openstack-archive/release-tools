#!/usr/bin/python
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

import argparse
import datetime
import os.path
import subprocess
import sys
import tempfile
import time
import urllib

from launchpadlib.launchpad import Launchpad


def abort(code, errmsg):
    print >> sys.stderr, errmsg
    sys.exit(code)


# Argument parsing
parser = argparse.ArgumentParser(description='Grab tarball and release it '
                                             'on LP as milestone or version.')
parser.add_argument('project', help='Project to publish release for (nova)')
parser.add_argument('version', help='Version under development (2013.1)')
parser.add_argument("--milestone", help='Milestone to publish (grizzly-3)')
parser.add_argument("--tarball",
                    help='Tarball to fetch (defaults to version[~milestone])')
parser.add_argument("--test", action='store_const', const='staging',
                    default='production', help='Use LP staging server to test')
args = parser.parse_args()

if args.milestone is None:
    milestone = args.version
else:
    milestone = args.milestone

# Connect to LP
print "Connecting to Launchpad..."
try:
    launchpad = Launchpad.login_with('openstack-releasing', args.test)
except Exception, error:
    abort(2, 'Could not connect to Launchpad: ' + str(error))

# Retrieve milestone
print "Checking milestone..."
try:
    lp_proj = launchpad.projects[args.project]
except KeyError:
    abort(2, 'Could not find project: %s' % args.project)

for lp_milestone in lp_proj.all_milestones:
    if lp_milestone.name == milestone:
        if lp_milestone.release:
            abort(2, 'Milestone %s was already released !' % milestone)
        if args.milestone:
            short_ms = lp_milestone.code_name.lower()
            if not short_ms.startswith("rc"):
                short_ms = "b" + args.milestone[-1:]
            if len(short_ms) < 2 or len(short_ms) > 3:
                abort(2, 'Bad code name for milestone: %s' % short_ms)
        break
else:
    abort(2, 'Could not find milestone: %s' % milestone)

# Retrieve tgz, check contents and MD5
print "Downloading tarball..."
tmpdir = tempfile.mkdtemp()
if args.tarball is None:
    if args.milestone is None:
        base_tgz = "%s-%s.tar.gz" % (args.project, args.version)
    else:
        base_tgz = "%s-%s.%s.tar.gz" % (args.project, args.version, short_ms)
else:
    base_tgz = "%s-%s.tar.gz" % (args.project, args.tarball)
url_tgz = "http://tarballs.openstack.org/%s/%s" % (args.project, base_tgz)
tgz = os.path.join(tmpdir, base_tgz)

(tgz, message) = urllib.urlretrieve(url_tgz, filename=tgz)

try:
    subprocess.check_call(['tar', 'ztvf', tgz])
except subprocess.CalledProcessError, e:
    abort(2, '%s is not a tarball. Bad revision specified ?' % base_tgz)

md5 = subprocess.check_output(['md5sum', tgz]).split()[0]

# Sign tgz
print "Signing tarball..."
sig = tgz + '.asc'
if not os.path.exists(sig):
    print 'Calling GPG to create tgz signature...'
    subprocess.check_call(['gpg', '--armor', '--sign', '--detach-sig', tgz])

# Read contents
with open(tgz) as tgz_file:
    tgz_content = tgz_file.read()
with open(sig) as sig_file:
    sig_content = sig_file.read()

# Mark milestone released
print "Marking milestone released..."
if args.milestone:
    release_notes = "This is another milestone (%s) on the road to %s %s." \
        % (args.milestone, args.project.capitalize(), args.version)
else:
    release_notes = "This is %s %s release." \
        % (args.project.capitalize(), args.version)

lp_release = lp_milestone.createProductRelease(
                 date_released=datetime.datetime.utcnow(),
                 release_notes=release_notes)

# Mark milestone inactive
print "Marking milestone inactive..."
lp_milestone.is_active = False
lp_milestone.lp_save()

# Upload file
print "Uploading release files..."
if args.milestone:
    final_tgz = "%s-%s.%s.tar.gz" % (args.project, args.version, short_ms)
    description = '%s "%s" milestone' % \
                  (args.project.capitalize(), args.milestone)
else:
    final_tgz = "%s-%s.tar.gz" % (args.project, args.version)
    description = '%s %s release' % (args.project.capitalize(), args.version)

lp_file = lp_release.add_file(file_type='Code Release Tarball',
                              description=description,
                              file_content=tgz_content,
                              filename=final_tgz,
                              signature_content=sig_content,
                              signature_filename=final_tgz + '.asc',
                              content_type="application/x-gzip; "
                                           "charset=binary")

# Check LP-reported MD5
print "Checking MD5s..."
time.sleep(2)
result_md5_url = "http://launchpad.net/%s/+download/%s/+md5" % \
                 (lp_release.self_link[30:], final_tgz)
result_md5_file = urllib.urlopen(result_md5_url)
result_md5 = result_md5_file.read().split()[0]
result_md5_file.close()
if md5 != result_md5:
    abort(3, 'MD5sums (%s/%s) do not match !' % (md5, result_md5))

# Finished
print md5
print "Done!"
