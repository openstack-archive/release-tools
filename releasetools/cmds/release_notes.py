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
import os

from releasetools import release_notes


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
    parser.add_argument('--include-pypi-link',
                        action='store_true',
                        default=False,
                        help='include a pypi hyperlink for the library',
                        )
    parser.add_argument('--first-release',
                        action='store_true',
                        default=False,
                        help='this is the first release of the project',
                        )
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
                        action='store_true',
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
        "--email-reply-to",
        default="openstack-dev@lists.openstack.org",
        help="follow-up for discussions, defaults to %(default)s",
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

    notes = release_notes.generate_release_notes(
        library=args.library,
        library_path=library_path,
        start_revision=args.start_revision,
        end_revision=args.end_revision,
        show_dates=args.show_dates,
        skip_requirement_merges=args.skip_requirement_merges,
        is_stable=args.stable,
        series=args.series,
        email=args.email,
        email_from=args.email_from,
        email_to=args.email_to,
        email_reply_to=args.email_reply_to,
        email_tags=args.email_tags,
        include_pypi_link=args.include_pypi_link,
        changes_only=args.changes_only,
        first_release=args.first_release,
    )
    print(notes.encode('utf-8'))
    return 0
