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


def try_int(val):
    try:
        return int(val)
    except ValueError:
        return val


def parse_version(v):
    parts = v.split('.')
    if len(parts) < 3:
        parts.append('0')
    return [try_int(p) for p in parts]


def format_version(v):
    return '.'.join(str(p) for p in v)


def sanity_check_version(new_version, existing_versions):
    warnings = []
    if not existing_versions:
        if new_version[0] != 0:
            warnings.append(
                'first version in repository does not start with 0'
            )
    if new_version in existing_versions:
        warnings.append(
            'version %r already exists in repository' %
            format_version(new_version)
        )
    same_minor = same_major = None
    for v in existing_versions:
        # Look for other numbers in the series
        if v[:2] == new_version[:2]:
            print('%r in same minor series as %r' %
                  (format_version(v), format_version(new_version)))
            if not same_minor or v > same_minor:
                same_minor = v
        if v[:1] == new_version[:1]:
            print('%r in same major series as %r' %
                  (format_version(v), format_version(new_version)))
            if not same_major or v > same_major:
                same_major = v
    if same_minor is not None:
        print('last version in minor series %r' %
              format_version(same_minor))
        expected = same_minor[2] + 1
        actual = new_version[2]
        if actual > expected:
            warnings.append(
                'new version %r increments patch version more than one over %r'
                % (format_version(new_version), format_version(same_minor))
            )
    if same_major is not None and same_major != same_minor:
        print('last version in major series %r' %
              format_version(same_major))
        if new_version > same_major:
            expected = same_major[1] + 1
            actual = new_version[1]
            if actual > expected:
                warnings.append(
                    ('new version %r increments minor '
                     'version more than one over %r') %
                    (format_version(new_version), format_version(same_major))
                )
            if new_version[2] != 0:
                warnings.append(
                    'new version %r increments minor version and patch version'
                    % format_version(new_version)
                )
    if existing_versions:
        latest_version = existing_versions[-1]
        if new_version[0] > latest_version[0]:
            warnings.append(
                '%r is a major version increment over %r' %
                (format_version(new_version), format_version(latest_version))
            )
    return warnings
