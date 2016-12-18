# -*- coding: utf-8 -*-
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from hatsdb import settings
from models import *
from random import randint
from scanner import *
from views import is_logged
import re, gc
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s')


#----------these functions prepare and send data for ajax etc (non-admin)------------------


# effect: {'$in':[1.2]}

#works
def convert_steam_id(steam_id):
	id64 = 0
	steamid_pattern1 = re.compile(settings.SID_PATTERN_OLD)
	steamid_pattern2 = re.compile(settings.SID_PATTERN_NEW)
	if steamid_pattern1.findall(steam_id) or steamid_pattern2.findall(steam_id):
		steam_id = steam_id.rsplit(":")
		if len(steam_id) == 3:
			if 'STEAM_' in steam_id[0]:
				try:
					id64 = int(settings.MAGIC_SID + int(steam_id[1]) + int(steam_id[2])*2)
				except Exception, ValueError:
					pass
			if steam_id[0] == 'U':
				try:
					id64 = int(settings.MAGIC_SID + int(steam_id[2]))
				except Exception, ValueError:
					pass
	else:
		id64 = steam_id
	return id64

#obsolete?
@csrf_protect
def scanner_results(request, steam_ids, marketable_check, uncraft_check, untrade_check, game_type):
	from celery.exceptions import SoftTimeLimitExceeded
	user, openid_user, user_details = is_logged(request)
	TIMED_OUT = 0

	if user.is_authenticated():
		startTime = datetime.now()

		blacklist = get_blacklist(user_details, game_type)
		USER_LIMIT = get_user_limit(user_details, game_type)

		if game_type not in settings.GAMES_LIST:
			return 6 
			logger.warning(str(user_details.steamid) + ' is trying to pass wrong data')
			###############################################

		id64_list = []
		# we are looking for STEAM_0:0:000000, U:1:0000000 and 76561197960265728
		id_list = re.findall(settings.SID64_PATTERN, steam_ids)\
				  + re.findall(settings.SID_PATTERN_NEW, steam_ids)\
				  + re.findall(settings.SID_PATTERN_OLD, steam_ids)		
				  	
		for id in id_list:
			i = convert_steam_id(id)
			id64_list.append(i)

		#remove id of scanning person (if it is not admin)	
		# if user_details.steamid in id64_list and not user.is_superuser:
			# id64_list.remove(user_details.steamid)

		if len(id64_list) > 0:
			if len(id64_list) > USER_LIMIT:
				return 3 											#too many players to scan
			marketable 	= True if marketable_check 	else False
			untrade = True if untrade_check else False
			uncraft = True if uncraft_check else False

			results_array = []
			tasks_array = []
			from tasks import scan_task
			for sid in id64_list[::4]:
				tasks_array.append(scan_task.apply_async((sid, game_type, marketable, uncraft, untrade, blacklist),queue="q1", expires=60))
			for sid in id64_list[1::4]:
				tasks_array.append(scan_task.apply_async((sid, game_type, marketable, uncraft, untrade, blacklist),queue="q2", expires=60))
			for sid in id64_list[2::4]:
				tasks_array.append(scan_task.apply_async((sid, game_type, marketable, uncraft, untrade, blacklist),queue="q3", expires=60))
			for sid in id64_list[3::4]:
				tasks_array.append(scan_task.apply_async((sid, game_type, marketable, uncraft, untrade, blacklist),queue="q4", expires=60))

			for task in tasks_array:
				try:
					task_result = task.get()
				except SoftTimeLimitExceeded:
					task_result = None
					logger.info('SoftTimeLimitExceeded')

				if isinstance(task_result, dict):
					results_array.append(task_result)
				else:
					TIMED_OUT = TIMED_OUT + 1
			gc.collect(0)
			gc.collect(1)
			gc.collect(2)
				

			# for i in results_array:
			# 	i['all'] = 0
			# 	for q in i:
			# 		i['all'] += len(q)
			result = {}
			if len(results_array) > 0:							#everything ok
				from operator import itemgetter
				result["raw"] 			= results_array
				result["user"] 			= user
				result["user_details"] 	= user_details
				result["results"] 		= sorted(results_array, key=itemgetter("hours"))
				result["time"] 			= str(datetime.now()-startTime)
				result["timed_out"] 	= TIMED_OUT
				return result
			elif TIMED_OUT > 0:			
				return 4 				# there were NO RESULTS and every task timed out
			else:						
				return 1 				#there were no results, tasks returned NONE
		else:
			return 0 					#no user input at all
	else:
		return 2 						#not logged in

def get_user_limit(user_details, game_type):
	USER_LIMIT = settings.NONPREMIUM_LIMIT
	if game_type == 'tf2' and user_details.premium_tf2:
		USER_LIMIT = settings.PREMIUM_LIMIT

	if game_type == 'dota2' and user_details.premium_dota2:
		USER_LIMIT = settings.PREMIUM_LIMIT

	if game_type == 'csgo' and user_details.premium_csgo:
		USER_LIMIT = settings.PREMIUM_LIMIT
	return USER_LIMIT

def get_blacklist(user_details, game_type):
	if game_type == 'tf2':
		if user_details.premium_tf2:
			blacklist = user_details.blacklist_tf2
		else:
			blacklist = get_default_blacklist('tf2')

	if game_type == 'dota2':
		if user_details.premium_dota2:
			blacklist = user_details.blacklist_dota2
		else:
			blacklist = get_default_blacklist('dota2')

	if game_type == 'csgo':
		if user_details.premium_csgo:
			blacklist = user_details.blacklist_csgo
		else:
			blacklist = get_default_blacklist('csgo')
	return blacklist

def get_default_blacklist(game_type):
	defuser = userProfile.objects.get(steamid=settings.DEFAULT_GUY_ID)
	if game_type == 'tf2':
		blacklist = defuser.blacklist_tf2
	elif game_type == 'dota2':
		blacklist = defuser.blacklist_dota2
	elif game_type == 'csgo':
		blacklist = defuser.blacklist_csgo
	return blacklist
			
def save_items(scanned_player, game_type):
	from connect import HatsdbClient
	client = HatsdbClient(read_only=False)
	connected = client.connect(game_type=game_type)
	items_from_old_api = None
	# used for dota 2 to get steamids for players who made something heroic
	for item in scanned_player['items']:
		if 'Heroic' in item['market_hash_name'] and not items_from_old_api:
			items_from_old_api = download_items_legacy(scanned_player['info']['id'], game_type)
			if not items_from_old_api:
				logger.warning('Failed to get items for heroic item: ' + str(item['id'])\
								 + ', owner: ' + str(owner) + ' (dota2)')
		i = process_item(item, game_type, scanned_player['info'], items_from_old_api=items_from_old_api)
		if i is not None:
			if connected:
				client.save_to_collection(i.to_dict(), i.defindex, game_type)
				if i.quality in settings.UNUSUAL_QUALITIES[game_type]:
					client.save_to_collection(i.to_dict(), 'unusuals', game_type)
				if i.quality in settings.TOURNAMENT_QUALITIES[game_type]:
					client.save_to_collection(i.to_dict(), 'tournament', game_type)
	if connected:
		client.disconnect()

def process_item(item, game_type, owner, items_from_old_api=None):
	if game_type == 'tf2':
		n = process_tf2_item(item, owner)
	if game_type == 'csgo':
		n = process_csgo_item(item, owner)
	if game_type == 'dota2':
		n = process_dota2_item(item, owner, items_from_old_api=items_from_old_api)
	return n

class db_item_tf2():
	def __init__(self):
		self._id 				= None
		self.defindex 			= None
		self.quality 			= None
		self.level 				= None 				#stranges don't have any levels
		self.tradable 			= None
		self.craftable 			= True
		self.craftnumber 		= None
		self.gifted 			= None
		self.paint 				= None
		self.owner 				= None
		self.effect 			= None
		self.killstreak_type 	= None
		self.ks_killstreaker 	= None
		self.ks_sheen 			= None
		self.odd_level 			= None 				
		self.quality_2 			= None
		self.halloween_spell 	= []
		self.strange_parts 		= []
		self.uses 				= None
		self.ks_defindex 		= None
		self.chem_set_defindex 	= None
		self.is_complicated 	= None
		self.new_defindex 		= None 				#this field must be turned into NONE before writing
		self.new_name 			= None 				#this field must be turned into NONE before writing
		self.hours 				= None
	def to_JSON(self):
		return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
	def to_dict(self):
		return {key: value for key, value in self.__dict__.items() if (value not in (None,[]))}

class db_item_dota2():
	def __init__(self):
		self._id 				= None
		self.defindex 			= None
		self.quality 			= None
		self.tradable 			= None
		self.craftable 			= None
		self.owner 				= None
		self.effect 			= None
		self.gems 				= []
		self.uses 				= None
		self.new_defindex 		= None 			#this field must be turned into NONE before writing
		self.new_name 			= None 			#this field must be turned into NONE before writing
		self.is_set_part		= None 			#this field must be turned into NONE before writing
		self.quality_name		= None 			#this field must be turned into NONE before writing
		self.tournament_info	= None
		self.hours 				= None
	def to_JSON(self):
		return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
	def to_dict(self):
		return {key: value for key, value in self.__dict__.items() if (value not in (None,[]))}

class db_item_csgo():
	def __init__(self):
		self._id 				= None
		self.defindex 			= None
		self.quality 			= None
		self.tradable 			= None
		self.owner 				= None
		self.effect 			= None
		self.stickers 			= []
		self.uses 				= None
		self.quality_name		= None 			#this field must be turned into NONE before writing
		self.tournament_info	= None
		self.hours 				= None
	def to_JSON(self):
		return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
	def to_dict(self):
		return {key: value for key, value in self.__dict__.items() if (value not in (None,[]))}

#------------TF2-------------

def process_tf2_item(item, owner):
	# checks for:
	# level
	# is tradable
	# craftnumber
	# Australium stuff
	# killstreaks stuff
	# chemistry sets stuff
	# strange hats with another quality
	# a fix for haunted axe and haunted scrap metal

	new_item = db_item_tf2()
	new_item._id = item['id']
	new_item.defindex = int(item['app_data']['def_index'])
	new_item.quality = int(item['app_data']['quality'])

	#LEVEL
	# strange items have no level, impossible to parse from web
	if 'Limited' in item['type']:
		item['type'] = item['type'][8:]
	level = item['type'].rsplit(' ')
	if level[0] == 'Level':
		new_item.level = int(level[1])

	#TRADABLE
	new_item.tradable = bool(item['tradable'])
	
	#CRAFTNUMBER
	if item['name'][0] != "'":
		#item is not renamed
		craftnumber = item['name'].rsplit(' ')
		if len(craftnumber) > 1:
			if craftnumber[-2:][0] != 'Series':
				if craftnumber[-1:][0][0] == '#':
					new_item.craftnumber = int(craftnumber[-1:][0][1:])

	# additional strange quality for strangified hats
	if 'Points Scored' in item['type']:
		new_item.quality_2 = 11
	if 'Strange Cosmetic Item' in item['type']:
		new_item.quality_2 = 11

	# move haunted scrap and axe to haunted quality
	if 'Unusual' in item['market_hash_name']:
		if new_item.defindex in [267,266]:
			new_item.quality = 13
	
	# killstreak type
	if 'Killstreak' in item['market_hash_name']:
		n = process_killstreak_tf2(item)
		new_item.ks_killstreaker = n['ks_killstreaker']
		new_item.ks_sheen = n['ks_sheen']
		new_item.killstreak_type = n['killstreak_type']
		new_item.new_defindex = n['new_defindex']
		if n['is_fabricator']:
			new_item.is_complicated = True
			new_item.ks_defindex = n['ks_defindex']

	#chemistry set stuff
	if 'Chemistry Set' in item['market_hash_name']:
		n = process_strangifier_tf2(item)
		new_item.is_complicated = True
		new_item.chem_set_defindex = n['chem_set_defindex']
		new_item.defindex = n['new_defindex']
		new_item.new_defindex = n['new_defindex']

	if 'Australium' in item['market_hash_name'] and item['market_hash_name'] != 'Australium Gold':
		n = process_australium_tf2(new_item.defindex)
		new_item.new_defindex = n['new_defindex']
		new_item.new_name = n['new_name']

	process_descriptions_tf2(item, new_item)

	#change defindex for aus, chemistry sets and ks fabricators
	if new_item.new_defindex > -1:
		type_name = ""
		if new_item.quality != 11:
			type_name = ' '.join(level[2:])
		if not new_item.new_name:
			new_item.new_name = item['market_hash_name']

		a,b = def_item.objects.get_or_create(
			name=new_item.new_name,
			defindex=new_item.new_defindex,
			type_name=type_name,
			image_url='http://steamcommunity-a.akamaihd.net/economy/image/' + item['icon_url'],
			game_type='tf2'
			)
		if b:
			logger.info('Created ' + str(a) + ' with defindex '+ str(a.defindex) + ' (tf2)')
		elif not a:
			logger.critical('Failed to create item with name ' + new_item.new_name + ' (tf2)')
		else:
			pass
		new_item.defindex = int(new_item.new_defindex)
		new_item.new_defindex = None

	if new_item.defindex == None or new_item.quality == None:
		logger.critical('Parsing failed for asset ' + item['classid'] + '_' + item['instanceid'] + ' (tf2)')
		new_item = None
	else:
		new_item.owner = owner['id']
		new_item.hours = owner['all_hours'][str(settings.APPS['tf2'])]
		new_item.new_name = None
	return new_item

def process_descriptions_tf2(item, new_item):
	# checks:
	# was gifted
	# is painted and with what paint
	# is craftable
	# unusual effect
	# halloween spells
	# attached strange parts
	# uses
	for desc in item['descriptions']:

		if 'Gift from: ' in desc['value']:
			new_item.gifted = True


		if 'Paint Color: ' in desc['value']:
			color_name = desc['value'][13:]
			try:
				c = paint.objects.get(name=color_name, game_type='tf2')
			except Exception, e:
				logger.error('Cannot get paint ' + color_name + ' (tf2)')
			else:
				new_item.paint = c.defindex


		if ('( Not Usable in Crafting )' or '( Not Tradable or Usable in Crafting )') in desc['value']:
			new_item.craftable = False


		if new_item.quality == 5 and 'Effect: ' in desc['value']:
			effect_name = desc['value'][8:]
			try:
				eff = effect.objects.filter(name=effect_name, game_type='tf2')
				if eff.count() > 0:
					eff = eff[0]
			except Exception, e:
				logger.error('Cannot get effect ' + effect_name + ' (tf2)')
			else:
				new_item.effect = eff.defindex


		if desc['value'][0:11] == 'Halloween: ':
			pattern = "Halloween: (.*?) \(spell only active during event\)"
			spell_name = re.findall(pattern, desc['value'])
			if spell_name:
				spell = None
				if 'Pumpkin Bombs' in spell_name:
					spell = def_item.objects.get(name='Halloween Spell: Gourd Grenades', game_type='tf2')
				else:
					try:
						spell = def_item.objects.get(name='Halloween Spell: ' + spell_name[0], game_type='tf2')
					except Exception, e:
						logger.error('Cannot get halloween_spell ' + spell_name[0] + ' (tf2)')
				if spell:
					new_item.halloween_spell.append(spell.defindex)

		#strange parts, usually (part name: number), no spaces after (

		if re.match("\(.*[A-Za-z]\: .*[0-9]\)", desc['value']):
			n =	re.findall("[^0-9:()]+", desc['value'])
			if n:
				# part_name = n[0].encode('ascii','ignore')
				# part_name = n[0].encode('utf-8')
				part_name = n[0]
				if part_name in settings.TF2_INGNORED_STRANGE_PARTS:
					pass
				else:
					try:
						p = strange_part.objects.get(description=part_name, game_type='tf2')
					except Exception, e:
						logger.error('Cannot get strange_part ' + part_name + ' on item ' + item['market_hash_name'] + ' (tf2) ')
					else:
						new_item.strange_parts.append(p.defindex)


		if 'This is a limited use item' in desc['value']:
			try:
				new_item.uses = int(desc['value'][35:])
			except Exception, e:
				logger.error('Cannot parse uses_amount for (tf2)')

def process_killstreak_tf2(item):
	# checks for: 
	# killstreak type
	# sheen
	# killstreaker
	# is fabricator
	# defindex of fabricator's item
	# applies new defindex
	n_item = {"killstreak_type":None,
				'is_fabricator':False,
				'ks_sheen':None, 
				'ks_killstreaker':None, 
				'ks_defindex': None, 
				'new_defindex': None}
	if 'Specialized' in item['market_hash_name']:
		n_item['killstreak_type'] = 1
	elif 'Professional' in item['market_hash_name']:
		n_item['killstreak_type'] = 2
	else:
		n_item['killstreak_type'] = 0

	if 'Fabricator' in item['market_hash_name']:
		n_item['is_fabricator'] = True

	k,s = (None,)*2
	for desc in item['descriptions']:
		#specialized killstreaks have sheen only
		if n_item['killstreak_type'] == 1:
			if 'Sheen: ' in desc['value']:
				if n_item['is_fabricator']:
					sheen_name = desc['value'][8:-1]
				else:
					sheen_name = desc['value'][7:]
				try:
					s = sheen.objects.get(name=sheen_name, game_type='tf2')
				except Exception, e:
					logger.error('Cannot get sheen ' + sheen_name + ' (tf2)')
				else:
					n_item['ks_sheen'] = s.defindex

		#prof killstreaks have sheen and killstreaker
		#fabricators have sheen and killstreaker in one string (not two)
		if n_item['killstreak_type'] == 2:
			if n_item['is_fabricator']:
				if ('Killstreaker: ' or 'Sheen: ') in desc['value']:
					#has sheen+killstreaker in description
					names = desc['value'].rsplit(',')
					killstreaker_name = names[0][15:]
					sheen_name = names[1][8:-1]
			else:
				if 'Killstreaker: ' in desc['value']:
					killstreaker_name = desc['value'][14:]
				elif 'Sheen: ' in desc['value']:
					sheen_name = desc['value'][7:]
			try:
				if n_item['is_fabricator']:
					k = killstreaker.objects.get(name=killstreaker_name, game_type='tf2')
					s = sheen.objects.get(name=sheen_name, game_type='tf2')
				elif killstreaker_name:
					k = killstreaker.objects.get(name=killstreaker_name, game_type='tf2')
					killstreaker_name = None
				elif sheen_name:
					s = sheen.objects.get(name=sheen_name, game_type='tf2')
					sheen_name = None
			except Exception, e:
				#no info for sheen/killstreaker here, maybe in next one?
				pass
			else:
				if k:
					n_item['ks_killstreaker'] = k.defindex
				if s:
					n_item['ks_sheen'] = s.defindex
	#fabricator defitem
	if n_item['killstreak_type'] == 1:
		FABRICATOR_START_DEFINDEX = settings.SPEC_FABRICATOR_START_DEFINDEX
	if n_item['killstreak_type'] == 2:
		FABRICATOR_START_DEFINDEX = settings.PROF_FABRICATOR_START_DEFINDEX
	if n_item['is_fabricator']:
		item_name = item['market_hash_name'].replace('Professional Killstreak ','')
		item_name = item_name.replace('Specialized Killstreak ', '')
		item_name = item_name.replace(' Kit Fabricator', '')
		i = def_item.objects.filter(name=item_name, game_type='tf2')
		try:
			it = i[0]
		except Exception, e:
			logger.error('Failed to get defitem for fabricator '\
						 + item['classid'] + '_' + item['instanceid'] + ' (tf2)')
		else:
			n_item['ks_defindex'] = it.defindex
			n_item['new_defindex'] = FABRICATOR_START_DEFINDEX + it.defindex

	if (n_item['killstreak_type'] == 2) and (n_item['ks_killstreaker'] == None or n_item['ks_sheen'] == None):
		logger.error('Failed to get killstreaker/sheen for item '\
					  + item['classid'] + '_' + item['instanceid'] + ' (tf2)')

	if (n_item['killstreak_type'] == 1) and (n_item['ks_sheen'] == None):
		logger.error('Failed to get sheen for item '\
					  + item['classid'] + '_' + item['instanceid'] + ' (tf2)')
	return n_item

def process_strangifier_tf2(item):
	# checks for:
	# defindex of set's item
	# new defindex
	# regular defindex
	n_item = {'chem_set_defindex': -1, 'new_defindex': -1}
	r = def_item.objects.filter(name=item['market_hash_name'], game_type='tf2')
	try:
		r = r[0]
	except Exception, e:
		item_name = re.findall('^(.*?)\ Strangifier', item['market_hash_name'])
		if item_name:
			i = def_item.objects.filter(name=item_name[0], game_type='tf2')
			try:
				it = i[0]
			except Exception, e:
				logger.error('Failed to get defitem for chemistry_set '\
							 + item['classid'] + '_' + item['instanceid'] + ' (tf2)')
			else:
				n_item['chem_set_defindex'] = it.defindex
				n_item['new_defindex'] = settings.CHEMSET_START_DEFINDEX + it.defindex
	else:
		n_item['new_defindex'] = r.defindex
		n_item['chem_set_defindex'] = r.defindex - settings.CHEMSET_START_DEFINDEX
	return n_item
	
def process_australium_tf2(defindex):
	# checks for:
	# new defindex
	# new name
	n_item = {'new_defindex': -1, 'new_name': -1}
	i = def_item.objects.filter(defindex=defindex, game_type='tf2')
	try:
		it = i[0]
	except Exception, e:
		logger.error('Failed to get defitem for australium '\
					  + item['classid'] + '_' + item['instanceid'] + ' (tf2)')
	else:
		n_item['new_name'] = 'Australium ' + it.name
		n_item['new_defindex'] = settings.AUSTRALIUM_START_DEFINDEX + it.defindex
	return n_item

#------------DOTA2-------------

def process_dota2_item(item, owner, items_from_old_api):
	# checks for:
	# id
	# tradable
	# gems
	# tournament info
	# creates exceptional recipes, gems, tournament teams/players
	new_item = db_item_dota2()
	new_item._id = item['id']
	new_item.tradable = bool(item['tradable'])
	new_item.owner = owner['id']
	new_item.hours = owner['all_hours'][str(settings.APPS['dota2'])]

	if item['market_hash_name'][0:8] == 'Recipe: ':
		process_recipe_dota2(item, new_item)

	#quality
	for tag in item['tags']:
		if tag['category_name'] == 'Quality':
			if tag['name'] == 'Standard':
				# 4 is the defindex for STANDARD->DDDDDDDDDDDDDDD quality
				new_item.quality = 4
				new_item.quality_name = None
			else:
				q = quality.objects.filter(name=tag['name'], game_type='dota2')
				try:
					qt = q[0]
				except Exception, e:
					logger.error('Failed to get quality ' + tag['name'] + ' (dota2)')
				else:
					new_item.quality = int(qt.defindex)
					new_item.quality_name = tag['name']

	process_descriptions_dota2(item, new_item, items_from_old_api)

	# item is not part of the set, got to get defindex from name
	if not new_item.defindex:
		# maybe this is greevil?
		if 'Greevil' in item['market_hash_name']:		# diretide greevils
			new_item.defindex = 10070
		elif 'Present' in item['market_hash_name']:		#level-up presents
			new_item.defindex = 15407
		elif 'Egg' in item['market_hash_name']:			#seraphic eggs
			new_item.defindex = 10066
		else:

			#this is not a greevil, everything is bad
			if new_item.quality_name:
				u = len(new_item.quality_name)+1
				item_name = item['market_hash_name'][u:]
			else:
				item_name = item['market_hash_name']
			try:
				d = def_item.objects.filter(name=item_name, game_type='dota2')
				d = d[0]
			except Exception, e:
				logger.critical('Impossible to parse defindex for '\
								+ item['classid'] + '_' + item['instanceid'] +' (dota2)')
			else:
				new_item.defindex = int(d.defindex)

	new_item.is_set_part = None
	new_item.quality_name = None
	if new_item.craftable == None:
		new_item.craftable = True

	if new_item.defindex == None or new_item.quality == None:
		logger.critical('Parsing failed for asset ' + item['classid'] + '_' + item['instanceid'] + ' (dota2)')
		new_item = None
	return new_item

def process_descriptions_dota2(item, new_item, items_from_old_api):
	# all description info:
	# tournament info
	# gems
	# is part of the set (allows to get defindex)
	# craftability
	new_item.is_set_part = False
	if new_item.quality_name:
		u = len(new_item.quality_name)+1
		item_name = item['market_hash_name'][u:]
	else:
		item_name = item['market_hash_name']

	for desc in item['descriptions']:
		if desc.has_key('app_data'):
			# if item is in set - we can get a defindex by parsing set items
			if desc['app_data'].has_key('is_itemset_name'):
				new_item.is_set_part = True

		if new_item.is_set_part:
			if item_name == desc['value']:
				if desc['app_data'].has_key('def_index'):
					new_item.defindex = int(desc['app_data']['def_index'])

		if desc.has_key('type'):
			if desc['type'] == 'html':
				if desc['value']:
					if desc['value'][0] == '<':
						process_html_desc_dota2(desc['value'], item, new_item, items_from_old_api)
		
				if (' Not Tradable or Usable in Crafting ' or ' Not Usable in Crafting ') in desc['value']:
					new_item.craftable = False

def process_html_desc_dota2(desc, item, new_item, items_from_old_api):
	# used to prepare description and process it
	# looks for: 
	# gems
	# tournament info
	from bs4 import BeautifulSoup
	soup = BeautifulSoup(desc)
	gems = soup.findAll(style=settings.DOTA_GEM_DIV_STYLE)
	if gems:
		process_gems_dota2(gems, new_item)
	tournaments = soup.findAll('div',{'id':'tournament_info'})
	if tournaments:
		new_item.tournament_info = process_tournament_item_dota2(tournaments, item, items_from_old_api)

def process_tournament_item_dota2(info, item, items_from_old_api):
	# used to get info about item tourney
	# player, team1, team2, matchid, event type, date
	item_id = item['id']
	info = info[0]
	event = {'player':None,
			'player_id':None,	#saved to mysql
			'player_sid':None,	#saved to mongodb
			'team1':None,
			'team2':None,
			'event_date':None,
			'event_id':None,
			'match_id':None}
	match_id = info.findAll('font',{'color':'#666666'})
	if match_id:
		event['match_id'] = int((match_id[0].text)[9:])

	pics = []
	event_info = info.findAll('center')
	# 2 pics with team logos and name of event (ex. double kill)
	if len(event_info) == 2:
		event_name = event_info[1].text
		for p in event_info[0].findAll('img'):
			pics.append(p['src'])
		if len(pics) != 2:
			logger.error('Failed to parse pics for tournament item ' + str(item_id) + ' (dota2)')
	else:
		logger.error('Failed to tournament info for ' + str(item_id) + ' (dota2)')


	event_details = info.findAll('font', {'color':'#999999'})
	if event_details:
		event_details = event_details[0].text
		try:
			tournament_event = dota_tournament_event.objects.get(name=event_name)
		except Exception, e:
			logger.error('Failed to get tournament_event ' + event_name + ' (dota2)')
		else:
			event_details = re.split(tournament_event.strings, event_details)
			# '(\D*.?) of (\D*.?) against (\D*.?) on ([\D0-9]*.?)'
			
			if len(event_details) == tournament_event.length:
				# proper amount of fields
				# e.g. 5 fields for fb - p1 of t1 killd p2 from t2 on time1
				# 4 fields for victory
				# t1 won t2 with score 2-1 on time1
				from datetime import datetime
				event_details[-1] = event_details[-1].rstrip('.!')
				event['event_date']	= datetime.strptime(event_details[-1], '%b %d, %Y (%H:%M:%S)')
				event['player']	= event_details[0]
				player_sid  = get_tournament_player_dota2(item_id, items_from_old_api)
				if player_sid:
					p, updated = dota_tournament_player.objects.update_or_create(
						steam_id=str(player_sid), defaults={'nickname':event['player']})
					event['player_sid'] = player_sid
					event['player_id'] = p.id
				event['event_id'] = int(tournament_event.defindex)

				if tournament_event.defindex == 2:
					# first blood, 5 fields with second player
					team1_name = event_details[2]
					team2_name = event_details[3]
				else:
					team1_name = event_details[1]
					team2_name = event_details[2]

				if tournament_event.defindex == 8:
					# ally denial, only one team listed
					# 'unk of kokoko denied his ally on'
					team1_name = event_details[1]
					team2_name = None

				team_ids = []
				team_ids = process_teams_dota2(team1_name, team2_name, pics)
				event['team1'] = int(team_ids[0].id)
				if team2_name:
					event['team2'] = int(team_ids[1].id)

			else:
				logger.error('Tournament info badly parsed for ' + tournament_event.name + ' '\
							 + item['classid'] + '_' + item['instanceid'] + ' (dota2)')
	return event
	# save the item to the separate 'tournaments' table 	- django
	# id, event_type, team 1, team 2, steamid of player
	# save player to 'tournament player' 				- django
	# nickname_s_!!, steamid, team_id
	# save teams to 'tournament teams'					- django
	# team id, 

def process_recipe_dota2(item, new_item):
	# used to create exceptional recipes
	d = None
	except_recipe = def_item.objects.get(name='Recipe: Craft Exceptional Item')
	try:
		d = def_item.objects.get(name__iexact=item['market_hash_name'], game_type='dota2')
	except Exception, e:
		# log and send a message about creating new recipe
		# this is a special recipe for battlefury or shit like that
		obj, created1 = dota_exceptional_recipe.objects.update_or_create(
				name=item['market_hash_name'],
				defindex=settings.DOTA_EXRECIPE_START_DEFINDEX + dota_exceptional_recipe.objects.count()+1,
				image_url=except_recipe.image_url
				)
		defitem, created2 = def_item.objects.update_or_create(
				name=item['market_hash_name'],
				defindex=obj.defindex,
				image_url=except_recipe.image_url,
				game_type='dota2'
				)
		if created1 and created2:
			logger.info('Created ' + item['market_hash_name'] + ' with defindex '\
					+ str(defitem.defindex) + ' using asset ' + item['classid']\
					+ '_' + item['instanceid'] + ' (dota2)')
			new_item.defindex = obj.defindex
		else:
			logger.critical('Failed to create ' + item['market_hash_name']\
			 +' using asset ' + item['classid']	+ '_' + item['instanceid'] + ' (dota2)')

def process_teams_dota2(team1_name, team2_name, pics):
	t1, created = dota_tournament_team.objects.get_or_create(
		name=team1_name,
		image_url=pics[0]
		)
	if team2_name:
		t2, created = dota_tournament_team.objects.get_or_create(
			name=team2_name,
			image_url=pics[1]
			)
	else:
		t2 = None
	return (t1,t2)

def get_tournament_player_dota2(item_id, items_from_old_api):
	# used to get steamid of tournament dota2 player who was involved in heroic event
	player = None
	if items_from_old_api:
		logger.info('we have items')
		if items_from_old_api['result'].has_key('items'):
			for item in items_from_old_api['result']['items']:
				if item['id'] == int(item_id):
					for attr in item['attributes']:
						if attr['defindex'] == 312:
							player = attr['account_info']['steamid']
					break
	return player

def tag_with_background(tag):
	# used to get background images to create new dota2 gems
	if tag.has_attr('style'):
		if 'background-image' in tag['style']:
			return tag

def process_gems_dota2(gems, new_item):
	# used to get info about gems and create new if needed
	for gem in gems:
		gem_descriptions = gem.findAll('span')
		if len(gem_descriptions) == 2:
			gem_name = gem_descriptions[0].text
			gem_type = gem_descriptions[1].text
			if 'Empty' in gem_name:
				continue
			# removing the amount of kills/gold/etc to get clean name
			if ':' in gem_name:
				gem_name = gem_name.split(':')[0]
				
			if 'Games Watched' in gem_type:
				gem_type = 'Spectator Gem'
				gem_name = 'Spectator: ' + gem_name
			if 'Autographed by' in gem_name:
				gem_name = 'Autograph: ' + gem_name[15:]
			if 'Inscribed' in gem_type:
				gem_name = 'Inscribed ' + gem_name
			if 'Ethereal' in gem_type:
				gem_name = 'Ethereal: ' + gem_name
			if 'Prismatic' in gem_type:
				gem_name = 'Prismatic: ' + gem_name
			if 'Kinetic' in gem_type:
				gem_name = 'Kinetic: ' + gem_name
			if 'Mastery' in gem_type:
				gem_name = 'Mastery: ' + gem_name				
			if 'Victory Prediction Gem' in gem_type:
				gem_name = 'Victory Prediction Gem'
			if 'Foulfell Shard' in gem_type:
				gem_name = 'Foulfell Shard'
				gem_type = 'Black Gem'
			if "Dreamer's Gem" in gem_type:
				gem_name = "Dreamer's Gem"
				gem_type = 'Sleeping Aid'
			if ('Bloodstone' or 'Ascendant' or 'Taegeuk') in gem_type:
				gem_name = gem_type
				gem_type = 'Relic of Prestige'
			if gem_type == "Rune of the Duelist Indomitable":
				gem_name = gem_type
				gem_type = 'Inscribed Gem'

			created = False
			new_gem = def_item.objects.filter(name=gem_name, type_name__contains=gem_type, game_type='dota2')
			try:
				new_gem = new_gem[0]	
			except Exception, e:
				# no gem found, need to create one
				defindex = dota_gem.objects.count() + 1 + settings.DOTA_GEM_START_DEFINDEX
				new_gem = def_item.objects.create(
					defindex = defindex,
					name = gem_name,
					type_name = gem_type,
					game_type = 'dota2'
					)
				g = dota_gem.objects.create(defindex=defindex, name=gem_name)
				created = True
				logger.info('Created new gem ' + gem_name + ' with defindex '\
							+ str(g.defindex) + ' (dota2)')

				# add an image for gem based on its ___type___
				# there are shitload inscribed gems with same pic
				g = def_item.objects.filter(type_name=gem_type, game_type='dota2')
				try:
					gt = g[0]
				except Exception, e:
					# CUT MY STYLE INTO PIECES
					# THIS IS MY LAST RESORT
					bg = gem.find(tag_with_background)
					if bg:
						bg_regex = re.compile('\((.*?)\)')
						url = bg_regex.findall(bg)[0]
						new_gem.image_url = url
					logger.info('No gem with type ' + gem_type + ' found, getting image from html (dota2)')
				else:
					new_gem.image_url = gt.image_url

				new_gem.save()
			new_item.gems.append(int(new_gem.defindex))
		else:
			logger.error('During gem info parsing amount of descriptions was not 2 (dota2)')

#------------CSGO-------------

def process_csgo_item(item, owner):
	# checks for:
	# id
	# tradability
	# quality
	# rarity
	# exterior
	# tournament shit
	new_item = db_item_csgo()
	new_item._id = item['id']

	#TRADABLE
	new_item.tradable = bool(item['tradable'])
	process_tags_csgo(item, new_item)
	process_descriptions_csgo(item, new_item)

	if not new_item.quality_name:
		new_item.quality_name = ''
	else:
		new_item.quality_name = new_item.quality_name + ' '

	name_re = re.compile(new_item.quality_name + '(.*) \(')
	item_name = name_re.findall(item['market_hash_name'])
	if not item_name:
		item_name = item['market_hash_name']
	else:
		item_name = item_name[0]


	try:
		i = def_item.objects.get(name=item_name, game_type='csgo')
	except Exception, e:
		new_defindex = settings.CSGO_ITEM_DEFINDEX_START + def_item.objects.filter(game_type='csgo').count()
		if def_item.objects.filter(defindex=new_defindex, game_type='csgo').count > 0:
			new_defindex = new_defindex + 10
		i = def_item.objects.create(
			name=item_name,
			defindex=new_defindex,
			image_url='http://steamcommunity-a.akamaihd.net/economy/image/' + item['icon_url'],
			game_type='csgo'
			)
		i.save()
		logger.info('Created ' + item_name + ' with defindex '\
					+ str(i.defindex) + ' using asset ' + item['classid']\
					+ '_' + item['instanceid'] + ' (csgo)')
	new_item.defindex = int(i.defindex)
	new_item.quality_name = None

	if new_item.defindex == None or new_item.quality == None:
		logger.critical('Parsing failed for asset ' + item['classid'] + '_' + item['instanceid'] + ' (csgo)')
		new_item = None
	else:
		new_item.owner = owner['id']
		new_item.hours = owner['all_hours'][str(settings.APPS['csgo'])]
	return new_item

def process_tags_csgo(item, new_item):
	# rarity, exterior, quality
	item_rarity = None
	item_exterior = None
	item_quality = None
	# knifes can be unusual and strange
	# so valve decided to make a new hidden quality - UNUSUAL_STRANGE
	# which is listed among with normal qualities
	unusual_strange = False

	for tag in item['tags']:
		# rarity - Consumer/Industrial
		if tag['category_name'] == 'Quality':
			item_rarity = tag['name']
		# exterior - Minimal Wear/Field-Tested
		if tag['category_name'] == 'Exterior':
			item_exterior = tag['name']
		# quality - Souvenir/StatTrak
		if tag['category_name'] == 'Category' and not unusual_strange:
			if tag['internal_name'] == 'unusual_strange':
				unusual_strange = True
			item_quality = tag['name']

	if item_rarity:
		try:
			r = rarity.objects.get(name=item_rarity, game_type='csgo')
		except Exception, e:
			logger.error('Cannot get item_rarity ' + item_rarity + ' (csgo)')
		else:
			new_item.rarity = int(r.defindex)

	if item_quality:
		try:
			q = quality.objects.get(name=item_quality, game_type='csgo')
		except Exception, e:
			logger.error('Cannot get item_quality ' + item_quality + ' (csgo)')
		else:
			if item_quality != 'Normal':
				new_item.quality_name = item_quality
			new_item.quality = int(q.defindex)

	if item_exterior:
		try:
			e = exterior.objects.get(name=item_exterior)
		except Exception, e:
			logger.error('Cannot get item_exterior ' + item_exterior + ' (csgo)')
		else:
			new_item.exterior = int(e.defindex)

def process_descriptions_csgo(item, new_item):
	# the only valuable	descriptions are html ones
	for desc in item['descriptions']:
		if desc['type'] == 'html':
			if desc['value']:
				if desc['value'][:3] == '<br':
					process_html_desc_csgo(desc, new_item)

	if new_item.quality_name == 'Souvenir':
		process_tournament_item_csgo(item, new_item)

def process_html_desc_csgo(desc, new_item):
	# html description contains stickers
	from bs4 import BeautifulSoup
	soup = BeautifulSoup(desc['value'])
	stickers = soup.findAll('div',id='sticker_info')
	if stickers:
		pics = stickers[0].findAll('img')
		names = (stickers[0].findAll('center'))[0].text
		if 'Sticker' in names:
			names = names[9:].split(',')
			for number, n in enumerate(names):
				names[number] = n.lstrip(' ')
			sticks = [{'pic':pic, 'name':name} for pic,name in zip([p['src'] for p in soup.findAll('img')],names)]
			if sticks:
				process_stickers_csgo(sticks, new_item)

def process_stickers_csgo(sticks, new_item):
	# processes stickers and creates them if needed
	for s in sticks:
		new_name = 'Sticker | ' + s['name']
		try:
			sticker = def_item.objects.get(name=new_name)
		except Exception, e:
			# create a new one
			new_defindex = settings.CSGO_STICKER_DEFINDEX + \
						   def_item.objects.filter(defindex__range=(settings.CSGO_STICKER_DEFINDEX,700000), game_type='csgo').count()+1
			sticker = def_item.objects.create(
				name=new_name,
				image_url=s['pic'],
				defindex=new_defindex,
				game_type='csgo')
			if sticker:
				logger.info('Created ' + new_name + ' with defindex '\
							+ str(sticker.defindex) + ' (csgo)')
				new_item.stickers.append(int(sticker.defindex))
			else:
				logger.error('Failed to create sticker ' + new_name + ' with defindex '\
							+ str(new_defindex) + ' (csgo)')
		else:
			new_item.stickers.append(int(sticker.defindex))
		
def process_tournament_item_csgo(item, new_item):
	event = {
		'event_id': None,		#csgo_tournament_event, DREAMHACK 2013
		'event_type': None,		#csgo_tournament_match, GRAND FINAL
		'team1': None,
		'team2': None
	}
	for desc in item['descriptions']:
		if desc.has_key('color'):
			if desc['color'] == settings.CSGO_TOURNAMENT_COLOUR:
				if 'commemorates' in desc['value']:
					event_re = re.compile('This item commemorates (.*) CS:GO Championship\.')
					event_name = event_re.findall(desc['value'])[0]
					e, created = csgo_tournament_event.objects.get_or_create(name=event_name)
					if created:
						logger.info('Created tournament event ' + event_name + ' (csgo)')
					event['event_id'] = int(e.id)

				if 'It was dropped' in desc['value']:
					type_re = re.compile('It was dropped during the (.*) match between (.*) and (.*)\.')
					info = type_re.findall(desc['value'])[0]
					if len(info) == 3:
						event_type = info[0]
						team1_name = info[1]
						team2_name = info[2]

						t1, created1 = csgo_tournament_team.objects.get_or_create(
							name=team1_name
							)
						t2, created2 = csgo_tournament_team.objects.get_or_create(
							name=team2_name
							)
						ev, created_ev = csgo_tournament_match.objects.get_or_create(
							name=event_type)

						if created1:
							logger.info('Created tournament team  ' + team1_name + ' (csgo)') 
						if created2:
							logger.info('Created tournament team  ' + team2_name + ' (csgo)') 
						if created_ev:
							logger.info('Created tournament event ' + event_type + ' (csgo)') 

						event['team1'] = int(t1.id)
						event['team2'] = int(t2.id)
						event['event_type'] = int(ev.id)
					else:
						logger.error('Wrong amount of fields for tournament info '\
									  + item['classid'] + '_' + item['instanceid'] + ' (csgo)') 
	new_item.tournament_info = event

def build_query(data):
	from get_numbers import return_int
	query = {}
	allowed_keys = frozenset(['gifted', 'hours_more_than', 'sheen_id', 'level', 'paint_id', 'craftable',\
					'game_type', 'craftnumber', 'tradable', 'hours_less_than', 'effect_id',\
					'strange_parts', 'ks_id', 'item_uses', 'defindex', 'quality', 'ks_type', 'gems',\
					'stickers', 'exterior', 'skip', 'sort_by', 'effect', 'page','team1','team2',
					'player_sid', 'match_id', 'event_id', 'event_type', 'tournament'])
	bool_keys = ['tradable', 'craftable','gifted']

	a = frozenset(data.keys())
	if a.issubset(allowed_keys):
		for key in data:
			if isinstance(data[key],unicode) and key!='game_type':
				data[key] = return_int(data[key])
			if isinstance(data[key],list):
				for num, value in enumerate(data[key]):
					data[key][num] = return_int(value)
				if len(data[key]) == 1:
					data[key] = data[key][0]

		if data.has_key('craftable'):
			if data['craftable'] == 1:
				data.pop('craftable')
			elif data['craftable'] == 2:
				data['craftable'] = True
			else:
				data['craftable'] = False

		if data.has_key('tradable'):
			if data['tradable'] == 1:
				data.pop('tradable')
			elif data['tradable'] == 2:
				data['tradable'] = True
			else:
				data['tradable'] = False

		data['hours'] = {}
		if data.has_key('hours_more_than'):
			if data['hours_more_than'] is not None:
				data['hours']['$gt'] = data['hours_more_than']
			data.pop('hours_more_than')
		if data.has_key('hours_less_than'):
			if data['hours_less_than'] is not None:
				data['hours']['$lt'] = data['hours_less_than']
			data.pop('hours_less_than')

		if data.has_key('team1') and data.has_key('team2'):
			if data['team1'] and data['team2']:
				data['team1'] = [data['team2'],data['team1']]
				data['team2'] = data['team1']

		if data.has_key('tournament'):
			data['event_id'] = data['tournament']
			data.pop('tournament')

		if data.has_key('gifted'):
			if data['gifted'] == False:
				data.pop('gifted')


		query = dict((k, v) for k, v in data.iteritems() if v)

		#fix for items without hours
		if not query.has_key('hours'):
			query['hours'] = {}
			query['hours']['$gt'] = 0

		if data.has_key('quality'):
			if data['quality'] == 0:
				query['quality'] = 0

		for key in bool_keys:
			if data.has_key(key):
				query[key] = data[key]
		for key in query:
			if isinstance(query[key], list):
				query[key] = {'$in':query[key]}
		query.pop('game_type')
		if query.has_key('skip'):
			query.pop('skip')

		tourney_stuff = ['team1','team2', 'player_sid', 'match_id', 'event_id', 'event_type']
		if bool(set(data.keys()) & set(tourney_stuff)):
			for key in tourney_stuff:
				if query.has_key(key):
					query['tournament_info.'+key] = query[key]
					query.pop(key)

			if query.has_key('tournament_info.team1') and not query.has_key('tournament_info.team2'):
				query['$or'] = [{'tournament_info.team1':query['tournament_info.team1']},{'tournament_info.team2':query['tournament_info.team1']}]
				query.pop('tournament_info.team1')
			elif query.has_key('tournament_info.team2') and not query.has_key('tournament_info.team1'):
				query['$or'] = [{'tournament_info.team1':query['tournament_info.team2']},{'tournament_info.team2':query['tournament_info.team2']}]
				query.pop('tournament_info.team2')


	else:
		# query stays empty
		pass
	return query

# works
@csrf_protect
def search_results(request, data):
	user, openid_user, user_details = is_logged(request)
	results = {'page':0,'items':None,'query_details':None}
	if user.is_authenticated():
		from get_numbers import return_int
		from connect import HatsdbClient
		import operator
		#-----------------------
		game_type = 'tf2' 		#default
		client = HatsdbClient()
		connected = False
		unsorted_list = []
		query_details = {}
		page = 0
		query = None
		if data.has_key('game_type'):
			game_type = data['game_type']
			if game_type in settings.APPS.keys():
				connected = client.connect(game_type=game_type)
			
		if connected:
			time1 = datetime.now()
			if data.has_key('defindex'):
				query = build_query(data)
			if not query:
				return results
			if not user_details.is_premium(game_type):
				if data.has_key('hours_less_than'):
					if data['hours_less_than'] != "":
						query.pop('hours')
				if data.has_key('hours_more_than'):
					if data['hours_more_than'] != "":
						if query.has_key('hours'):
							query.pop('hours')

			query_details['query'] = str(query)
			defindex = str(query['defindex'])
			if defindex == "":
				defindex = "-1"
			query.pop('defindex')
			if query.has_key('page'):
				query.pop('page')
				page = return_int(data['page'])
			
			items = client.find(defindex, query, skip=(page-1)*20, limit=20, sort_order=1)
			query_details['time'] = datetime.now() - time1
			query_details['count'] = client.get_count(defindex, query)
		#---------parsing items--------------
			
			LIST_OF_OWNERS = []
			for item in items:
				if game_type == 'tf2':
					unsorted_list.append(append_names_tf2(item, game_type))
				elif game_type == 'dota2':
					unsorted_list.append(append_names_dota2(item, game_type))
				elif game_type == 'csgo':
					unsorted_list.append(append_names_csgo(item, game_type))
				else:
					pass
				LIST_OF_OWNERS.append(item['owner'])

			from data_collectors import download_owners_info, resolve_text_status
			LIST_OF_OWNERS = list(set(LIST_OF_OWNERS))
			statuses = download_owners_info(LIST_OF_OWNERS)
			for item in unsorted_list:
				if statuses:
					for status in statuses['response']['players']:
						if status['steamid'] == item['owner']:
							item['owner_status'] = resolve_text_status(status['personastate'])
				else:
					item['owner_status'] = '??'

			client.disconnect()

		if len(unsorted_list) > 0 and page == 0:
			page = 1
		results['page'] = page
		results['query_details'] = query_details
		results['items'] = unsorted_list
	return results

# works
def append_names_tf2(item, game_type):
	if item.has_key('effect'):													
		eff = effect.objects.filter(defindex=item['effect'], game_type=game_type)
		if len(eff) > 0:
			item['effect'] = eff[0].name
		else:
			item['effect'] = 'A new and unknown effect. You\'d better contact webmaster'
			logger.error('Cannot find effect with id ' + str(item['effect']) + ' ' + game_type)

	if item.has_key('strange_parts'):
		p_names = []
		for part in item['strange_parts']:
			p = def_item.objects.get(defindex=part, game_type=game_type)
			p_names.append(p.name)
		item['strange_parts'] = p_names

	# duplicated in other functions, not good
	if item.has_key('quality'):
		q = quality.objects.filter(defindex=item['quality'], game_type=game_type)
		if q.count() > 0:
			item['quality'] = q[0].name
		else:
			item['quality'] = 'A new and unknown quality. You\'d better contact webmaster'
			logger.error('Cannot find quality with id ' + str(item['quality']) + ' ' + game_type)

	if item.has_key('paint'):
		p = def_item.objects.get(defindex=item['paint'], game_type=game_type)
		item['paint'] = p.name

	if item.has_key('halloween_spell'):
		p_names = []
		for part in item['halloween_spell']:
			p = def_item.objects.get(defindex=part, game_type=game_type)
			p_names.append(p.name)
		item['halloween_spell'] = p_names

	if item.has_key('killstreak_type'):
		if item['killstreak_type'] == 1:
			item['killstreak_type'] = 'Specialized'
		elif item['killstreak_type'] == 2:
			item['killstreak_type'] = 'Professional'
		else:
			item['killstreak_type'] = 'Enabled'

	if item.has_key('ks_killstreaker'):
		ks = killstreaker.objects.filter(defindex=item['ks_killstreaker'])
		if ks.count() > 0:
			item['ks_killstreaker'] = ks[0].name

	if item.has_key('ks_sheen'):
		sh = sheen.objects.filter(defindex=item['ks_sheen'])
		if sh.count() > 0:
			item['ks_sheen'] = sh[0].name

	if item.has_key('quality_2'):
		q = quality.objects.filter(defindex=item['quality_2'])
		if q.count() > 0:
			item['quality_2'] = q[0].name
	return item

# works
def append_names_dota2(item, game_type):
	# duplicated in other functions, not good
	if item.has_key('quality'):
		q = quality.objects.filter(defindex=item['quality'], game_type=game_type)
		if q.count() > 0:
			item['quality'] = q[0].name
		else:
			item['quality'] = 'A new and unknown quality. You\'d better contact webmaster'
			logger.error('Cannot find quality with id ' + str(item['quality']) + ' ' + game_type)

	if item.has_key('gems'):
		g_names = []
		for gem in item['gems']:
			g = dota_gem.objects.get(defindex=gem)
			g_names.append(g.name)
		item['gems'] = g_names
	return item

# works
def append_names_csgo(item, game_type):
	# duplicated in other functions, not good
	if item.has_key('quality'):
		q = quality.objects.filter(defindex=item['quality'], game_type=game_type)
		if q.count() > 0:
			item['quality'] = q[0].name
		else:
			item['quality'] = 'A new and unknown quality. You\'d better contact webmaster'
			logger.error('Cannot find quality with id ' + str(item['quality']) + ' ' + game_type)

	if item.has_key('exterior'):
		q = exterior.objects.filter(defindex=item['exterior'])
		if q.count() > 0:
			item['exterior'] = q[0].name
		else:
			item['exterior'] = 'A new and unknown exterior. You\'d better contact webmaster'
			logger.error('Cannot find exterior with id ' + str(item['exterior']) + ' ' + game_type)

	if item.has_key('stickers'):
		s_names = []
		for sticker in item['stickers']:
			stick = def_item.objects.get(defindex=sticker)
			s_names.append(stick.name)
		item['stickers'] = s_names

	return item

# works
def filter_unusuals(data):
	results = {'unusuals':None}
	game_type = data['game_type']
	from get_numbers import return_int
	from connect import HatsdbClient
	client = HatsdbClient()
	connected = client.connect(game_type=game_type)
	if connected:
		page = 0
		LIST_OF_OWNERS = []
		query = build_query(data)
		if query.has_key('sort_by'):
			query.pop('sort_by')
		if query.has_key('page'):
			query.pop('page')
			page = return_int(data['page'])

		if return_int(data['sort_by']) == 1:
			sort_key = 'hours'
			direction = 1
		else:
			sort_key = '_id'
			direction = -1

		filter_results = client.find("unusuals", query, skip=(page-1)*50, limit=50, sort=sort_key, sort_order=direction)
		results['amount'] = client.get_count("unusuals", query)
		unusuals = list(filter_results)

		if unusuals:
			for hat in unusuals:
				LIST_OF_OWNERS.append(hat['owner'])
				hat['name'] = def_item.objects.get(game_type=game_type, defindex=hat['defindex']).name
				if game_type == 'tf2':
					e = effect.objects.filter(game_type=game_type, defindex=hat['effect'])
					if e.count() == 1:
						hat['effect'] = e[0].name
					else:
						hat['effect'] = 'unknown effect'
				if game_type == 'dota2':
					gem_names = ""
					if hat.has_key('gems'):
						for gem in hat['gems']:
							n = dota_gem.objects.get(defindex=gem).name 
							if ('Prismatic' in n) or ('Ethereal' in n):
								gem_names += n + '</br>'
						hat['gems'] = gem_names.rstrip('</br>')
				if game_type == 'csgo':
					hat['quality'] = quality.objects.get(defindex=hat['quality'], game_type=game_type).name
					hat['exterior'] = exterior.objects.get(defindex=hat['exterior']).name

			LIST_OF_OWNERS = list(set(LIST_OF_OWNERS))
			statuses = download_owners_info(LIST_OF_OWNERS)
			for hat in unusuals:
				if statuses:
					for status in statuses['response']['players']:
						if status['steamid'] == hat['owner']:
							hat['owner_status'] = resolve_text_status(status['personastate'])

			results['unusuals'] = unusuals

		if results['amount'] > 0 and page == 0:
			page = 1
		results['page'] = page
		results['q'] = query
		client.disconnect()
	return results

# works
def filter_australiums(data):
	results = {'items':None, 'amount':0}
	game_type = data['game_type']
	from get_numbers import return_int
	from connect import HatsdbClient
	client = HatsdbClient()
	connected = client.connect(game_type=game_type)
	if connected:
		if data.has_key('page'):
			page = return_int(data['page'])
		LIST_OF_OWNERS = []			

		if return_int(data['sort_by']) == 1:
			sort_key = 'hours'
			direction = 1
		else:
			sort_key = '_id'
			direction = -1

		australiums = []
		if data.has_key('defindex'):
			from get_numbers import return_int
			if return_int(data['defindex']) in [None,-1]:
				pass
			else:
				aussies = client.find(str(data['defindex']), {}, skip=(page-1)*50, limit=50, sort=sort_key, sort_order=direction)
				name = def_item.objects.get(defindex=data['defindex']).name
				australiums = list(aussies)
				for item in australiums:
					LIST_OF_OWNERS.append(item['owner'])
					item['name'] = name
				
				# remove duplicates
				LIST_OF_OWNERS = list(set(LIST_OF_OWNERS))
				statuses = download_owners_info(LIST_OF_OWNERS)
				for hat in australiums:
					if statuses:
						for status in statuses['response']['players']:
							if status['steamid'] == hat['owner']:
								hat['owner_status'] = resolve_text_status(status['personastate'])
			

				results['amount'] = client.get_count(str(data['defindex']), {})
				results['items'] = australiums

		if results['amount'] > 0 and page == 0:
			page = 1
		results['page'] = page

		results['q'] = data
		client.disconnect()
	return results

# works
def filter_tourneys(data):
	results = {'items':None}
	game_type = data['game_type']
	from get_numbers import return_int
	from connect import HatsdbClient
	client = HatsdbClient()
	connected = client.connect(game_type=game_type)
	if connected:
		page = 0
		LIST_OF_OWNERS = []
		query = build_query(data)
		if query.has_key('sort_by'):
			query.pop('sort_by')
		if query.has_key('page'):
			query.pop('page')
			page = return_int(data['page'])

		if query.has_key('tournament_info.player_sid'):
			if len(str(query['tournament_info.player_sid'])) != 17:
				query['tournament_info.player_sid'] = query['tournament_info.player_sid'] + int(settings.MAGIC_SID)

		if return_int(data['sort_by']) == 1:
			sort_key = 'hours'
			direction = 1
		else:
			sort_key = '_id'
			direction = -1

		filter_results = client.find("tournament", query, skip=(page-1)*50, limit=50, sort=sort_key, sort_order=direction)
		results['amount'] = client.get_count("tournament", query)
		items = list(filter_results)

		if items:
			for hat in items:
				LIST_OF_OWNERS.append(hat['owner'])
				hat['name'] = def_item.objects.get(game_type=game_type, defindex=hat['defindex']).name
				if game_type == 'dota2':
					if hat['tournament_info'].has_key('team1'):
						hat['tournament_info']['team1'] = dota_tournament_team.objects.get(id=hat['tournament_info']['team1']).name
					if hat['tournament_info'].has_key('team2'):	
						hat['tournament_info']['team2'] = dota_tournament_team.objects.get(id=hat['tournament_info']['team2']).name
					if hat['tournament_info'].has_key('event_id'):
						hat['tournament_info']['event'] = dota_tournament_event.objects.get(id=hat['tournament_info']['event_id']).name
				if game_type == 'csgo':
					if hat['tournament_info'].has_key('team1'):
						hat['tournament_info']['team1'] = csgo_tournament_team.objects.get(id=hat['tournament_info']['team1']).name
					if hat['tournament_info'].has_key('team2'):	
						hat['tournament_info']['team2'] = csgo_tournament_team.objects.get(id=hat['tournament_info']['team2']).name
					if hat['tournament_info'].has_key('event_id'):
						hat['tournament_info']['event_id'] = csgo_tournament_event.objects.get(id=hat['tournament_info']['event_id']).name
					if hat['tournament_info'].has_key('event_type'):	
						hat['tournament_info']['event_type'] = csgo_tournament_match.objects.get(id=hat['tournament_info']['event_type']).name
			LIST_OF_OWNERS = list(set(LIST_OF_OWNERS))
			statuses = download_owners_info(LIST_OF_OWNERS)
			for hat in items:
				if statuses:
					for status in statuses['response']['players']:
						if status['steamid'] == hat['owner']:
							hat['owner_status'] = resolve_text_status(status['personastate'])

			results['items'] = items

		if results['amount'] > 0 and page == 0:
			page = 1
		results['page'] = page
		results['q'] = query
		client.disconnect()
	return results



# #DOESNT work
# @csrf_protect
# def get_owner_info(request, owner_id):
# 	user = request.user
# 	user_details=""
# 	if user.is_authenticated():
# 		openid_user = UserOpenID.objects.get(user=user)
# 		user_details = userProfile.objects.get(user=openid_user)
# 		data = download_owners_info(owner_id)
# 		if data == 1:
# 			return 1
# 		data = data["response"]["players"][0]
# 		if data.has_key('gameid'):
# 			data["personastate"] = 'In-game: '+data['gameextrainfo'] #in-game!!
# 		if data['personastate'] == 0:
# 			data["lastlogoff"] = datetime.fromtimestamp(int(data["lastlogoff"])).strftime('%Y-%m-%d %H:%M:%S')
# 		data['personastate'] = resolve_text_status(data["personastate"])
# 		return data
# 	else:
# 		return 2



# #DOESNT work
# @csrf_protect
# def still_available(request,game_type, defindex, item_id):
# 	user = request.user
# 	user_details=""
# 	if user.is_authenticated():
# 		openid_user = UserOpenID.objects.get(user=user)
# 		user_details = userProfile.objects.get(user=openid_user)
# 		if game_type == 'tournament':
# 			game_type = 'dota2'
# 		database = select_proper_db(game_type)
# 		item_to_check = database[str(defindex)].find({"_id":int(item_id)})
# 		if item_to_check.count() > 0:
# 			item_to_check = item_to_check[0]
# 		else:
# 			item_to_check = None
# 		if item_to_check:
# 			item_owner = item_to_check['owner']
# 			from tasks import scan_task
# 			task = scan_task.apply_async((item_owner, False, False, False, game_type),queue="q1")
# 			from celery.exceptions import SoftTimeLimitExceeded
# 			try:
# 				task_result = task.get()
# 			except SoftTimeLimitExceeded:
# 				return 7
# 			else:
# 				if task_result:
# 					for item in task_result['items']:
# 						if item['original_id'] == int(item_id):
# 							return 4 				#yea, available
# 					return 5 						#nah, not item in bp
# 				else:
# 					return 6 						#private bp
# 		else:
# 			return 5
# 	else:
# 		return 2 							#not logged



#DOESNT work
def download_owners_info(owners):
	owner_id = ''
	if isinstance(owners, list):
		for o in owners:
			owner_id = owner_id + str(o) + ','
		owner_id = owner_id.rstrip(',')
	else:
		owner_id = owners
	user_info_url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=" + settings.API_KEY + "&steamids=" + owner_id
	try:
		data = urllib2.urlopen(user_info_url, timeout=20).read()
	except Exception,e:
		return None 			#probably network error
	else:
		data = json.loads(data)
	return data

# works
def resolve_text_status(status):
	if status == 0:			# 0 - Offline, 1 - Online, 2 - Busy, 3 - Away, 4 - Snooze, 5 - looking to trade, 6 - looking to play
		status = "Offline"
	if status == 1:
		status = "Online"
	if status == 2:
		status = "Busy"
	if status == 3:
		status = "Away"
	if status == 4:
		status = "Snooze"
	if status == 5:
		status = "Looking to trade"
	if status == 6:
		status = "Looking to play"
	return status

#DOESNT work
def get_player_hours(id64):
	retrieved_hours = ""
	try:
		link = 'http://steamcommunity.com/profiles/'+ str(id64) +'/games?tab=all&xml=1'
		time_data = urllib2.urlopen(link).read()
	except urllib2.URLError, e:
		return "?"
	else:
		pattern = r'<appID>440</appID>.*?<hoursOnRecord>(.*?)</hoursOnRecord>'	#hours in tf2
		time_data = ''.join(time_data.split())
		t = re.findall(pattern, time_data)
		retrieved_hours = t if (t!=[]) else '?'									#there were some errors
		return retrieved_hours

#------------------------------------------------

 # @csrf_protect
 # def get_default_items_detail(request, game_type, itemID, quality_id, item_count=100):
 # 	user = request.user
 # 	user_details=""
 # 	if user.is_authenticated():
 # 		openid_user = UserOpenID.objects.get(user=user)
 # 		user_details = userProfile.objects.get(user=openid_user)
 # 		items = {}
 # 		database = select_proper_db(game_type)
 
 # 		item_count_query = database[str(itemID)].find({"quality":int(quality_id)}).count()
 # 		if item_count_query >= 100:
 # 			item_count = randint(0, item_count_query-100)
 # 		else:
 # 			item_count = 0
 
 # 		query_items = database[str(itemID)].find({"quality":int(quality_id)}).skip(item_count).limit(100)
 # 		qual = quality.objects.filter(defindex=int(quality_id),game_type=game_type)[0]
 
 # 		if query_items.count() > 0:		#items with needed id/quality combination exist in db
 # 			unsorted_list = []
 # 			for item in query_items:
 # 				try:
 # 					item_owner = owners_db['owners'].find({"_id":item['owner']})
 # 				except Exception,e:
 # 					item_owner = ''
 # 				if item_owner.count() > 0:
 # 					item_owner = item_owner[0]
 # 					item['id'] = item['_id']
 # 					item['owner_ID'] = item_owner['_id']
 # 					item["is_f2p"] = item_owner["is_f2p"]
 # 					if game_type == "tf2":
 # 						item['hours'] = item_owner['tf2_hours']
 # 					else:
 # 						item['hours'] = item_owner['dota2_hours']
 
 # 					if (user_details.tf2_premium == False and game_type == 'tf2') or (user_details.dota2_premium == False and game_type == 'dota2'):
 # 						if item['hours'] < 300:
 # 							item['owner_ID'] = "---"
 # 							item['id'] = "---"
 # 					if qual.name == 'Unusual':
 # 						eff = effect.objects.filter(game_type=game_type, defindex=item['effect'])
 # 						if len(eff) > 0:
 # 							item['effect'] = eff[0].name
 # 						else:
 # 							item['effect'] = '???'
 # 					unsorted_list.append(item)
 # 			import operator
 # 			sorted_list = sorted(unsorted_list, key=operator.itemgetter('hours'))
 # 			all_items = {}
 # 			i=1
 # 			for r in sorted_list:			#to make list with numbers
 # 				all_items[i] = r
 # 				i+=1
 
 # 			items['sorted_list'] = all_items
 # 			items['qual'] = qual
 # 			return items
 # 		else:			#no items found
 # 			return 1
 # 	else:				#we are not logged in
 # 		return 2
 
 
 
 # def fix_errored_item(defindex, id, game_type):
 # 	database = select_proper_db(game_type,True)
 # 	owner_database = select_proper_db('owners',True)
 
 # 	item = database[str(defindex)].find({"_id":id})
 # 	key = game_type + '_hours'
 # 	unusual_db = None
 
 # 	if item.count() > 0:
 # 		item = item[0]
 # 		owner = owner_database['owners'].find({"_id":item['owner']})
 # 		if (item['quality'] == 5 and game_type == 'tf2') or ((item['quality'] == 3 or item['quality'] == 12) and game_type == 'dota2'):
 # 			unusual_db = select_proper_db('unusuals',True)
 # 			print 'this is unusual'
 # 			#save UNUSUALS along with items
 # 	else:
 # 		itemlist = open('rescan_these_faggots.txt', 'a')
 # 		itemlist.write('%s\t%s\t%s\twrong type\n'%(defindex,id,game_type))
 # 		itemlist.close()
 # 		return 0
 
 
 # 	if owner and owner.count() > 0:
 # 		owner = owner[0]
 # 	else:
 # 		itemlist = open('rescan_these_faggots.txt', 'a')
 # 		itemlist.write('%s\t%s\t%s\twrong type\n'%(defindex,id,game_type))
 # 		itemlist.close()
 # 		return 0
 # 	ok_key = False
 # 	if type(owner) == type(item):
 # 		if owner.has_key(key):
 # 			if item.has_key(key):
 # 				if owner[key] > item[key]:
 # 					item[key] = owner[key]
 # 					database[str(defindex)].save(item)
 # 					ok_key = True
 # 					print '1'
 # 				elif owner[key] < item[key]:
 # 					owner[key] = item[key]
 # 					owner_database['owners'].save(owner)
 # 					ok_key = True
 # 					print '2'
 # 				elif owner[key] < 0 and item[key] < 0:
 # 					itemlist = open('rescan_these_faggots.txt','a')
 # 					itemlist.write('%s\t%s\t%s\t%s\n'%(item['owner'], defindex, id, game_type))
 # 					itemlist.close()
 # 					print '3'
 # 			else:
 # 				item[key] = owner[key]
 # 				database[str(defindex)].save(item)
 # 				ok_key = True
 # 				print '4'
 # 		else:
 # 			if item.has_key(key):
 # 				owner[key] = item[key]
 # 				owner_database['owners'].save(owner)
 # 				ok_key = True
 # 				print '5'
 # 			else:
 # 				#--no hours at all
 # 				itemlist = open('rescan_these_faggots.txt','a')
 # 				itemlist.write('%s\t%s\t%s\t%s\n'%(item['owner'], defindex, id, game_type))
 # 				itemlist.close()
 # 				print '6'
 # 		if ok_key and unusual_db:
 # 			print 'saving unusual, ', item
 # 			unusual_db['unusuals'].save(item)
 # 			print '7'
 # 	else:
 # 		itemlist = open('rescan_these_faggots.txt', 'a')
 # 		itemlist.write('%s\t%s\t%s\twrong type\n'%(defindex,id,game_type))
 # 		itemlist.close()
 
 # def to_log(sss):
 # 	f = open('celery_fials.txt','a')
 # 	f.write(sss)
 # 	f.close()
#------------------------------------------------
