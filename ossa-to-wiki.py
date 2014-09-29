"""
ossa-to-wiki.py FROM-DATE TO-DATE

Extract OSSAs from openstack-announce archive
and output in wiki format for stable point releases at
https://wiki.openstack.org/wiki/ReleaseNotes/2014.1.2
and
https://wiki.openstack.org/wiki/SecurityAdvisories/Icehouse
"""

import datetime
import email.utils
import gzip
import iso8601
import locale
import mailbox
import os
import re
import requests
import sys
import tempfile
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
from six import StringIO

session = CacheControl(requests.Session(), cache=FileCache('.ossa_cache'))

mbox_url_template = "http://lists.openstack.org/pipermail/openstack-announce/%s.txt"
date_url_template = "http://lists.openstack.org/pipermail/openstack-announce/%s/date.html"
ossa_url_template = "http://lists.openstack.org/pipermail/openstack-announce/%s/%s"
ossa_pattern = re.compile('HREF="(.*)">.*\[OSSA (.*)\]')

def parse_ossa(message, ossa2announce):
    """Returns a map with OSSA details extracted from openstack-announce
       message."""

    patterns = { field: re.compile(field + ': (.*)$') for field in (
        'OpenStack Security Advisory',
        'CVE',
        'Date',
        'Title',
        'Reporters',
        'Products',
        'Versions',
    ) }
    patterns_ml = { field: re.compile(field + ':$') for field in (
        'Description',
        'Icehouse fix',
        'Havana fix',
        'Notes',
        'References',
    ) }
    ossa = {}
    ml = None
    for line in message.splitlines():
      if ml:
        if len(line)>1:
          ossa[ml].append(line)
        else:
          ml = None
          continue
      for field, pattern in patterns.iteritems():
        m = pattern.match(line)
        if m:
          ossa[field] = m.group(1)
          del patterns[field]
          break
      for field, pattern in patterns_ml.iteritems():
        m = pattern.match(line)
        if m:
          ml=field
          ossa[ml] = []
          del patterns_ml[field]
          break
    if ossa2announce:
        ossa['announce'] = ossa2announce[ossa['OpenStack Security Advisory']]
    return ossa

def get_openstack_announce(date):
    """Returns openstack-announce mbox archive and mapping OSSA to
       announce message for the month specified by @date."""
    # FIXME this is all wrong, OSSAs should be stored in a db
    # or at least in git repo like OSSNs:
    # https://github.com/openstack/security-doc/tree/master/security-notes
    locale.setlocale(locale.LC_ALL, 'en_US')
    year_month = date.strftime("%Y-%B")
    mbox_url = mbox_url_template % year_month
    date_url = date_url_template % year_month
    print "processing %s" % year_month,
    req = session.get(mbox_url)
    if req.status_code == 200:
        print '.',
        (fd, mbox_name) = tempfile.mkstemp(prefix='openstack-announce-')
        f = os.fdopen(fd,'wb')
        print '.',
        f.write(req.content)
        f.close()
        print '.',
        req = session.get(date_url)
        if req.status_code == 200:
            print '.',
            # OSSA -> openstack-announce message URL mapping
            ossa2announce = {}
            for ref in ossa_pattern.finditer(req.text):
                ossa2announce[ref.group(2)] = ossa_url_template % (
                                                  year_month,
                                                  ref.group(1))
            return mbox_name, ossa2announce
        else:
            return mbox_name, None
    else:
        return None, None

def next_month(date):
    year = date.year
    month = date.month + 1
    if month == 13:
        month = 1
        year = year + 1
    return date.replace(year=year, month=month)

def usage():
    print "usage: ossa-to-wiki.py FROM-DATE TO-DATE"
    sys.exit(1)

if len(sys.argv) < 3:
    usage()

from_date = iso8601.parse_date(sys.argv[1]).date()
to_date = iso8601.parse_date(sys.argv[2]).date()
if from_date > to_date:
    usage()

archive = from_date.replace(day=1)
ossas=[]
while archive <= to_date:
    mbox_name, ossa2announce = get_openstack_announce(archive)
    if mbox_name:
        mbox = mailbox.mbox(mbox_name, create=False)
        for msg in mbox:
            subject = msg['subject']
            if subject.find('OSSA') >= 0:
                year, month, day = email.utils.parsedate(msg['date'])[0:3]
                date = datetime.date(year, month, day)
                if date >= from_date and date <= to_date:
                    if msg.get_content_type() == 'text/plain':
                        ossas.append(parse_ossa(msg.get_payload(),
                                                ossa2announce))
        os.unlink(mbox_name)
    archive = next_month(archive)
# TODO query gerrit review status, git tag --contains for each branch

# DEBUG
#print ossas
# 'Date': 'June 12, 2014', 'References': ['http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2014-3476', 'https://launchpad.net/bugs/1324592'], 'CVE': 'CVE-2014-3476', 'OpenStack Security Advisory': '2014-018', 'Notes': ['This fix will be included in the Juno-2 development milestone and in', 'future 2013.2.4 and 2014.1.2 releases.']}, {'Description': ['Thiago Martins from Hewlett Packard reported a vulnerability in Neutron', 'L3-agent. By creating an IPv6 private subnet attached to a L3 router, an', 'authenticated user may break the L3-agent, preventing further floating', 'IPv4 addresses from being attached for the entire cloud. Note: removal', 'of the faulty network can not be done using the API and must be cleaned', 'at the database level. Only Neutron setups using IPv6 and L3-agent are', 'affected.'], 'Versions': 'up to 2013.2.3, and 2014.1', 'Havana fix': ['https://review.openstack.org/95939'], 'Title': 'Neutron L3-agent DoS through IPv6 subnet', 'Products': 'Neutron', 'Icehouse fix': ['https://review.openstack.org/95938'], 'announce': u'http://lists.openstack.org/pipermail/openstack-announce/2014-June/000242.html',

# ReleaseNotes OSSA wiki format example:
# * [http://lists.openstack.org/pipermail/openstack-announce/2014-July/000248.html OSSA 2014-022] / [https://launchpad.net/bugs/1331912 CVE-2014-3520] - Keystone V2 trusts privilege escalation through user supplied project id
for ossa in ossas:
   ossa['LPbug'] = ossa['References'][1]
   print "* [%(announce)s OSSA %(OpenStack Security Advisory)s] / [%(LPbug)s %(CVE)s] - %(Title)s" % ossa


# TODO dump format for SecurityAdvisories wiki:
#| Product
#| Date
#| Openstack Security Advisory
#| CVE Number
#| Title
#| Impact
#|-
#| Neutron
#| April 22, 2014
#| [http://lists.openstack.org/pipermail/openstack-announce/2014-April/000227.html 2014-014]
#| [https://launchpad.net/bugs/1300785 2014-0187]
#| Neutron security groups bypass through invalid CIDR
#|
