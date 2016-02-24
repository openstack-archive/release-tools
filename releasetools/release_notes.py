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

from __future__ import unicode_literals

import glob
import os
import random
import subprocess
import sys

import jinja2
from oslo_concurrency import processutils
import parawrap
from reno import defaults as reno_defaults
from reno import formatter
from reno import scanner

from releasetools import rst2txt


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
Reply-To: {{email_reply_to}}
Subject: [release]{% if stable_series %}[stable]{% endif %}{{email_tags}} {{project}} {{end_rev}} release{% if series %} ({{series}}){% endif %}
{% endif %}
"""

PYPI_URL_TPL = 'https://pypi.python.org/pypi/%s'

# This will be replaced with template values and then wrapped using parawrap
# to correctly wrap at paragraph boundaries...

HEADER_RELEASE_TPL = """
We are {{ emotion }} to announce the release of:

{{ project }} {{ end_rev }}: {{ description }}

{% if first_release -%}
This is the first release of {{project}}.
{%- endif %}
{% if series -%}
This release is part of the {{series}} {% if stable_series %}stable {% endif %}release series.
{%- endif %}
{% if source_url %}

With source available at:

    {{ source_url }}
{% endif %}
{% if pypi_url %}

With package available at:

    {{ pypi_url }}
{% endif %}
{% if bug_url %}

Please report issues through launchpad:

    {{ bug_url }}
{% endif %}

For more details, please see below.
"""

# This will just be replaced with template values (no wrapping applied).
CHANGE_RELEASE_TPL = """{% if reno_notes %}{{ reno_notes }}{% endif %}
{{ change_header }}{% if skip_requirement_merges %}

NOTE: Skipping requirement commits...
{%- endif %}

{% for change in changes -%}
{{ change }}
{% endfor %}
{% if not first_release -%}
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
{%- endif %}
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
                    candidate = pieces[1].strip()
                    if 'http' in candidate:
                        sections[key_name] = candidate
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


def run_cmd(cmd, cwd=None, encoding='utf-8'):
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
    return stdout.decode(encoding), stderr.decode(encoding)


def is_skippable_commit(skip_requirement_merges, line):
    return (skip_requirement_merges and
            line.lower().endswith('updated from global requirements'))


def generate_release_notes(library, library_path,
                           start_revision, end_revision,
                           show_dates, skip_requirement_merges,
                           is_stable, series,
                           email, email_from,
                           email_to, email_reply_to, email_tags,
                           include_pypi_link,
                           changes_only,
                           first_release,
                           ):
    """Return the text of the release notes.

    :param library: The name of the library.
    :param library_path: Path to the library repository on disk.
    :param start_revision: First reference for finding change log.
    :param end_revision: Final reference for finding change log.
    :param show_dates: Boolean indicating whether or not to show dates
        in the output.
    :param skip_requirement_merges: Boolean indicating whether to
        skip merge commits for requirements changes.
    :param is_stable: Boolean indicating whether this is a stable
        series or not.
    :param series: String holding the name of the series.
    :param email: Boolean indicating whether the output format should
        be an email message.
    :param email_from: String containing the sender email address.
    :param email_to: String containing the email recipient.
    :param email_reply_to: String containing the email reply-to address.
    :param email_tags: String containing the email header topic tags to add.
    :param include_pypi_link: Boolean indicating whether or not to
        include an automatically generated link to the PyPI package
        page.
    :param changes_only: Boolean indicating whether to limit output to
        the list of changes, without any extra data.
    :param first_release: Boolean indicating whether this is the first
        release of the project

    """

    # Do not mention the series in independent model since there is none
    if series == 'independent':
        series = ''

    if not os.path.isfile(os.path.join(library_path, "setup.py")):
        raise RuntimeError("No 'setup.py' file found in %s\n" % library_path)

    if not email_from:
        raise RuntimeError('No email-from specified')

    # Get the python library/program description...
    cmd = [sys.executable, 'setup.py', '--description']
    stdout, stderr = run_cmd(cmd, cwd=library_path)
    description = stdout.strip()

    # Get the python library/program name
    cmd = [sys.executable, 'setup.py', '--name']
    stdout, stderr = run_cmd(cmd, cwd=library_path)
    library_name = stdout.strip()

    # Get the commits that are in the desired range...
    git_range = "%s..%s" % (start_revision, end_revision)
    if show_dates:
        format = "--format=%h %ci %s"
    else:
        format = "--oneline"
    cmd = ["git", "log", "--no-color", format, "--no-merges", git_range]
    stdout, stderr = run_cmd(cmd, cwd=library_path)
    changes = []
    for commit_line in stdout.splitlines():
        commit_line = commit_line.strip()
        if not commit_line or is_skippable_commit(skip_requirement_merges,
                                                  commit_line):
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

    # Extract + valdiate needed sections from readme...
    readme_sections = parse_readme(library_path)
    change_header = ["Changes in %s %s" % (library_name, git_range)]
    change_header.append("-" * len(change_header[0]))

    # Look for reno notes for this version.
    branch = None
    if is_stable and series:
        branch = 'origin/stable/%s' % series
    scanner_output = scanner.get_notes_by_version(
        reporoot=library_path,
        notesdir='%s/%s' % (reno_defaults.RELEASE_NOTES_SUBDIR,
                            reno_defaults.NOTES_SUBDIR),
        branch=branch,
    )
    if end_revision in scanner_output:
        rst_notes = formatter.format_report(
            reporoot=library_path,
            scanner_output=scanner_output,
            versions_to_include=[end_revision],
        )
        reno_notes = rst2txt.convert(rst_notes)
    else:
        reno_notes = ''

    params = dict(readme_sections)
    params.update({
        'project': library_name,
        'description': description,
        'end_rev': end_revision,
        'range': git_range,
        'lib': library_path,
        'skip_requirement_merges': skip_requirement_merges,
        'changes': changes,
        'requirement_changes': requirement_changes,
        'diff_stats': diff_stats,
        'change_header': "\n".join(change_header),
        'emotion': random.choice(EMOTIONS),
        'stable_series': is_stable,
        'series': series,
        'email': email,
        'email_from': email_from,
        'email_to': email_to,
        'email_reply_to': email_reply_to,
        'email_tags': email_tags,
        'reno_notes': reno_notes,
        'first_release': first_release,
    })
    if include_pypi_link:
        params['pypi_url'] = PYPI_URL_TPL % library_name
    else:
        params['pypi_url'] = None

    response = []
    if changes_only:
        response.append(expand_template(CHANGES_ONLY_TPL, params))
    else:
        if email:
            email_header = expand_template(EMAIL_HEADER_TPL.strip(), params)
            response.append(email_header.lstrip())
        header = expand_template(HEADER_RELEASE_TPL.strip(), params)
        response.append(parawrap.fill(header))
        response.append(expand_template(CHANGE_RELEASE_TPL, params))
    return '\n'.join(response)
