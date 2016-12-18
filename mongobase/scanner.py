# -*- coding: utf-8 -*-
import json, urllib2, re
from hatsdb import settings
from models import *
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)
broken_hours_logger = logging.getLogger('broken_hours')

def scan_wrapper(steam_id, game_type, marketable, uncraft, untrade, blacklist):
	logger.info('Scanning ' + str(steam_id) + '\t' + game_type)
	result = scan_player(steam_id, game_type, marketable, uncraft, untrade, blacklist)
	return result

#-----------utility--------------

#rewrite
def get_player_info(steam_id):
	player_info = {}
	user_info_url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key="\
					 + settings.API_KEY + "&steamids=" + str(steam_id)
	i = 0
	while True:
		try:
			userdata = urllib2.urlopen(user_info_url, timeout=5).read()
		except Exception, e:
			import time
			time.sleep(0.15)
			if i < 3:
				i+=1
			else:
				break
		else:
			try:
				raw_data = json.loads(userdata)
			except Exception, e:
				break
			else:
				break
	if raw_data.has_key('response'):
		if raw_data['response'].has_key('players'):
			if len(raw_data['response']['players']) > 0:
				player_info['avatar'] = raw_data['response']["players"][0]["avatar"]
				player_info['nickname'] = raw_data['response']["players"][0]["personaname"]
				player_info['profileurl'] = raw_data['response']["players"][0]["profileurl"]
				player_info['id'] = str(steam_id)
	return player_info

#done, should be working
def download_items(profileurl, game_type):
	game_id = get_id_by_game_type(game_type)
	url_string = profileurl + "inventory/json/" + str(game_id) + "/2?l=en"
	json_data = None
	raw_data = None
	try:
		raw_data = urllib2.urlopen(url_string, timeout=15).read()
	except Exception, e:
		logger.info('Exception while downloading items for ' + str(profileurl) + ' ' + str(e))
	else:
		try:
			json_data = json.loads(raw_data) 
		except Exception, e:
			logger.info('Cannot download items for ' + str(profileurl) + ' ' + str(e))
		else:
			pass
	return json_data

#done, should be working
def download_items_legacy(steam_id, game_type):
	api_part = get_api_part(game_type)
	url_string = "http://api.steampowered.com/" + api_part + "/GetPlayerItems/v0001/?language=en&key=" + settings.API_KEY + "&steamid=" + str(steam_id)
	json_data = None
	raw_data = None
	try:
		raw_data = urllib2.urlopen(url_string, timeout=5).read()
	except Exception, e:
		logger.info('Cannot download legacy items for ' + str(steam_id) + ' ' + str(e))
		return None
	else:
		try:
			json_data = json.loads(raw_data) 
		except Exception, e:
			return None
		else:
			pass
	return json_data

#done, should be working, ALSO USELESS
def is_f2p(num_backpack_slots, game_type):
	f2p = False
	if game_type == 'tf2':
		if num_backpack_slots < 300:
			f2p = True

#done, should be working
def get_player_hours(steam_id):
	link = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key='+ settings.API_KEY +'&include_played_free_games=1&steamid=' + steam_id
	hours = dict.fromkeys(settings.APPID_LIST, -1)		#tf2, dota2, csgo
	try:
		time_data = urllib2.urlopen(link, timeout=5).read()
	except Exception, e:
		return hours
	else:
		try:
			time_data = json.loads(time_data)
		except Exception, e:
			pass
		else:
			if time_data.has_key('response'):
				if time_data['response'].has_key('games'):
					times = filter(lambda app: app['appid'] in settings.APPID_LIST, time_data['response']['games'])
					if len(times) > 0:
						for t in times:
							hours[t['appid']] = t['playtime_forever']/60
	return hours

#done, should be working
def get_id_by_game_type(game_type):
	id = 440
	if game_type == 'tf2':
		pass
	elif game_type == 'dota2':
		id = 570
	elif game_type == 'csgo':
		id = 730
	return id

#-----------scanner--------------

#
#	save owners separately
#	player = {"_id":id64, "tf2_hours":tf2_hours, "dota2_hours":dota2_hours, "is_f2p":scanned_player['F2P']}
#	item must get its owner during saving
#

#should be working
def scan_player(steam_id, game_type, marketable, uncraft, untrade, blacklist):
	scanned_player = {}
	items_json = None
	game_id = get_id_by_game_type(game_type)
	hours = get_player_hours(str(steam_id))
	scanned_player['info']  = get_player_info(str(steam_id))
	scanned_player['info']['all_hours']  = hours
	scanned_player['hours'] = hours[game_id]
	scanned_player['items'] = []
	if scanned_player['info'].has_key('profileurl'):
		items_json = download_items(scanned_player['info']['profileurl'], game_type)
	if not items_json:						#permission etc
		scanned_player['items'] = -1
	else:
		if not items_json.has_key('rgInventory'):
			scanned_player['items'] = {}
		else:
			unsorted_items = []
			for i in items_json['rgInventory']:
				itemid = items_json['rgInventory'][i]['classid'] + '_' + items_json['rgInventory'][i]['instanceid']
				item = items_json['rgDescriptions'][itemid]
				item['id'] = items_json['rgInventory'][i]['id']
				unsorted_items.append(item)
			scanned_player['items'] = unsorted_items
			from tasks import save_task
			a = save_task.apply_async((scanned_player, game_type),queue="q5", expires=121)
			scanned_player['items'] = sort_items(unsorted_items, game_type, marketable, uncraft, untrade, blacklist)
			if scanned_player['hours'] < 0:
				broken_hours_logger.info(str(steam_id) + '\t' + game_type)
	return scanned_player

#should be working
def sort_items(items, game_type, marketable, uncraft, untrade, blacklist):
	sorted_items = {}
	for item in items:
		if blacklist_check(item, blacklist):
			####### default rarity for csgo and dota
			item_rarity = 'Common'
			#######

			failed = False
			for desc in item['descriptions']:
				if 'Not Usable in Crafting )' in desc and uncraft:
					failed = True

			if item['marketable'] == 0 and marketable:
				failed = True
			if item['tradable'] == 0 and untrade:
				failed = True

			if not failed:
				for tag in item['tags']:
					if tag['category_name'] == settings.SORT_KEY[game_type]:
						item_rarity = tag['name']
						break

				if sorted_items.has_key(item_rarity):
					sorted_items[item_rarity].append(item)
				else:
					sorted_items[item_rarity] = []
					sorted_items[item_rarity].append(item)
		else:
			pass
			# logger.info('blacklisted ' + item['market_hash_name'])
	
	for item_rarity in sorted_items:
		sorted_items[item_rarity] = sorted(sorted_items[item_rarity], key=lambda k: k['market_hash_name'])

	return sorted_items

# works
def blacklist_check(item, blacklist):
	if item['market_hash_name'] in blacklist:
		return False
	else:
		return True

# deprecated with move to json
# NO IT IS NOT
def get_api_part(game_type):
	api_part = "IEconItems_440"
	if game_type == 'tf2':
		api_part = "IEconItems_440"
	elif game_type == "dota2":
		api_part = "IEconItems_570"
	elif game_type == "csgo":
		api_part = "IEconItems_730"
	return api_part