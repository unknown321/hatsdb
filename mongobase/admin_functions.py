# -*- coding: utf-8 -*-
import urllib2, json, time
from datetime import datetime
from models import *
from views import is_logged

def find_user(request, steam_id):
	user_profile = userProfile.objects.filter(steamid=steam_id)
	if user_profile.count() > 0:
		user_profile = user_profile[0]
	return user_profile

def save_user(request, steam_id, tf2_sub, dota2_sub, csgo_sub, donator):
	our_user =  userProfile.objects.filter(steamid=steam_id)[0]
	our_user.premium_tf2 = tf2_sub
	our_user.premium_dota2 = dota2_sub
	our_user.premium_csgo = csgo_sub
	our_user.donator = donator
	our_user.save()
	return 0

def gather_stats(game_type='tf2'):
	from connect import HatsdbClient
	client = HatsdbClient()
	connected = client.connect(game_type=game_type)
	results = {}
	if connected:
		stats = client.client[game_type].command('dbStats')
		results['items'] = stats['objects']
		results['unusuals'] = client.client[game_type].command('collstats','unusuals')['count']
		if game_type == 'tf2':
			results['earbuds'] = client.client[game_type].command('collstats','143')['count']
			results['bills'] = client.client[game_type].command('collstats','126')['count']
			results['australiums'] = 0
			aussies = list(def_item.objects.filter(game_type='tf2',name__startswith='Australium').exclude(name='Australium Gold').order_by('name'))
			for a in aussies:
				results['australiums'] += client.client[game_type].command('collstats',str(a.defindex))['count']
			results['subscribers'] = userProfile.objects.filter(premium_tf2=True).count()
		elif game_type == 'dota2':
			results['timebreakers'] = client.client[game_type].command('collstats','4264')['count']
			results['hooks'] = client.client[game_type].command('collstats','4007')['count']
			results['tournament'] = client.client[game_type].command('collstats','tournament')['count']
			results['subscribers'] = userProfile.objects.filter(premium_dota2=True).count()
		elif game_type == 'csgo':
			results['tournament'] = client.client[game_type].command('collstats','tournament')['count']
			results['subscribers'] = userProfile.objects.filter(premium_csgo=True).count()
		client.disconnect()
	return results

def save_stats():
	stats = {}
	stats['tf2'] = gather_stats('tf2')
	stats['dota2'] = gather_stats('dota2')
	stats['csgo'] = gather_stats('csgo')

	s = real_stats()
	s.tf2_items = stats['tf2']['items']
	s.tf2_unusuals = stats['tf2']['unusuals']
	s.tf2_earbuds = stats['tf2']['earbuds']
	s.tf2_bills = stats['tf2']['bills']
	s.tf2_australiums = stats['tf2']['australiums']
	s.tf2_subscribers = stats['tf2']['subscribers']

	s.dota2_items = stats['dota2']['items']
	s.dota2_unusuals = stats['dota2']['unusuals']
	s.dota2_timebreakers = stats['dota2']['timebreakers']
	s.dota2_tournament = stats['dota2']['tournament']
	s.dota2_hooks = stats['dota2']['hooks']
	s.dota2_subscribers = stats['dota2']['subscribers']

	s.csgo_items = stats['csgo']['items']
	s.csgo_knives = stats['csgo']['unusuals']
	s.csgo_tournament = stats['csgo']['tournament']
	s.csgo_subscribers = stats['csgo']['subscribers']

	s.users = userProfile.objects.count()
	s.save()


# mapreduce by quality
def gather_item_stats(game_type):
	if game_type == 'csgo':
		key = 'exterior'
	else:
		key = 'quality'
	map = "function(){ emit(this." + key + ", {count: 1}); }"
	reduce =  "function(key, values) { total = 0; for (var i = 0; i < values.length; ++i) { total += values[i].count; }; return {count: total}; }"
	from connect import HatsdbClient
	client = HatsdbClient()
	connected = client.connect(game_type=game_type)
	if connected:
		collections = client.client[game_type].collection_names()
		database = client.client[game_type]
		collections.remove('unusuals')
		collections.remove('system.indexes')
		if 'system.users' in collections:
			collections.remove('system.users')
		if game_type != 'tf2':
			collections.remove('tournament')
		for c in collections:
			item_stats.objects.filter(defindex=int(c), game_type=game_type).delete()
			result = database[c].inline_map_reduce(map,reduce)
			overall = database[c].count()
			for r in result:
				if r["_id"] is not None:
					s = item_stats()
					s.defindex = int(c)
					s.quality = int(r["_id"])
					s.count = int(r["value"]["count"])
					s.game_type = game_type
					s.overall = overall

					n = def_item.objects.filter(defindex=int(c), game_type=game_type)
					if n.count > 0:
						name = n[0].name
						name = def_item.objects.get(defindex=int(c), game_type=game_type).name
						if game_type == 'csgo':
							ex_name = exterior.objects.get(defindex=int(r["_id"])).name
							full_name = name + ' (' + ex_name + ')'
						else:
							quality_name = quality.objects.get(defindex=int(r["_id"]), game_type=game_type).name
							if quality_name in settings.HIDDEN_QUALS[game_type]:
								full_name = name
							else:
								full_name = quality_name + ' ' + name
					
						price = get_market_price(full_name, game_type)
						if price.has_key('lowest_price'):
							s.price = float(price['lowest_price'].lstrip('&#36;'))
						else:
							if price.has_key('median_price'):
								s.price = float(price['median_price'].lstrip('&#36;'))
						print c, full_name, s.price
					else:
						pass
					s.save()
	return 0


def get_market_price(name, game_type):
	import json
	result = {}
	name = name.replace(' ', '+')
	url = "http://steamcommunity.com/market/priceoverview/?country=US&currency=0&appid="\
							+ str(settings.APPS[game_type]) + "&market_hash_name=" + name
	try:

		data = urllib2.urlopen(url.encode('utf-8')).read()
	except urllib2.URLError, e:
		print e
	else:
		result = json.loads(data)
	time.sleep(1)
	return result