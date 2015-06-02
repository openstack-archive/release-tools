#!/usr/bin/env python
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

"""Generates a standard set of release notes for a repository."""

import argparse
import glob
import os
import random
import subprocess
import sys

import jinja2
from oslo_concurrency import processutils
import parawrap


EMOTIONS = [
    'amped',
    'chuffed',
    'content',
    'delighted',
    'eager',
    'excited',
    'glad',
    'gleeful',
    'happy',
    'jazzed',
    'jubilant',
    'overjoyed',
    'pleased',
    'psyched',
    'pumped',
    'satisfied',
    'stoked',
    'thrilled',
    'tickled pink',
]

# The email headers for generating a message to go right into sendmail
# or msmtp.
EMAIL_HEADER_TPL = """
{%- if email %}
From: {{email_from}}
To: {{email_to}}
Subject: [release]{% if stable_series %}[stable]{% endif %}{{email_tags}} {{project}} release {{end_rev}} {% if series %}({{series}}){% endif %}
{% endif %}
"""

# This will be replaced with template values and then wrapped using parawrap
# to correctly wrap at paragraph boundaries...

HEADER_RELEASE_TPL = """
We are {{ emotion }} to announce the release of:

{{ project }} {{ end_rev }}: {{ description }}

{% if series -%}
This release is part of the {{series}} {% if stable_series %}stable {% endif %}release series.
{%- endif %}
{% if source_url %}

With source available at:

    {{ source_url }}
{% endif %}
{% if milestone_url %}
For more details, please see the git log history below and:

    {{ milestone_url }}
{% else %}
For more details, please see the git log history below.
{% endif %}

{% if bug_url %}
Please report issues through launchpad:

    {{ bug_url }}
{% endif %}
"""

# This will just be replaced with template values (no wrapping applied).
CHANGE_RELEASE_TPL = """{% if notables %}
Notable changes
----------------

{{ notables }}
{% endif %}
{{ change_header }}{% if skip_requirement_merges %}

NOTE: Skipping requirement commits...
{%- endif %}

{% for change in changes -%}
{{ change }}
{% endfor %}
Diffstat (except docs and test files)
-------------------------------------

{% for change in diff_stats -%}
{{ change }}
{% endfor %}
{% if requirement_changes %}
Requirements updates
--------------------

{% for change in requirement_changes -%}
{{ change }}
{% endfor %}
{% endif %}
"""

CHANGES_ONLY_TPL = """{{ change_header }}
{% for change in changes -%}
{{ change }}
{% endfor %}
"""


def parse_readme(library_path):
    sections = {
        'bug_url': '',
        'source_url': '',
    }
    readme_path = os.path.join(library_path, 'README.rst')
    with open(readme_path, 'r') as fh:
        for line in fh:
            for (name, key_name) in [("Bugs:", "bug_url"),
                                     ("Source:", 'source_url')]:
                pieces = line.split(name, 1)
                if len(pieces) == 2:
                    sections[key_name] = pieces[1].strip()
    for (k, v) in sections.items():
        if not v:
            what = k.replace("_", " ")
            sys.stderr.write("WARNING: No %s found in '%s'\n"
                             % (what, readme_path))
    return sections


def expand_template(contents, params):
    if not params:
        params = {}
    tpl = jinja2.Template(source=contents, undefined=jinja2.StrictUndefined)
    return tpl.render(**params)


def run_cmd(cmd, cwd=None):
    # Created since currently the 'processutils' function doesn't take a
    # working directory, which we need in this example due to the different
    # working directories we run programs in...
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=cwd)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise processutils.ProcessExecutionError(stdout=stdout,
                                                 stderr=stderr,
                                                 exit_code=p.returncode,
                                                 cmd=cmd)
    return stdout, stderr


def is_skippable_commit(args, line):
    return (args.skip_requirement_merges and
            line.lower().endswith('updated from global requirements'))


def main():
    parser = argparse.ArgumentParser(
        prog='release_notes',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("library", metavar='path', action="store",
                        help="library directory, for example"
                             " 'openstack/cliff'",
                        )
    parser.add_argument("start_revision", metavar='revision',
                        action="store",
                        help="start revision, for example '1.8.0'",
                        )
    parser.add_argument("end_revision", metavar='revision',
                        action="store",
                        nargs='?',
                        help="end revision, for example '1.9.0'"
                             " (default: HEAD)",
                        default="HEAD")
    parser.add_argument('--changes-only',
                        action='store_true',
                        default=False,
                        help='List only the change summary, without details',
                        )
    parser.add_argument("--notable-changes", metavar='path',
                        action="store",
                        help="a file containing any notable changes")
    parser.add_argument("--skip-requirement-merges",
                        action='store_true', default=False,
                        help="skip requirement update commit messages"
                             " (default: False)")
    parser.add_argument("--show-dates",
                        action='store_true', default=False,
                        help="show dates in the change log")
    parser.add_argument("--series", "-s",
                        default="",
                        help="release series name, such as 'kilo'",
                        )
    parser.add_argument("--stable",
                        default=False,
                        help="this is a stable release",
                        )

    email_group = parser.add_argument_group('email settings')
    email_group.add_argument(
        "--email", "-e",
        action='store_true', default=False,
        help="output a fully formed email message",
    )
    email_group.add_argument(
        "--email-to",
        default="openstack-dev@lists.openstack.org",
        help="recipient of the email, defaults to %(default)s",
    )
    email_group.add_argument(
        "--email-from", "--from",
        default=os.environ.get('EMAIL', ''),
        help="source of the email, defaults to $EMAIL",
    )
    email_group.add_argument(
        "--email-tags",
        default="",
        help="extra topic tags for email subject, e.g. '[oslo]'",
    )
    args = parser.parse_args()

    library_path = os.path.abspath(args.library)
    if not os.path.isfile(os.path.join(library_path, "setup.py")):
        sys.stderr.write("No 'setup.py' file found in %s\n" % library_path)
        sys.stderr.write("This will not end well...\n")
        return 1

    # Get the python library/program description...
    cmd = [sys.executable, 'setup.py', '--description']
    stdout, stderr = run_cmd(cmd, cwd=library_path)
    description = stdout.strip()

    # Get the python library/program name
    cmd = [sys.executable, 'setup.py', '--name']
    stdout, stderr = run_cmd(cmd, cwd=library_path)
    library_name = stdout.strip()

    # Get the commits that are in the desired range...
    git_range = "%s..%s" % (args.start_revision, args.end_revision)
    if args.show_dates:
        format = "--format=%h %ci %s"
    else:
        format = "--oneline"
    cmd = ["git", "log", "--no-color", format, "--no-merges", git_range]
    stdout, stderr = run_cmd(cmd, cwd=library_path)
    changes = []
    for commit_line in stdout.splitlines():
        commit_line = commit_line.strip()
        if not commit_line or is_skippable_commit(args, commit_line):
            continue
        else:
            changes.append(commit_line)

    # Filter out any requirement file changes...
    requirement_changes = []
    requirement_files = list(glob.glob(os.path.join(library_path,
                                                    '*requirements*.txt')))
    if requirement_files:
        cmd = ['git', 'diff', '-U0', '--no-color', git_range]
        cmd.extend(requirement_files)
        stdout, stderr = run_cmd(cmd, cwd=library_path)
        requirement_changes = [line.strip()
                               for line in stdout.splitlines() if line.strip()]

    # Get statistics about the range given...
    cmd = ['git', 'diff', '--stat', '--no-color', git_range]
    stdout, stderr = run_cmd(cmd, cwd=library_path)
    diff_stats = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or line.find("tests") != -1 or line.startswith("doc"):
            continue
        diff_stats.append(line)

    notables = ''
    if args.notable_changes:
        with open(args.notable_changes, 'r') as fh:
            notables = fh.read().rstrip()

    # Extract + valdiate needed sections from readme...
    readme_sections = parse_readme(library_path)
    bug_url = readme_sections['bug_url']
    if bug_url:
        lp_url = bug_url.replace("bugs.", "").rstrip("/")
        milestone_url = lp_url + "/+milestone/%s" % args.end_revision
    else:
        lp_url = ''
        milestone_url = ''
    change_header = ["Changes in %s %s" % (library_name, git_range)]
    change_header.append("-" * len(change_header[0]))

    params = dict(readme_sections)
    params.update({
        'project': os.path.basename(library_path),
        'description': description,
        'end_rev': args.end_revision,
        'range': git_range,
        'lib': library_path,
        'milestone_url': milestone_url,
        'skip_requirement_merges': args.skip_requirement_merges,
        'changes': changes,
        'requirement_changes': requirement_changes,
        'diff_stats': diff_stats,
        'notables': notables,
        'change_header': "\n".join(change_header),
        'emotion': random.choice(EMOTIONS),
        'stable_series': args.stable,
        'series': args.series,
        'email': args.email,
        'email_from': args.email_from,
        'email_to': args.email_to,
        'email_tags': args.email_tags,
    })
    if args.changes_only:
        print(expand_template(CHANGES_ONLY_TPL, params))
    else:
        if args.email:
            email_header = expand_template(EMAIL_HEADER_TPL.strip(), params)
            print(email_header.lstrip())
        header = expand_template(HEADER_RELEASE_TPL.strip(), params)
        print(parawrap.fill(header))
        print(expand_template(CHANGE_RELEASE_TPL, params))
    return 0


if __name__ == '__main__':
    sys.exit(main())
