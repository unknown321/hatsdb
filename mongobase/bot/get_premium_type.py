#!/usr/bin/python
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-i", "--sid", dest="sid")
(options, args) = parser.parse_args()

from functions import get_prem_type
print get_prem_type(options.sid)