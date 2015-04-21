#!/bin/bash
#
# Generate the release notes email bodies for one or more project.
#

bindir=$(cd $(dirname $0) && pwd)

function get_release_range () {
    git log --decorate --oneline \
        | egrep '^[0-9a-f]+ \((HEAD, )?tag: ' \
        | sed -E 's/^.+tag: ([^ ]+)[,\)].+$/\1/g' \
        | head -n 2 \
        | sort -n
}

PROJECTS="$@"
if [[ $# -eq 0 ]]
then
    echo "Usage: make_release_notes_emails.sh ../cliff ../python-barbicanclient ..."
    exit 1
fi

# FIXME(dhellmann): We need a way to not hard-code these values.
FROM="Doug Hellmann <doug@doughellmann.com>"
TO="openstack-dev@lists.openstack.org"
SERIES=liberty

OUTROOT="relnote-emails"
mkdir -p $OUTROOT

for projdir in $PROJECTS
do
    proj=$(basename $projdir)
    echo $proj
    range=$(cd $projdir && get_release_range)
    ver=$(echo $range | sed -E 's/.+ //')
    outfile="$OUTROOT/${proj}-${ver}-release-notes.txt"
    echo "From: $FROM
To: $TO
Subject: [release] $proj release $ver ($SERIES)

" > $outfile
    $bindir/release_notes.py --show-dates $projdir $range >> $outfile
done
