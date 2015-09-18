==========================================================================
openstack-releasing - A set of scripts to handle OpenStack release process
==========================================================================

Prerequisites
=============

You'll need the following Python modules installed:
 - launchpadlib

similar_tarballs.sh also requires that you have tardiff installed.  If it's not
packaged for your distribution, you can find it at
http://tardiff.coolprojects.org/.

Top-level scripts
=================

The top-level scripts call the various base tools to get their work done.


milestone.sh
------------

This script handles all development milestone publication tasks. It creates
a tag, pushes it, waits for the tarball build, lets you doublecheck tarball
similarities, turns FixCommitted bugs into FixReleased ones (and targets them
to the milestone), and upload the resulting tarball to Launchpad (while
marking it released).

It supports special cases for the release of a swift intermediary release
(where bugs should have been processed using swiftrc.sh beforehand), and
oslo-incubator (where no tarball is generated or needs to be uploaded).

Example:

./milestone.sh kilo-3 HEAD keystone

  Apply 2015.1.0b3 tag to HEAD of keystone master branch, check resulting
  tarball, mark FixCommitted bugs as released, upload tarball to Launchpad
  and mark Launchpad milestone released.


intermediary.sh
---------------

This script handles cycle-with-intermediary project releases. It creates
a tag, pushes it, waits for the tarball build, turns FixCommitted bugs into
FixReleased ones (and targets them to the milestone), and upload the
resulting tarball to Launchpad (while marking it released).

Example:

./intermediary.sh 2.4.0 HEAD swift

  Apply 2.4.0 tag to HEAD of swift master branch, check resulting tarball,
  mark FixCommitted bugs as released, upload tarball to Launchpad and mark
  Launchpad milestone released.


rccut.sh
--------

Final release for pre-versioned components follows a slightly different
process. Just before RC1 we need to create a stable/* release branch.
rccut.sh creates a stable/$SERIES branch from the specified SHA, and turns
all Launchpad bugs for the RC1 milestone to FixReleased (which means
"present in the release branch").

It supports deliverables with multiple repositories, using an additional
parameter to point to the main deliverable (in which case it skips Launchpad
update). It special-cases oslo-incubator, where it doesn't wait for a tarball
to be built.

Examples:

./rccut.sh 7432f32d838ab346c liberty nova

  Create a series/liberty branch for Nova at commit 7432f32d838ab346c, and
  mark FixCommitted bugs FixReleased, while targeting them to the juno-rc1
  milestone.

./rccut.sh 3472368b3a546d liberty neutron-fwaas neutron

  Create a series/liberty branch for neutron-fwaas at commit 3472368b3a546d.


rcdelivery.sh
-------------

This script is used for pre-versioned projects to publish RCs and final
release from the stable/$SERIES branch. It applies the RC or final tag,
pushes it, waits for the tarball build, and uploads the resulting
tarball to Launchpad (while marking it released).

It supports deliverables with multiple repositories, using an additional
parameter to point to the main deliverable (in which case it uploads to the
main Launchpad page). It special-cases oslo-incubator, where no tarball is
generated or needs to be uploaded.

Examples:

./rcdelivery.sh kilo rc1 cinder

  Push 2015.1.0rc1 tag to current cinder stable/kilo branch HEAD, wait for
  the tarball build, and upload the resulting tarball to Launchpad (while
  marking it released).

./rcdelivery kilo final neutron-fwaas neutron

  Push 2015.1.0 final tag to current neutron-fwaas stable/kilo branch HEAD
  (which should be the last RC), wait for the tarball build, and upload the
  resulting tarball to the "neutron" Launchpad page.


release_postversion.sh
----------------------

Release a project using post-versioning (without a version specified
in setup.cfg).

The arguments are:

* the release series
* the version number
* the git reference (SHA or "HEAD")
* the launchpad project name

Examples:

./release_postversion.sh liberty 1.13.0 85c069e oslo.messaging

release_many.sh
---------------

Run release_postversion.sh for many projects one after the
other. Requires an input file with one line per library, containing::

  version hash project

Optionally, the line can also include a series name, for example::

  1.13.0 85c069e oslo.messaging
  1.8.3 0f24108 oslo.messaging kilo

release-notes
-------------

This produces a set of release notes intended to be sent as an
announcement email when a new library or package is produced. It is
more suitable for libraries than for the major projects, because it
includes a list of all of the changes and diff-stats output to show
which files changed.

The script parses the README.rst to find a line matching "``Bugs:``",
extracts the URL following the colon, and includes that information in
the output.

The bugs URL is converted to a launchpad project URL and combined with
the final version number to produce a *milestone* URL.

The script uses ``python setup.py`` to determine the project name and
the one-line description to include in the output text.

Examples:

release-notes ~/repos/openstack/oslo.config 1.7.0 1.8.0

  Print the release notes between versions 1.7.0 and 1.8.0 for the
  project in the ``~/repos/openstack/oslo.config`` directory.

release-notes --show-dates --changes-only ~/repos/openstack/oslo.config 1.8.0 HEAD

  Print the list of changes after 1.8.0 for the project in the
  ``~/repos/openstack/oslo.config`` directory, including the date of
  the change but leaving out the email message boilerplate. This mode
  is useful for examining the list of unreleased changes in a project
  to decide if a release is warranted and to pick a version number.

list_unreleased_changes.sh
--------------------------

Given a branch and one or more repositories, produce a list of the
changes in those repositories since their last tag on that
branch. This is useful for deciding if a project needs to prepare a
release, and for predicting what the next release version should be by
looking at the commit logs.

./list_unreleased_changes.sh master openstack/oslo.config

  Print the list of changes in ``openstack/oslo.config`` along the
  master branch.

./list_unreleased_changes.sh stable/kilo $(list-repos --code-only --team Oslo)

  Print the list of changes in the ``stable/kilo`` branch of all Oslo
  libraries.

list_oslo_unreleased_changes.sh
-------------------------------

Runs list_unreleased_changes.sh for all of the Oslo library
repositories.

./list_oslo_unreleased_changes.sh stable/kilo

is equivalent to:

./list_unreleased_changes.sh stable/kilo $(list-repos --code-only --team Oslo)

make_library_stable_branch.sh
-----------------------------

Libraries do not use proposed branches, and go directly to creating
stable branches using a pre-tagged release version. This script makes
that easy to coordinate and ensures that the desired version also
exists in launchpad as a released milestone and by updating the
.gitreview file in the new branch for future submissions.

make_feature_branch.sh
----------------------

Feature branches need to have "feature/" at the beginning of the name
and should have their ``.gitreview`` updated when the branch is
created.

list-repos
----------

Read the project list from the governance repository and print a list
of the repositories, filtered by team and/or tag.

list-repos --team Oslo
list-repos --tag release:managed --tag type:library

update_git_review.sh
--------------------

Update the .gitreview file in a specific branch of a checked out
repositories.

./update_git_review.sh stable/kilo ~/repos/openstack/oslo.*

launchpad-login
---------------

Test or configure the launchpad credentials. This will set up a
keyring entry for the launchpad site, prompt for credentials, and
handle the OAuth handshake. All of the other launchpad-connected
commands will do these steps, too, but this command takes no other
action after logging in so it is safe to run it repeatedly.

check_library_constraints.sh
----------------------------

Script to check the current list of constraints against the most
recent release for all of the library projects. This script can be
used at any point, but is especially intended to ensure that the
constraints for things we release are all updated at the end of a
release cycle. To run the script, check out both the release-tools and
requirements repositories and then run the script as::

  $ check_library_constraints.sh /path/to/requirements-repository

Base tools
==========

milestone-close
---------------

Marks a Launchpad milestone as released and sets it inactive so no
more bugs or blueprints can be targeted to it.

Example::

  milestone-close oslotest 1.8.0

milestone-rename
----------------

Renames a Launchpad milestone.

Example:

::

  milestone-rename oslo.rootwrap next-juno 1.3.0

Rename oslo.rootwrap next-juno milestone to 1.3.0.


ms2version.py
-------------

Converts milestone code names (juno-1) to version numbers suitable for tags
(2014.2.b1). If used with --onlycheck, only checks that the milestone
exists in Launchpad (useful for Swift where the rules are different).

Examples:

./ms2version.py nova kilo-3

  Returns 2015.1.0b3 (after checking that the kilo-3 milestone exists in Nova)

./ms2version.py swift 2.1.0 --onlycheck

  Exists successfully if there is a 2.1.0 milestone in Swift.


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


similar_tarballs.sh
-------------------

This script compares the content of two tarballs on tarballs.openstack.org.

Example:

./similar_tarballs.sh nova stable-kilo 2015.1.0rc1

  Check content differences between nova-stable-kilo.tar.gz and
  nova-2015.1.0rc1.tar.gz, as found on http://tarballs.openstack.org.


process_bugs.py
---------------

This script fetches bugs for a project (by default all "FixCommitted" bugs,
or all open bugs targeted to a given milestone if you pass the --milestone
argument) and sets a milestone target for them (--settarget) and/or sets their
status to "Fix Released" (--fixrelease).

It ignores bugs that have already a milestone set, if that milestone does
not match the one in --settarget.

Examples:

./process_bugs.py nova --settarget=grizzly-3 --fixrelease

  Sets the target for all Nova FixCommitted bugs to grizzly-3 
  and mark them 'Fix Released'.

./process_bugs.py glance --settarget=grizzly-2 --status='Fix Released' --test

  Test setting the target for all untargeted Glance FixReleased bugs to
  grizzly-2 on Launchpad Staging servers.

./process_bugs.py neutron --milestone juno-3 --settarget juno-rc1

  Move all juno-3 open bugs from juno-3 to juno-rc1 milestone.


wait_for_tarball.py
-------------------

This script queries Jenkins tarball-building jobs to find either a job
matching the provided --mpsha SHA building milestone-proposed.tar.gz,
or a job matching the provided --tag. It then waits for that job completion
and reports the built tarball name.

Examples:

./wait_for_tarball.py cinder --mpsha=59089e56f674f5f94f67c5986e9a616bb669d846

  Looks for a cinder-branch-tarball job matching SHA 59089e... which would
  produce a milestone-proposed.tar.gz tarball, and waits for completion

./wait_for_tarball.py cinder --tag=2013.1.1

  Looks for a cinder-tarball job for tag "2013.1.1" and waits for completion.


upload_release.py
-----------------

This script grabs a tarball from tarballs.openstack.org and uploads it
to Launchpad, marking the milestone released and inactive in the process.
If used with the --nop argument, it will only mark the milestone released and
inactive (this is used for projects like oslo-incubator which do not release
source code).

The script prompts you to confirm that the tarball looks like the one you
intend to release, and to sign the tarball upload.

Examples:

./upload_release.py nova 2015.1.0 --milestone=kilo-3

  Uploads Nova's nova-2015.1.0b3.tar.gz to the kilo-3 milestone page.

./upload_release.py glance 2015.1.0 --test

  Uploads Glance's glance-2015.1.0.tar.gz to the final "2015.1.0" milestone
  as glance-2015.1.0.tar.gz, on Launchpad staging server

./upload_release.py cinder 2012.2.3 --tarball=stable-folsom

  Uploads Cinder's current cinder-stable-folsom.tar.gz to the 2012.2.3
  milestone as cinder-2012.2.3.tar.gz


consolidate_release_page.py
---------------------------

This script moves blueprints and bugs from interim milestones to the final
release milestone page, in order to show all bugs and features fixed during
the cycle. For Swift, this will only move X-rc* bugs and blueprints to
final X release.

The --copytask mode is an experimental variant where a series bugtask is
created and the release milestone is set on that bugtask, preserving the
information from the "development" bugtask (and the milestone the bug was
fixed in).

Examples:

./consolidate_release_page.py cinder kilo 2015.1.0

  Moves Cinder blueprints and bugs from intermediary kilo milestones
  to the final 2015.1 milestone page.

./consolidate_release_page.py --test swift grizzly 1.8.0

  Moves Swift 1.8.0-rc* blueprints and bugs to the final 1.8.0 page, on
  Launchpad staging server

./consolidate_release_page.py --copytask glance kilo 2015.1.0

  Moves Glance blueprints from intermediary kilo milestones to the final
  2015.1.0 milestone page. Creates kilo series task for all grizzly bugs
  and sets the milestone for those to 2015.1.0.


milestones-create
-----------------

This script lets you create milestones in Launchpad in bulk. It is given a
YAML description of the milestone dates and the projects to add milestones
to. The script is idempotent and can safely be run multiple times. See
create_milestones.sample.yaml for an example configuration file.

Example::

  milestones-create havana.yaml


milestone-ensure
----------------

This script lets you create one series and milestone in Launchpad. The
script is idempotent and can safely be run multiple times.

Example::

  milestone-ensure oslo.config liberty next-liberty


spec2bp.py
----------

This experimental script facilitates setting blueprint fields for approved
specs. It takes the project and blueprint name as arguments. For specs that
are still under review (--in-review) it will set them to "Blocked" (and
definition status to Review). For approved specs it will set definition
status to Approved, and set Spec URL. In both cases it will set the target
milestone, approver name and specified priority (by default, 'Low').

Examples:

./spec2bp.py glance super-spec --milestone=juno-2 --priority=Medium

  Glance's super-spec.rst was approved and you want to add it to juno-2,
  with Medium priority. This will do it all for you.

./spec2bp.py nova --specpath=specs/kilo/approved/my-awesome-spec.rst
  --in-review --milestone=juno-2

  Nova's my-awesome-spec.rst is still under review, but you would like to
  add the my-awesome-spec blueprint to juno-2 (marked Blocked). Since it's
  located in a non-standard path, we specify it using --specpath parameter.

./spec2bp.py nova my-awesome-spec --priority=High

  my-awesome-spec is now approved. You want to flip all the approval bits,
  but also change its priority to High. There is no need to pass --specpath
  again, spec2bp will infer it from the blueprint URL field.


stable_freeze.py
----------------

A script that can be used to quickly "freeze" all open reviews to a stable
branch.  It may also be used to "thaw" frozen reviews upon re-opening of
the branch for merges.  Reviews are frozen by adding a -2 and thawed by
reverting that and adding a 0.

Examples:

To view open reviews for stable/icehouse 2014.1.4:

./stable_freeze.py -r 2014.1.4 query

  View open reviews for stable/icehouse 2014.1.4.

./stable_freeze.py -r 2014.1.4 -o ~/openstack/2014.1.4-freeze.txt

  Freeze all open reviews proposed to stable/icehouse. 2014.1.4-freeze.txt will
  contain all frozen reviews and this can be used to thaw later on.

./stable_freeze -r 2014.1.4 -i ~/openstack/2014.1.4-freeze.txt thaw

  Thaw all reviews previously frozen and stored in 2014.1.4-freeze.txt.

./stable_freeze -r 2014.1.4 -i ~/openstack/2014.1.4-freeze.txt \
  -c 123777 -c 123778 freeze

  Freeze individual changes that have been proposed after the stable freeze
  period started.  References to these reviews will be appended to
  2014.1.4-freeze.txt to be unfrozen later on.


autokick.py
-----------

A script to periodically clean up blueprints (adjusting series goal based on
target milestone, and optionally kicking unpriotized blueprints from the
milestone. ttx is running it in a cron so you don't have to.

Examples:

To clean up Nova kilo blueprints:

./autokick.py nova kilo

highest_semver.py
-----------------

Reads a list of version tags from standard input and prints the
"highest" value as output, ignoring tags that don't look like valid
versions.


translation-cleanup.sh
----------------------

A script to cleanup translations for a release. It updates all
translation source files, downloads translation files and removes
translation files that are not sufficiently translated. It results in
a change that then needs to get reviewed and send to gerrits.

Examples:

To generate a cleanup patch for nova:

./translation-cleanup.sh kilo nova


adjust_blueprints.py
--------------------

Run around milestone release time, this script retrieves and parses the list
of blueprints for a given project and:

* sets the milestone target and series goal on recently-implemented blueprints

* removes the milestone target on incomplete milestone-targeted blueprints

Examples:

./adjust_blueprints.py nova liberty-1

  Displays proposed adjustments around Nova liberty-1 blueprints.

./adjust_blueprints.py nova liberty-1 --target --clean

  Targets missing implemented blueprints and cleans incomplete ones for Nova
  in liberty-1.

How to Release a Library
========================

Libraries should all be using post-versioning, getting their version
information from git tags and not having any version specifier in the
``setup.cfg``.

Library release requests are filed as patches to deliverables files in
the openstack/releases repository, see the README there for more
details.

Before beginning this process, you need to set up ``gpg`` with a valid
key, and authorize launchpad to run the release tools
commands. Authorizing launchpad can be tricky on a system that only
provides a terminal-based browser, since the launchpad site does not
work well with the default configuration of ``lynx`` (cookies and
referrer headers need to be enabled for the launchpad site). Newer
versions of launchpadlib also rely on keyring, which may require a
password for every command being run if you are not in a graphical
environment with a better interactive key manager. Talk with dhellmann
if you start a release and run into trouble with launchpad auth.

When a release request is ready to be approved, follow these steps:

1. LIAISON: If the release includes any completed blueprints, go to
   launchpad and create a ``next-$SERIES`` milestone as part of the
   ``$SERIES`` release. Set the targets for the blueprints to
   ``next-$SERIES`` and mark them as implemented. If there are no
   blueprints, this step can be skipped.

2. LIAISON: If this is a stable release and there are bugs to be
   reported as fixed, create a ``next-$SERIES`` milestone as part of
   the ``$SERIES`` release and target the bugs to the milestone. Set
   their status to ``Fix Committed``. If the release is from the
   ``master`` branch, this step can be skipped.

3. RELEASE TEAM: The release team member taking responsibility for the
   release should approve the change in
   ``openstack/releases``. Release requests should not be approved
   until we are actually ready to cut the release.

4. RELEASE TEAM: After the release request merges, check out or update
   a local copy of ``openstack/releases`` to get the new version of
   the deliverable file.

5. RELEASE TEAM: In a local copy of this
   ``openstack-infra/release-tools`` repository, run
   ``release_from_yaml.py``, giving the path to the deliverable file
   and the version from that file that needs to be released as
   arguments.

   For example::

      $ ./release_from_yaml.py ~/repos/openstack/releases/deliverables/liberty/openstack-doc-tools.yaml 0.30.1

6. RELEASE TEAM: As the release script runs, it reports on the
   existing tags in the branch being released and offers a last chance
   to review the new tag in light of the history. Press ``<return>``
   when ready to continue, then enter the pass phrase for your GPG key
   to add the tag.

7. RELEASE TEAM: After the tag is created locally and pushed up to the
   remote server, the script generates a release announcement email
   with some basic change information. It prints the results to the
   console, and saves a copy in ``relnotes/$project-$version``. The
   file is a fully formatted email, ready to be processed with a tool
   like ``msmtp``.

   If you use another mailer, copy the contents of the subject and
   body into the mail program, preserving the topic tags in the
   subject line, then send the message to
   ``openstack-announce@lists.openstack.org`` with the ``Reply-To``
   header set to ``openstack-dev@lists.openstack.org``.

8. RELEASE TEAM: After the release notes are written out, the script
   ensures that a launchpad milestone with the version number is
   created. If there is a ``next-$SERIES`` milestone, it is renamed
   and used. For releases from ``master``, all closed bugs are
   targeted to the new milestone. For stable branches, bugs should be
   targeted explicitly (see step 2).
