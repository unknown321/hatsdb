#!/usr/bin/python
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-i", "--sid", dest="sid")
parser.add_option("-d", "--donator", dest="donator", action='store_true')
(options, args) = parser.parse_args()

from functions import grant
print grant(options.sid, options.donator)