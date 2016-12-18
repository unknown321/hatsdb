# -*- coding: utf-8 -*-
import urllib2, json, time
from models import *

#	               █           ▄                 
# ▄   ▄  ▄▄▄▄    ▄▄▄█   ▄▄▄   ▄▄█▄▄   ▄▄▄         
# █   █  █▀ ▀█  █▀ ▀█  ▀   █    █    █▀  █        
# █   █  █   █  █   █  ▄▀▀▀█    █    █▀▀▀▀        
# ▀▄▄▀█  ██▄█▀  ▀█▄██  ▀▄▄▀█    ▀▄▄  ▀█▄▄▀        
#        █                                        
#        ▀                                        


#notes:
# strange parts in tf2 have different description after application:
# "Kills while ubercharged" -> "Kills While Invuln bercharged"
# update_strange_parts method was created to fix that
# you have to find the proper description on market (advanced search - 'search in descriptions' box)
# and put it into the schemas/tf2/strange_parts.json file with defindex

# dota and tf2 have a lot of unused effects, which are removed in update_qualities method

# vdf_to_json was stolen from somewhere on the internet

# there are no proper quality colours for tf2 in schema, so we have update_quality_colours method
# all colours should be listed in corresponding file
# other games have colours in items_game.txt 

# update_rarities has the issue for csgo where rarities are placed in file, which has to be updated

# origins are not used and method stays for legacy purposes I guess

class PBar:
	def __init__(self, name='noname', max=1):
		from progressbar import Percentage, Bar, ETA, Counter, ProgressBar, RotatingMarker
		widgets = [name + ': ', Percentage(), ' ', Bar(marker=RotatingMarker()), ' ', ETA(), ' ', Counter()]
		self.bar = ProgressBar(widgets=widgets, maxval=max)
		return None
	def start(self):
		self.bar.start()
	def update(self, i):
		self.bar.update(i)
	def finish(self):
		if self.bar:
			self.bar.finish()

class QualityDoesntExist(Exception):
	pass

class MissingItemsGameFile(Exception):
	pass

class Outdated(Exception):
	pass

#---------------------------------------------------------------

def get_api_part(game_type):
	api_game_part = 'IEconItems_440'
	if game_type == 'tf2':							# tf2
		api_game_part = 'IEconItems_440'
	elif game_type == 'dota2':						# dota2
		api_game_part = 'IEconItems_570'
	elif game_type == 'csgo':						# csgo
		api_game_part = 'IEconItems_730'
	return api_game_part

def get_api_version(game_type):
	version = 'v0001'
	if game_type == 'tf2':							# tf2
		version = 'v0001'
	elif game_type == 'dota2':						# dota2
		version = 'v0001'
	elif game_type == 'csgo':						# csgo
		version = 'v2'
	return version

def vdf_to_json(vdf):
	import re
	vdf = re.sub('"[ \t]*"', '":"', vdf)
	vdf = re.sub('"\s+"', '","', vdf)
	vdf = re.sub('"\s+{', '":{', vdf)
	vdf = re.sub('}\s+"', '},"', vdf)
	vdf = '{%s}' % vdf
	b = json.loads(vdf)
	return b

def save_latest_schema(game_type, data):
	#saves latest_schema file
	latest_schema_file = open("schemas/"+ game_type + "/latest_schema.txt","w")
	latest_schema_file.write(data)
	latest_schema_file.close()

def get_schema(game_type, build_from_cache=False):
	from datetime import datetime
	api_key = ''
	if (build_from_cache == False):
		api_game_part = get_api_part(game_type)
		api_version   = get_api_version(game_type)
		try:
			data = urllib2.urlopen("http://api.steampowered.com/" + api_game_part + "/GetSchema/" + api_version + "/?language=en&key=" + api_key)
		except Exception, e:
			print e
		else:
			http_status = data.getcode()
		if http_status != 200:
			print "HTTP Error " + str(http_status) + ", reading from file"
			build_from_cache = True
			schema_file = open("schemas/" + game_type + "/latest_schema.txt","r")
			data = schema_file.read()
		else:
			data = data.read()
			schema_file = open("schemas/"+ game_type + "/" + (datetime.now()).strftime("%d-%m-%y") + "_schema.txt","w")
			schema_file.write(data)
			save_latest_schema(game_type,data)
	else:
		schema_file = open("schemas/" + game_type + "/latest_schema.txt","r")
		data = schema_file.read()
	schema_file.close() 				#careful with that
	return data

def get_items_game(game_type, schema):
	items_url = schema['result']['items_game_url']
	items_data = urllib2.urlopen(items_url)
	http_status = items_data.getcode()
	if http_status != 200:
		print "HTTP Error " + str(http_status) + ", reading from file"
	else:
		items = items_data.read()
		items_file = open("schemas/"+ game_type + "/items_game.txt","w")
		items_file.write(str(items))
		items_file.close()

#---------------------------------------------------------------

def update_effects(schema_effects, game_type):
	# update effects, mostly for dota-tf, removing all Attrib_5165156 effects in process
	effects_amount = 0
	if len(schema_effects) > 0:
		bar = PBar('Effects', len(schema_effects))
		bar.start()
		for schema_effect in schema_effects:
			if schema_effect['name'][:6] == 'Attrib':
				pass
			else:
				effect.objects.update_or_create(
					defindex=schema_effect['id'],
					game_type=game_type,
					defaults={
					"name": unicode(schema_effect['name'])
					})
				effects_amount += 1
				bar.update(effects_amount)
		bar.finish()
	return effects_amount

def update_qualities(schema_qualities, quality_names, game_type):
	# update qualities for all games PLUS updating colours for each quality in tf2
	qualities_amount = 0
	if len(schema_qualities) > 0:
		bar = PBar('Qualities', len(schema_qualities))
		# bar.start()
		for schema_quality in schema_qualities:
			check = quality.objects.filter(game_type=game_type, defindex=schema_qualities[schema_quality])
			quality.objects.update_or_create(
				defindex=schema_qualities[schema_quality],
				game_type=game_type,
				defaults={
				"name": quality_names[schema_quality]
				}
				)
			# a = quality_names[schema_quality]
			# print a, schema_qualities[schema_quality]
			# if len(a) == 1:
			# 	print ord(a)

			qualities_amount += 1
			# bar.update(qualities_amount)
		try:
			update_quality_colours(game_type)
		except QualityDoesntExist:
			print 'Outdated colours file, update by hand'
		else:
			pass
		# bar.finish()
	return qualities_amount

def update_quality_colours(game_type):
	# colours dont exist in items_game for tf2, time for kostyli
	if game_type == 'tf2':
		colours = (open("schemas/tf2/quality.json")).read()
		data = json.loads(colours)
		for q in data['qualities']:
			q_to_update = quality.objects.filter(game_type='tf2', defindex=data['qualities'][q]['defindex'])
			if len(q_to_update) > 0:
				q_to_update[0].colour = data['qualities'][q]['hexColor']
				q_to_update[0].save()
			else:
				raise QualityDoesntExist
	else:
		data = vdf_to_json( (open('schemas/'+ game_type +'/items_game.txt')).read() )
		for q in data['items_game']['qualities']:
			q_to_update = quality.objects.filter(game_type=game_type, defindex=int(data['items_game']['qualities'][q]['value']))
			if len(q_to_update) > 0:
				q_to_update[0].colour = data['items_game']['qualities'][q]['hexColor']
				q_to_update[0].save()
			else:
				raise QualityDoesntExist

def update_hero_names():
	#to get readable hero names from fucking HAND-MADE FILE
	data = json.loads( (open('schemas/dota2/heroes.json')).read() )
	for hero in data['result']['heroes']:
		new_hero = hero_name()
		new_hero.id = hero['id']
		new_hero.codename = hero['name']
		new_hero.name = hero['human_name']
		new_hero.game_type = hero['game_type']
		if new_hero.name!='All':
			new_hero.image_url = "http://media.steampowered.com/apps/dota2/images/heroes/"+ new_hero.codename[14:] + "_full.png"
		new_hero.save()

def update_sheens():
	#to get sheen names for tf2 from fucking HAND-MADE FILE
	data = json.loads( (open('schemas/tf2/sheens.json')).read() )
	for s in data['sheens']:
		obj, created = sheen.objects.update_or_create(
			defindex = int(s),
			name = data['sheens'][s]['name'],
			game_type = 'tf2')

def update_killstreakers():
	# to get killstreakers for tf2 from fucking HAND-MADE FILE
	data = json.loads( (open('schemas/tf2/killstreakers.json')).read() )
	for k in data['killstreakers']:
		obj, created = killstreaker.objects.update_or_create(
			defindex=int(k),
			name=data['killstreakers'][k]['name'],
			game_type = 'tf2')

def update_strange_parts():
	#used to get corresponding strings for strange parts
	#eg 'Strange Part: Kills While Explosive Jumping' -> 'Kills While Explosive-Jumping: 0'
	
	data = json.loads( (open('schemas/tf2/strange_parts.json')).read() )
	for p in data['strange_parts']:
		obj, created = strange_part.objects.update_or_create(
			defindex=int(p),
			description=data['strange_parts'][p]['description'],
			game_type = 'tf2')

def update_tournament_events_dota2():
	# used to get tournament events - fb, megakills etc
	# file is handmade
	data = json.loads( (open('schemas/dota2/events.json')).read() )
	for event in data['result']['events']:
		obj, created = dota_tournament_event.objects.update_or_create(
			defindex=int(event['defindex']),
			name=event['name'],
			defaults={
			"strings":event['strings'],
			"length":event['len']})

def update_rarities(game_type):
	#to get rarities and their colours for 'rarity' table
	rarities_amount = 0
	if game_type == 'tf2':
		pass
	elif game_type == 'dota2':
		data = vdf_to_json( (open('schemas/' + game_type + '/items_game.txt')).read() )
		for r_name in data['items_game']['rarities']:
			r = data['items_game']['rarities'][r_name]
			rarity.objects.update_or_create(
				defindex=r['value'],
				game_type=game_type,
				defaults={
				"name":unicode(r['loc_key'][7:]),
				"order":r['value'],
				"colour":data['items_game']['colors'][r['color']]['hex_color']
				}
				)
			rarities_amount += 1
	elif game_type == 'csgo':
		# KOSTYLI, impossible to parse from api. File is HAND-MADE
		rarities = (open("schemas/csgo/rarity.json")).read()
		data = json.loads(rarities)
		for r in data['rarities']:

			rarity.objects.update_or_create(
				defindex=data['rarities'][r]['defindex'],
				game_type=game_type,
				defaults={
				"name":unicode(data['rarities'][r]['name']),
				"order":data['rarities'][r]['defindex'],
				"colour":data['rarities'][r]['hexColor']
				}
				)
			rarities_amount += 1
	return rarities_amount

def update_defitems(schema_defitems, game_type):
	# updating defitems.
	defitems_amount = 0
	if len(schema_defitems) > 0:
		bar = PBar('Defitems', len(schema_defitems))
		bar.start()
		for item in schema_defitems:
			i, created = def_item.objects.update_or_create(
				defindex=item['defindex'],
				game_type=game_type,
				defaults={
				"name":unicode(item['item_name']),
				"inv_name":unicode(item['name']),
				"image_url": item['image_url'],
				"type_name": item['item_type_name'],
				"quality": quality.objects.get(defindex=item['item_quality'], game_type=game_type)
				}
				)
			if game_type == 'tf2':
				# deflevel
				if item.has_key('min_ilevel') and item.has_key('max_ilevel'):
					if item['min_ilevel'] == item['max_ilevel']:
						i.deflevel = item['min_ilevel']
						i.save()

			if item.has_key('item_description'):
				i.description = item['item_description']
				i.save()
			defitems_amount += 1
			bar.update(defitems_amount)
		bar.finish()
	return defitems_amount

def update_used_by(schema_defitems, game_type):
	#used by who? dota2 KOSTYLI edition
	bar = PBar('Used by', len(schema_defitems))
	bar.start()
	if game_type == 'dota2':
		data = vdf_to_json( (open('schemas/' + game_type + '/items_game.txt')).read() )
		for idx, item_defindex in enumerate(data['items_game']['items']):
			if data['items_game']['items'][item_defindex].has_key('used_by_heroes'):
				if type(data['items_game']['items'][item_defindex]['used_by_heroes']) == type({}):
					d_item = def_item.objects.filter(game_type=game_type, defindex=int(item_defindex))[0]
					for hero in data['items_game']['items'][item_defindex]['used_by_heroes'].keys():
						h = hero_name.objects.filter(game_type=game_type, codename=hero)
						if len(h) > 0:
							d_item.used_by.add(h[0])
						d_item.save()
			bar.update(idx)

	if game_type == 'csgo':
		pass
		# don't need this
		# for idx, d_item in enumerate(def_item.objects.filter(game_type='csgo')):
		# 	fraction = hero_name.objects.get(game_type=game_type,name='All')
		# 	d_item.used_by.add(fraction)
		# 	d_item.save()
		# 	bar.update(idx)

	if game_type == 'tf2':
		pass
		# for idx, item in enumerate(schema_defitems):
		# 	if item.has_key('used_by_classes'):
		# 		d_item = def_item.objects.get(game_type='tf2',defindex=int(item['defindex']))
		# 		for tf2_class in item['used_by_classes']:
		# 			h = hero_name.objects.filter(game_type=game_type, name=tf2_class)
		# 			if len(h) > 0:
		# 				d_item.used_by.add(h[0])
		# 				d_item.save()
		# 	bar.update(idx)
	bar.finish()

def update_origins(schema_origins, game_type):
	for new_origin in schema_origins:
		check = origin.objects.filter(game_type=game_type, defindex=new_origin['origin'])
		if len(check) > 0:
			o = check[0]
		else:
			o = origin()
		o.defindex = new_origin["origin"]
		o.name = new_origin['name']
		o.game_type = game_type		
		o.save()

def update_css(game_type):
	import settings
	css = open(settings.STATIC_ROOT + str(game_type) + '.css','w')
	for i in def_item.objects.filter(game_type=game_type):
		css.write("div[iid='" + str(i.defindex) + "'][class='" + str(game_type) + "image']{\n\tbackground: url(\"" + i.image_url + "\") no-repeat;\n}\n")
	css.close()

#-----------------game-specific---------------------------------

def update_dota_rarities():
	#to get rarity for every item
	data = vdf_to_json( (open('schemas/dota2/items_game.txt')).read() )
	items = data['items_game']['items']
	if len(items) > 0:
		bar = PBar('Dota rarities', len(items))
		bar.start()
		for idx, item_defindex in enumerate(items):
			if item_defindex == 'default':
				pass
			else:
				if items[item_defindex].has_key('item_rarity'):
					name = items[item_defindex]['item_rarity']
				else:
					name = 'common'
				item = def_item.objects.filter(game_type='dota2', defindex=item_defindex)
				if len(item) > 0:
					r = rarity.objects.filter(game_type='dota2', name=name)
					if len(r) > 0:
						item[0].rarity = r[0]
						item[0].save()
						bar.update(idx)
					else:
						raise Outdated
				else:
					raise Outdated
		bar.finish()

def update_paints(schema_defitems, game_type):
	# add images from tf2 wiki and colours from schema
	# without that all paints will have the same image
	if game_type == 'tf2':
		data = open('schemas/tf2/paints.json')
		paints = json.loads(data.read())
		for item in schema_defitems:
			if str(item['defindex']) in paints['paints'].keys():
				p = paints['paints'][str(item['defindex'])]
				d = def_item.objects.get(game_type=game_type, defindex=item['defindex'])
				d.type_name = 'Paint'
				d.image_url = p['url']
				d.save()
				n = paint.objects.filter(game_type=game_type, defindex=item['defindex'])
				if len(n) > 0:
					new_paint = n[0]
				else:
					new_paint = paint()
				new_paint.name = d.name
				new_paint.defindex = d.defindex
				for i in item['attributes']:
					if i['name'] == 'set item tint RGB':
						new_paint.colour = hex(int(i['value']))[2:]
				new_paint.game_type = game_type
				new_paint.save()

def update_exterior():
	# KOSTYLI, impossible to parse from api. File is HAND-MADE
	rarities = (open("schemas/csgo/exterior.json")).read()
	data = json.loads(rarities)
	for e in data['exteriors']:
		exterior.objects.update_or_create(
			defindex=data['exteriors'][e]['defindex'],
			defaults={
			"name":unicode(data['exteriors'][e]['name'])
			}
			)

#---------------------------------------------------------------

def update_db(game_type, build_from_cache=False):
	results = {}
	data = get_schema(game_type, build_from_cache)
	# data = unicode(data, errors='ignore')
	schema = json.loads(data)
	print 'Schema loaded'

	# download items_game.txt with rarities and stuff
	if build_from_cache == False:
		get_items_game(game_type, schema)

	results['items_before'] = def_item.objects.filter(game_type=game_type).count()
	results['qualities_before'] = quality.objects.filter(game_type=game_type).count()
	results['effects_before'] = effect.objects.filter(game_type=game_type).count()
	if game_type == 'tf2':
		results['s_parts_before'] = def_item.objects.filter(name__contains='Strange Part',game_type=game_type).count()
	print results

	print 'updating effects..'
	effects_amount = update_effects(schema['result']['attribute_controlled_attached_particles'], game_type)

	print 'updating qualities..'
	qualities_amount = update_qualities(schema['result']['qualities'], schema['result']['qualityNames'] , game_type)

	print 'updating origins..'
	update_origins(schema['result']['originNames'], game_type)

	print 'updating rarities..'
	update_rarities(game_type)

	print 'updating quality colours'
	update_quality_colours(game_type)

	print 'updating defitems..'
	defitems_amount = update_defitems(schema['result']['items'], game_type)

	print 'updating used by..'
	update_hero_names()
	update_used_by(schema['result']['items'], game_type)

	if game_type == 'tf2':
		print 'updating paints..'
		update_paints(schema['result']['items'], game_type)
		print 'updating sheens..'
		update_sheens()
		print 'updating killstreakers..'
		update_killstreakers()
		print 'updating strange part descriptions..'
		update_strange_parts()
		if def_item.objects.filter(name__contains='Strange Part',game_type=game_type).count() > results['s_parts_before']:
			print ("New strange parts were added to the game, you need to update "
					"schemas/tf2/strange_parts_descs.json and perform the update_db command "
					"again in order to be able to parse parts on strange items.")

	if game_type == 'dota2':
		print 'parsing items..'
		update_dota_rarities()
		update_tournament_events_dota2()

	if game_type == 'csgo':
		print 'updating exteriors..'
		update_exterior()
		quality.objects.update_or_create(
			name='★ StatTrak™',
			defindex=20,
			colour='#8650AC',
			game_type='csgo')

	results['items'] = defitems_amount
	results['qualities'] = qualities_amount
	results['effects'] = effects_amount

	print 'updating css..'
	update_css(game_type)
	return results

update_quality_colours.QualityDoesntExist = QualityDoesntExist
update_dota_rarities.Outdated = Outdated

#localization stuff, do not want

# if game_type == 'dota2':
# 	localization_url = 'https://raw.githubusercontent.com/dotabuff/d2vpk/master/dota/resource/dota_english.txt'
# elif game_type == 'tf2':
# 	localization_url = 'https://wiki.teamfortress.com/w/images/c/cf/Tf_english.txt'
# elif game_type == 'csgo':
# 	localization_url = 'https://wiki.teamfortress.com/w/images/c/cf/Tf_english.txt'
# loc_data = urllib2.urlopen(localization_url)
# http_status = items_data.getcode()
# if http_status != 200:
# 	print "HTTP Error " + str(http_status) + ", reading from file"
# else:
# 	items = items_data.read()
# 	items_file = open("schemas/"+ game_type + "/localization.txt","w")
# 	items_file.write(str(items))
# 	items_file.close()