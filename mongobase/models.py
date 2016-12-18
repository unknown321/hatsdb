# -*- coding: utf-8 -*-
from django_openid_auth.models import UserOpenID, models
from django_openid_auth.signals import openid_login_complete
from django.dispatch import receiver
import  urllib2,json
from hatsdb import settings
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.signals import user_logged_in
from datetime import datetime

import logging

# Get an instance of a logger
logger = logging.getLogger('mongobase.data_collectors')

class rarity(models.Model):
	defindex 	= models.IntegerField()												#defindex
	name 		= models.CharField(max_length=32, default='Unknown rarity')			#rarity name, Dota2: common-uncommon, CSGO:restricted-consumer
	colour 		= models.CharField(max_length=7, default='#000000', blank=True)		#colour in rgb
	order 		= models.IntegerField()												#rarity number to make a cool list
	game_type 	= models.CharField(max_length=5, default='') 						#tf2, dota2, csgo
	def __unicode__(self):
		return unicode(self.name)

# class attribute(models.Model):
# 	name 		= models.CharField(max_length=120, default='') 					#"international tag"
# 	value 		= models.CharField(max_length=120, default='') 					#"2013"
# 	description = models.CharField(max_length=120, default='') 					#proper description
# 	game_type 	= models.CharField(max_length=5, default='') 					#tf2, dota2, csgo
# 	def __unicode__(self):
# 		return unicode(self.name)

class exterior(models.Model):
	#table for csgo only
	name 		= models.CharField(max_length=32, default='') 					#minimal-factory_new etc
	defindex    = models.IntegerField()
	def __unicode__(self):
		return unicode(self.name)

class quality(models.Model):
	defindex 	= models.IntegerField()
	name 		= models.CharField(max_length=32, default='??')						#genuine-unusual-unique
	colour		= models.CharField(max_length=7, default='#000000', blank=True) 	#colour in rgb
	game_type 	= models.CharField(max_length=5, blank=True)						#tf2, dota2, csgo
	def __unicode__(self):
		return unicode(self.name)

class effect(models.Model):
	defindex 	= models.IntegerField()
	name 		= models.CharField(max_length=32, default='Unknown effect')		#burning flames, burning anus
	game_type 	= models.CharField(max_length=5, blank=True)					#tf2, dota2, csgo
	def __unicode__(self):
		return unicode(self.name)

class hero_name(models.Model):
	name 		 = models.CharField(max_length=128, default='Unknown hero')		# (human_name) human name (antimage, tidehunter, Engineer)
	codename	 = models.CharField(max_length=128, default='Unknown hero')		# (name) non-human name (npc_hero_tidehunter, engineer)
	game_type	 = models.CharField(max_length=5, default='dota2')				#tf2, dota2, csgo
	image_url 	 = models.CharField(max_length=512, default='') 				# (image_url)
	def __unicode__(self):
		return unicode(self.name)

class def_item(models.Model):
	name 		 = models.CharField(max_length=512, default='Unknown item')		# (item_name) in schema, should be fine as market_hash_name too
	inv_name     = models.CharField(max_length=512, default='Unknown item')		# (name) in schema, used in catched inventories. Should be saved to be used in blacklisting. Regular names don't always have 'the' in their names
	defindex 	 = models.IntegerField()										# (defindex)
	type_name 	 = models.CharField(max_length=512, default='None')  			# (item_type_name), TF2: hat-badge-weapon, Dota2: meathook-daggers-hair, CSGO: pistol-shotgun-rifle
	image_url 	 = models.CharField(max_length=1024, default='') 				# (image_url)
	description  = models.CharField(max_length=1000, default='')				# (item_description)
	quality 	 = models.ForeignKey(quality, null=True)						# (item_quality) default item quality 
	used_by 	 = models.ManyToManyField(hero_name)							# CSGO: empty, Dota2: hero name via api(item_game.txt), TF2: class name (used_by_classes)
	# ++++++
	rarity 		 = models.ForeignKey(rarity, null=True)							#rarity, Dota2: item_game.txt, CSGO: market
	deflevel	 = models.IntegerField(default=0)								#TF2: min_ilevel, max_ilevel, others: empty
	game_type	 = models.CharField(max_length=5, default='tf2')				#tf2, dota2, csgo
	def __unicode__(self):
		return unicode(self.name)

class paint(models.Model):
	defindex 	 = models.IntegerField()
	colour		 = models.CharField(max_length=7, default='#000000')
	name 		 = models.CharField(max_length=100, default='??')
	game_type 	 = models.CharField(max_length=5, default='tf2')				#tf2, dota2, csgo
	def __unicode__(self):
		return unicode(self.name)

class origin(models.Model):
	defindex 	 = models.IntegerField()
	name 		 = models.CharField(max_length=50, default='??')
	game_type 	 = models.CharField(max_length=5, default='tf2')				#tf2, dota2, csgo

class sheen(models.Model):
	defindex 	 = models.IntegerField()
	name 		 = models.CharField(max_length=50, default='??')
	game_type 	 = models.CharField(max_length=5, default='tf2')				#tf2, dota2, csgo
	def __unicode__(self):
		return unicode(self.name)

class killstreaker(models.Model):
	defindex 	 = models.IntegerField()
	name 		 = models.CharField(max_length=50, default='??')
	game_type 	 = models.CharField(max_length=5, default='tf2')				#tf2, dota2, csgo
	def __unicode__(self):
		return unicode(self.name)

class strange_part(models.Model):
	defindex 	 = models.IntegerField()
	description	 = models.CharField(max_length=50, default='??')				#the text displayed after applying the part
	game_type 	 = models.CharField(max_length=5, default='tf2')				#tf2, dota2, csgo
	def __unicode__(self):
		return unicode(str(self.defindex) + ' ' + self.description)

class dota_gem(models.Model):
	defindex 	 = models.IntegerField()
	name	 	 = models.CharField(max_length=50, default='??')				
	def __unicode__(self):
		return unicode(str(self.defindex) + ' ' + self.name)

class dota_tournament_player(models.Model):
	nickname     = models.CharField(max_length=50, default='??')
	steam_id 	 = models.CharField(max_length=17,default='')
	def __unicode__(self):
		return unicode(str(self.steam_id) + ' ' + self.nickname)

class dota_tournament_team(models.Model):
	name 		 = models.CharField(max_length=50, default='??')
	image_url    = models.CharField(max_length=2048, default='??')
	def __unicode__(self):
		return unicode(self.name)

class dota_tournament_event(models.Model):
	defindex 	 = models.IntegerField()
	name 		 = models.CharField(max_length=50, default='??')
	strings		 = models.CharField(max_length=256, default='??')
	length 		 = models.IntegerField(default=4)
	def __unicode__(self):
		return unicode(self.name)

class dota_exceptional_recipe(models.Model):
	defindex 	 = models.IntegerField()
	name 		 = models.CharField(max_length=100, default='??')
	image_url 	 = models.CharField(max_length=2048, default='??')
	def __unicode__(self):
		return unicode(self.name)

class dota_tournament_item(models.Model):
	defindex 	 = models.IntegerField()
	fisrt_team 	 = models.ForeignKey(dota_tournament_team, related_name='first team')
	second_team	 = models.ForeignKey(dota_tournament_team, related_name='second team')
	event_type 	 = models.ForeignKey(dota_tournament_event)
	player_id    = models.ForeignKey(dota_tournament_player)
	date 		 = models.DateTimeField()
	match_id 	 = models.IntegerField()
	def __unicode__(self):
		return unicode(self.name)

# event name, eg DREAMHACK 2013
class csgo_tournament_event(models.Model):
	name = models.CharField(max_length=2048, default='unknown event')
	def __unicode__(self):
		return unicode(self.name)

# match type, eg GRAND FINAL
class csgo_tournament_match(models.Model):
	name = models.CharField(max_length=2048, default='unknown match type')
	def __unicode__(self):
		return unicode(self.name)

class csgo_tournament_team(models.Model):
	name = models.CharField(max_length=2048, default='unknown team')
	def __unicode__(self):
		return unicode(self.name)

class csgo_tournament_item(models.Model):
	defindex 	 = models.IntegerField()
	fisrt_team 	 = models.ForeignKey(csgo_tournament_team, related_name='first team')
	second_team	 = models.ForeignKey(csgo_tournament_team, related_name='second team')
	event_type 	 = models.ForeignKey(csgo_tournament_event)					# tourney
	match 		 = models.ForeignKey(csgo_tournament_match)					# finals-semifinals etc
	date 		 = models.DateTimeField()
	def __unicode__(self):
		return unicode(self.name)

class userProfile(models.Model):
	# This field is required.
	user = models.OneToOneField(UserOpenID)

	# Other fields here
	premium_tf2 = models.BooleanField(default=False)
	premium_dota2 = models.BooleanField(default=False)
	premium_csgo = models.BooleanField(default=False)
	donator = models.BooleanField(default=False)
	avatar_url = models.CharField(max_length=500,default='')
	nickname = models.CharField(max_length=500,default='broken authorization, contact webmaster')
	steamid = models.CharField(max_length=17,default='')
	blacklist_tf2 = models.TextField(default='')
	blacklist_dota2 = models.TextField(default='')
	blacklist_csgo = models.TextField(default='')
	def __unicode__(self):
		return self.nickname + ' ' + str(self.steamid)
	def is_premium(self, game_type):
		p = False
		if game_type == 'tf2' and self.premium_tf2:
			p = True
		if game_type == 'dota2' and self.premium_dota2:
			p = True
		if game_type == 'csgo' and self.premium_csgo:
			p = True
		return p

class old_premiums(models.Model):
	steamid = models.CharField(max_length=17,default='')
	def __unicode__(self):
		return self.steamid
		
def create_user_profile(sender, instance, created, **kwargs):
	userProfile.objects.create(user=instance)
	steam_id =  instance.claimed_id[-17:]
	a = 0
	nickname = 'broken authorization, contact webmaster'
	avatar = ''
	tf2_premium = False
	dota2_premium = False
	urlstring = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key="+settings.API_KEY+"&steamids="+steam_id
	while a<30:
		try:
			data = urllib2.urlopen(urlstring).read()
		except urllib2.URLError, e:
			a += 1
		else:
			user_data = json.loads(data)
			nickname = user_data['response']['players'][0]['personaname']
			avatar = user_data['response']['players'][0]['avatar']
			if len(old_prems.objects.filter(steamid=steam_id)) > 0:
				tf2_premium = True
				dota2_premium = True
				logger.info('creating profile with premium ' + str(steam_id) + ' ' + nickname)
				old_prems.objects.filter(steamid=steam_id).delete()
			logger.info('creating profile ' + str(steam_id) + ' ' + nickname)
			break
	userProfile.objects.filter(user=instance).update(steamid=steam_id, avatar_url=avatar, nickname=nickname, premium_tf2=tf2_premium, premium_dota2=dota2_premium)
	
post_save.connect(create_user_profile, sender=UserOpenID)


@receiver(openid_login_complete)
def update_profile(sender,**kwargs):
	profile = None
	try:
		steamid = kwargs['openid_response'].message.getArg('http://specs.openid.net/auth/2.0','claimed_id')
		profile = userProfile.objects.get(steamid=steamid[-17:])
	except Exception, e:
		pass
	else:
		a = 0
		nickname = profile.nickname
		avatar = profile.avatar_url
		urlstring = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key="+settings.API_KEY+"&steamids="+profile.steamid
		while a<30:
			try:
				data = urllib2.urlopen(urlstring).read()
			except urllib2.URLError, e:
				a += 1
			else:
				user_data = json.loads(data)
				nickname = user_data['response']['players'][0]['personaname']
				avatar = user_data['response']['players'][0]['avatar']
				break
		profile.avatar_url = avatar
		profile.nickname = nickname
		profile.save()

class real_stats(models.Model):
	last_changed = models.DateTimeField(default=datetime.now)

	tf2_items = models.IntegerField(default=0)
	tf2_unusuals = models.IntegerField(default=0)
	tf2_earbuds = models.IntegerField(default=0)
	tf2_bills = models.IntegerField(default=0)
	tf2_australiums = models.IntegerField(default=0)
	tf2_subscribers = models.IntegerField(default=0)

	dota2_items = models.IntegerField(default=0)
	dota2_unusuals = models.IntegerField(default=0)
	dota2_timebreakers = models.IntegerField(default=0)
	dota2_tournament = models.IntegerField(default=0)
	dota2_hooks = models.IntegerField(default=0)
	dota2_subscribers = models.IntegerField(default=0)

	csgo_items = models.IntegerField(default=0)
	csgo_knives = models.IntegerField(default=0)
	csgo_tournament = models.IntegerField(default=0)
	csgo_subscribers = models.IntegerField(default=0)

	users = models.IntegerField(default=0)
	def __unicode__(self):
		return unicode(self.last_changed)

class item_stats(models.Model):
	defindex = models.IntegerField()
	quality = models.IntegerField()
	count = models.IntegerField()
	game_type = models.CharField(max_length=10)
	price = models.FloatField(default=0)
	overall = models.IntegerField()

class pending_payment(models.Model):
	id = models.CharField(max_length=17, default='', primary_key=True)
	pend_tf2 = models.BooleanField(default=False)
	pend_dota2 = models.BooleanField(default=False)
	pend_csgo = models.BooleanField(default=False)
	pend_donation = models.BooleanField(default=False)

	def __unicode__(self):
		return self.id

	def add(self, game_type):
		if game_type == 'tf2':
			self.pend_tf2 = True
			self.pend_dota2 = False
			self.pend_csgo = False
			self.pend_donation = False
		elif game_type == 'dota2':
			self.pend_tf2 = False
			self.pend_dota2 = True
			self.pend_csgo = False
			self.pend_donation = False
		elif game_type == 'csgo':
			self.pend_tf2 = False
			self.pend_dota2 = False
			self.pend_csgo = True
			self.pend_donation = False
		else:
			self.pend_tf2 = False
			self.pend_dota2 = False
			self.pend_csgo = False
			self.pend_donation = True

class old_prems(models.Model):
	steamid = models.CharField(default='none', max_length=17)