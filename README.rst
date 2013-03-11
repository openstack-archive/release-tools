openstack-releasing - A set of scripts to handle OpenStack release process
==========================================================================

Prerequisites
-------------

You'll need the following Python modules installed:
 - launchpadlib


repo_tarball_diff.sh
--------------------

This script fetches a specific branch from a git repository into a temp
directory and compares its content with the content of a tarball produced
from it (using "python setup.py sdist"). The difference should only contain
additional generated files (Changelog, AUTHORS...) and missing ignored
files (.gitignore...).

Example:

./repo_tarball_diff.sh nova master

  Check the difference between Nova master branch contant and a tarball
  that would be generated from it.


process_bugs.py
---------------

This script fetches bugs for a project (by default all "FixCommitted" bugs)
and sets a milestone target for them (--settarget) and/or sets their status
to "Fix Released" (--fixrelease).

It ignores bugs that have already a milestone set, if that milestone does
not match the one in --settarget.

Examples:

./process_bugs.py nova --settarget=grizzly-3 --fixrelease

  Sets the target for all Nova FixCommitted bugs to grizzly-3 
  and mark them 'Fix Released'.

./process_bugs.py glance --settarget=grizzly-2 --status='Fix Released' --test

  Test setting the target for all untargeted Glance FixReleased bugs to
  grizzly-2 on Launchpad Staging servers.

upload_release.py
-----------------

This script grabs a tarball from tarballs.openstack.org and uploads it
to Launchpad, marking the milestone released and inactive in the process.

The script prompts you to confirm that the tarball looks like the one you
intend to release, and to sign the tarball upload.

Examples:

./upload_release.py nova 2013.1 --milestone=grizzly-3

  Uploads Nova's nova-2013.1.g3.tar.gz to the grizzly-3
  milestone as nova-2013.1.g3.tar.gz

./upload_release.py glance 2013.1 --test

  Uploads Glance's current glance-milestone-proposed.tar.gz to the final
  "2013.1" milestone as glance-2013.1.tar.gz, on Launchpad staging server

./upload_release.py cinder 2012.2.3 --tarball=stable-folsom

  Uploads Cinder's current cinder-stable-folsom.tar.gz to the 2012.2.3
  milestone as cinder-2012.2.3.tar.gz

