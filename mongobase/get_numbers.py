import urllib2, re, json, time
from hatsdb import settings
#-----------------get_tratata---------------

def get_friends(steam_id):
	user_friends_url = "http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key=" + settings.API_KEY + "&relationship=all&steamid=" + str(steam_id)
	try:
		data = urllib2.urlopen(user_friends_url).read()
	except Exception,e:
		return None 			#probably network error
	else:
		real_friends = []
		friends = json.loads(data)
		if friends.has_key("friendslist"):
			for f in friends["friendslist"]["friends"]:
				real_friends.append(f["steamid"])
			return real_friends
		else:
			return 2 		#no friends ;;

def return_int(s):
	s = str(s)
	s = s.strip(' ')
	if s != '':
		try:
			result = int(s)
		except Exception, e:  
			result = -1
	else:
		result = None

	return result
#-------------------------------------
