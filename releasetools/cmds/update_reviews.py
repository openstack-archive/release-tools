# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys
import warnings

from releasetools import update_reviews


def updating_review_cb(r):
    print('Updating %s in %s' % (r['change_id'], r['project']))


def main():

    # Get urllib3 to shut up.
    warnings.simplefilter('ignore', Warning)

    project = sys.argv[1]
    u_r = update_reviews.UpdateReviews(project,
                                       updating_review_cb=updating_review_cb)
    u_r.update_my_reviews()
