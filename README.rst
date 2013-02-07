openstack-releasing - A set of scripts to handle OpenStack release process
==========================================================================

Prerequisites
-------------

You'll need the following Python modules installed:
 - launchpadlib


upload_release.py
-----------------

This script grabs a tarball from tarballs.openstack.org and uploads it
to Launchpad, marking the milestone released and inactive in the process.

The script prompts you to confirm that the tarball looks like the one you
intend to release, and to sign the tarball upload.

Examples:

./upload_release.py nova 2013.1 --milestone=grizzly-3

  Uploads Nova's nova-2013.1~g3.tar.gz to the grizzly-3
  milestone as nova-2013.1~g3.tar.gz

./upload_release.py glance 2013.1 --test

  Uploads Glance's current glance-milestone-proposed.tar.gz to the final
  "2013.1" milestone as glance-2013.1.tar.gz, on Launchpad staging server

./upload_release.py cinder 2012.2.3 --tarball=stable-folsom

  Uploads Cinder's current cinder-stable-folsom.tar.gz to the 2012.2.3
  milestone as cinder-2012.2.3.tar.gz

