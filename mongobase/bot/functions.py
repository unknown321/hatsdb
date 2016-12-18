def get_prem_type(steamid):
	import MySQLdb
	db = MySQLdb.connect(user='root',passwd='',db='site',use_unicode=True)
	cursor = db.cursor()
	payment_type = 0
	a = cursor.execute('select pend_tf2, pend_dota2, pend_csgo, pend_donation from mongobase_pending_payment where id = "' + str(steamid) + '"')
	if a:
		selection = cursor.fetchone()
		if selection[0]:
			# tf2
			payment_type = 1
		elif selection[1]:
			# dota2
			payment_type = 2
		elif selection[2]:
			# csgo
			payment_type = 3
		elif selection[3]:
			# donation
			payment_type = 4
	return payment_type

def grant(steamid, donator=False):
	import MySQLdb
	db = MySQLdb.connect(user='root',passwd='',db='site',use_unicode=True)
	cursor = db.cursor()
	site_id = None
	a = cursor.execute('select id from mongobase_userprofile where steamid = ' + steamid)
	key = None
	if a:
		if donator:
			key = "donator"
		else:
			prem_type = get_prem_type(steamid)
			if prem_type == 1:
				key = 'premium_tf2'
			elif prem_type == 2:
				key = 'premium_dota2'
			elif prem_type == 3:
				key = 'premium_csgo'
			elif prem_type == 4:
				key = 'donator'
		if key:
			cursor.execute('update mongobase_userprofile set ' +key + ' = 1 where steamid = ' + steamid)
			db.commit()
			return 0
		else:
			return 2
	else:
		return 1