#!/usr/bin/python
#-*- coding: utf-8 -*-
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-i", "--sid", dest="sid")
(options, args) = parser.parse_args()

import MySQLdb
db = MySQLdb.connect(user='root',passwd='',db='site',use_unicode=True)
cursor = db.cursor()
a = cursor.execute('select id from django_openid_auth_useropenid where claimed_id = "http://steamcommunity.com/openid/id/' + options.sid + '"')
if a:
	site_id = cursor.fetchone()
	cursor.execute('select nickname from mongobase_userprofile where id = "' + str(site_id[0]) + '"')
	print (cursor.fetchone()[0]).encode("ascii","ignore")
else:
	print 0
