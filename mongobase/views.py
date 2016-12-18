# -*- coding: utf-8 -*-
from models import *
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import get_object_or_404, render_to_response, render, redirect
from django.template import Context, loader, RequestContext
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime
import re, time, Queue, sys, os, itertools, pymongo, bson, urllib2

from loggingMiddleware import log_entry
# from connect import select_proper_db,database_connect
import json
# database_connect()
import logging

# Get an instance of a logger
logger = logging.getLogger('mongobase.data_collectors')


def is_logged(request):
	user = request.user
	user_details = ""
	openid_user = None
	if user.is_authenticated():
		try:
			openid_user = UserOpenID.objects.get(user=user)
			user_details = userProfile.objects.get(user=openid_user)
		except Exception, e:
			pass
		else:
			pass
	return user, openid_user, user_details

#-------------views go here--------------

# works
def index(request):
	user, openid_user, user_details = is_logged(request)
	return render_to_response('hatsdb/static/index.html',{'user':user,'user_details':user_details}, context_instance = RequestContext(request))

# works
def scanner(request, game_type='tf2'):
	user, openid_user, user_details = is_logged(request)
	return render_to_response('hatsdb/static/scanner.html',{'user':user,'user_details':user_details,
														    'game_type':game_type}, context_instance = RequestContext(request))			

# works
def friends(request, game_type):
	user, openid_user, user_details = is_logged(request)
	return render_to_response('hatsdb/static/friends.html',{'user':user,'user_details':user_details}, context_instance = RequestContext(request))

# works
def buy(request):
	user, openid_user, user_details = is_logged(request)
	return render_to_response('hatsdb/static/buy.html', {'user':user,'user_details':user_details}, context_instance = RequestContext(request))	

# works
def faq(request):
	user, openid_user, user_details = is_logged(request)
	return render_to_response('hatsdb/static/faq.html',{'user':user,'user_details':user_details}, context_instance = RequestContext(request))	

# works
def scan_friends(request, game_type):
	user, openid_user, user_details = is_logged(request)
	from get_numbers import get_friends
	friends = None
	if user_details:
		friends = get_friends(user_details.steamid)
		if not isinstance(friends,list):
			friends = []
	return render_to_response('hatsdb/static/friends.html', {"game_type":game_type,'user':user,'user_details':user_details, 
															"friends":friends}, context_instance = RequestContext(request))

# works
def blacklist(request):
	user, openid_user, user_details = is_logged(request)
	return render_to_response('hatsdb/static/blacklist.html',{'user':user, 'user_details':user_details}, 
															   context_instance = RequestContext(request))		
# works
def search(request, game_type):
	user, openid_user, user_details = is_logged(request)
	if user.is_authenticated():
		data = {}
		if game_type == 'tf2':
			data['strange_parts'] = []
			for sp in strange_part.objects.all():
				data['strange_parts'].append({'defindex':sp.defindex, 'name':def_item.objects.get(defindex=sp.defindex, game_type=game_type)})	
			data['paints'] = paint.objects.filter(game_type = game_type)
			data['sheens'] = sheen.objects.all()
			data['killstreakers'] = killstreaker.objects.all()
			data['effects'] = effect.objects.filter(game_type = game_type)
		if game_type == 'dota2':
			data['gems'] = dota_gem.objects.order_by('name').all()
		if game_type == 'csgo':
			data['stickers'] = def_item.objects.filter(name__startswith='Sticker |', game_type='csgo').order_by('name')
			data['exteriors'] = exterior.objects.all()
		qualities = quality.objects.filter(game_type = game_type)
		
		return render_to_response('hatsdb/static/search.html', {'user': user, 'data':data, 'qualities': qualities, 
															'game_type': game_type, 'user_details':user_details}, context_instance = RequestContext(request))
	else:
		return render_to_response('hatsdb/static/search.html',{'user':user, 'user_details':user_details, "game_type":game_type}, context_instance = RequestContext(request))			

# works
def unusuals(request, game_type):
	data = None
	user, openid_user, user_details = is_logged(request)
	if user.is_authenticated():
		LIST_OF_OWNERS = []
		data = {'unusuals':None}
		from connect import HatsdbClient
		client = HatsdbClient()
		connected = client.connect(game_type=game_type)
		if connected:
			if game_type == 'tf2':
				data['effects'] = effect.objects.filter(game_type=game_type)
			elif game_type == 'dota2':
				data['gems'] = list(dota_gem.objects.filter(name__startswith='Ethereal'))
				data['gems'] += list(dota_gem.objects.filter(name__startswith='Prismatic'))
			else:
				data['exteriors'] = exterior.objects.all()

			unusuals = list(client.find('unusuals',{},skip=0,limit=50,sort='_id',sort_order=-1))
			
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

				from data_collectors import download_owners_info, resolve_text_status
				# remove duplicates
				LIST_OF_OWNERS = list(set(LIST_OF_OWNERS))
				statuses = download_owners_info(LIST_OF_OWNERS)
				for hat in unusuals:
					if statuses:
						for status in statuses['response']['players']:
							if status['steamid'] == hat['owner']:
								hat['owner_status'] = resolve_text_status(status['personastate'])
				data['unusuals'] = unusuals
				data['page'] = 1
				data['amount'] = client.get_count('unusuals',{})
	return render_to_response('hatsdb/static/unusuals.html',{'user':user,'user_details':user_details,
															 "data":data,"game_type":game_type}, context_instance = RequestContext(request))	

#works
def australium(request):
	user, openid_user, user_details = is_logged(request)
	results = {}
	LIST_OF_OWNERS = []
	items = []
	if user.is_authenticated():
		aussies = list(def_item.objects.filter(game_type='tf2',name__startswith='Australium').exclude(name='Australium Gold').order_by('name'))
		amount = 0
		from connect import HatsdbClient
		client = HatsdbClient()
		connected = client.connect(game_type='tf2')
		if connected:
			for a in aussies:
				items += client.find(str(a.defindex),{}, limit=50, sort='_id')
				amount += client.get_count(str(a.defindex),{})

			from operator import itemgetter
			items = sorted(items, key=itemgetter('_id'), reverse=True )[:50]
			for item in items:
				item['name'] = def_item.objects.get(game_type='tf2',defindex=item['defindex']).name
				LIST_OF_OWNERS.append(item['owner'])

			LIST_OF_OWNERS = list(set(LIST_OF_OWNERS))
			from data_collectors import download_owners_info, resolve_text_status
			statuses = download_owners_info(LIST_OF_OWNERS)
			for hat in items:
				if statuses:
					for status in statuses['response']['players']:
						if status['steamid'] == hat['owner']:
							hat['owner_status'] = resolve_text_status(status['personastate'])
		results['items'] = items
		results['page'] = 1
		results['amount'] = amount
	return render_to_response('hatsdb/static/australium.html', {'results':results, 'user':user, 'user_details':user_details})

#should work
def tournament(request, game_type):
	data = None
	user, openid_user, user_details = is_logged(request)
	if user.is_authenticated():
		LIST_OF_OWNERS = []
		data = {'items':None}
		connected = False
		from connect import HatsdbClient
		client = HatsdbClient()
		if game_type in ['dota2', 'csgo']:
			connected = client.connect(game_type=game_type)
		if connected:
			if game_type == 'dota2':
				data['players'] = list(dota_tournament_player.objects.all())
				data['teams'] = list(dota_tournament_team.objects.all())
				data['events'] = list(dota_tournament_event.objects.all())
			else:
				data['teams'] = list(csgo_tournament_team.objects.all())
				data['matches'] = list(csgo_tournament_match.objects.all())
				data['events'] = list(csgo_tournament_event.objects.all())

			items = list(client.find('tournament', {} , skip=0, limit=50,sort='_id', sort_order=-1))
			
			if items:
				for hat in items:
					LIST_OF_OWNERS.append(hat['owner'])
					hat['name'] = def_item.objects.get(game_type=game_type, defindex=hat['defindex']).name
					if game_type == 'dota2':
						if hat['tournament_info'].has_key('team1'):
							if hat['tournament_info']['team1']:
								hat['tournament_info']['team1'] = dota_tournament_team.objects.get(id=hat['tournament_info']['team1'])
						if hat['tournament_info'].has_key('team2'):
							if hat['tournament_info']['team2']:
								hat['tournament_info']['team2'] = dota_tournament_team.objects.get(id=hat['tournament_info']['team2'])
						if hat['tournament_info'].has_key('event_id'):
							if hat['tournament_info']['event_id']:
								hat['tournament_info']['event'] = dota_tournament_event.objects.get(id=hat['tournament_info']['event_id'])

					if game_type == 'csgo':
						if hat['tournament_info'].has_key('team1'):
							if hat['tournament_info']['team1']:
								hat['tournament_info']['team1'] = csgo_tournament_team.objects.get(id=hat['tournament_info']['team1'])
						if hat['tournament_info'].has_key('team2'):
							if hat['tournament_info']['team2']:
								hat['tournament_info']['team2'] = csgo_tournament_team.objects.get(id=hat['tournament_info']['team2']).name
						if hat['tournament_info'].has_key('event_id'):
							if hat['tournament_info']['event_id']:
								hat['tournament_info']['event_id'] = csgo_tournament_event.objects.get(id=hat['tournament_info']['event_id']).name
						if hat['tournament_info'].has_key('event_type'):
							if hat['tournament_info']['event_type']:
								hat['tournament_info']['event_type'] = csgo_tournament_match.objects.get(id=hat['tournament_info']['event_type']).name

				from data_collectors import download_owners_info, resolve_text_status
				# remove duplicates
				LIST_OF_OWNERS = list(set(LIST_OF_OWNERS))
				statuses = download_owners_info(LIST_OF_OWNERS)
				for hat in items:
					if statuses:
						for status in statuses['response']['players']:
							if status['steamid'] == hat['owner']:
								hat['owner_status'] = resolve_text_status(status['personastate'])
				data['items'] = items
				data['page'] = 1
				data['amount'] = client.get_count('tournament_'+game_type,{})
	return render_to_response('hatsdb/static/tournament.html',{'user':user,'user_details':user_details,
															 "data":data,"game_type":game_type}, context_instance = RequestContext(request))



def stats(request):
	user, openid_user, user_details = is_logged(request)
	stats = real_stats.objects.all().order_by('last_changed')[0]
	return render_to_response('hatsdb/static/stats.html', {'user':user,'user_details':user_details,"stats":stats}, context_instance = RequestContext(request))	

def google(request):
	return render_to_response('.html', context_instance = RequestContext(request))	

def admin_v2(request):
	if request.user.is_superuser:
		user, openid_user, user_details = is_logged(request)
		return render_to_response('hatsdb/static/admin.html',{'user':user,'user_details':user_details}, context_instance = RequestContext(request))	
	else:
		return render_to_response('404.html')

# works
def logout(request):
	from django.contrib.auth import logout
	logout(request)
	return HttpResponseRedirect(request.GET.get('redirect', '/'))

# works
def is_premium(user_details, game_type):
	p = False
	if game_type == 'tf2' and user_details.premium_tf2:
		p = True
	if game_type == 'dota2' and user_details.premium_dota2:
		p = True
	if game_type == 'csgo' and user_details.premium_csgo:
		p = True
	return p

# def show_new_items(request):
# 	user = request.user
# 	user_details=""
# 	if user.is_authenticated():
# 		openid_user = UserOpenID.objects.get(user=user)
# 		user_details = userProfile.objects.get(user=openid_user)
# 	tf_items = def_item.objects.filter(game_type='tf2',is_new=True).order_by('name')
# 	dota_items = def_item.objects.filter(game_type='dota2',is_new=True).order_by('name')
# 	return render_to_response('hatsdb/static/new_items.html', {'tf_items': tf_items, 'dota_items': dota_items, 'user':user, 'user_details':user_details})


# def salvaged(request):
# 	crates = []
# 	user, openid_user, user_details = is_logged(request)
# 	if user.is_authenticated():
# 		from connect import HatsdbClient
# 		client = HatsdbClient()
# 		connected = client.connect('tf2', settings.AUTH_R['login'], settings.AUTH_R['password'])
# 		crates = list(client.find('5068',{}, sort='_id', limit=50))
# 		crates += list(client.find('5660',{}, sort='_id', limit=50))
# 		if crates:
# 			from operator import itemgetter
# 			crates = sorted(crates, key=itemgetter('_id'), reverse=True )
# 			for crate in crates:
# 				crate['name'] = def_item.objects.filter(game_type='tf2',defindex=crate['defindex'])[0].name
# 				LIST_OF_OWNERS.append(crate['owner'])
# 	return render_to_response('hatsdb/static/salvaged.html',{'user':user,'user_details':user_details, 'crates':crates, 'game_type':'tf2'}, context_instance = RequestContext(request))	


# def test_view(request):
# 	user, openid_user, user_details = is_logged(request)
# 	f = open('/tmp/570','r')
# 	j = json.loads(f.read())
# 	f.close()
# 	t = {}
	
# 	for i in j['rgInventory']:
# 		itemid = j['rgInventory'][i]['classid'] + '_' + j['rgInventory'][i]['instanceid']
# 		item = j['rgDescriptions'][itemid]
# 		item_rarity = 'Common'
# 		for tag in item['tags']:
# 			if tag['category_name'] == 'Rarity':
# 				item_rarity = tag['name']
# 				break
# 		if t.has_key(item_rarity):
# 			t[item_rarity].append(item)
# 		else:
# 			t[item_rarity] = []
# 			t[item_rarity].append(item)
# 	# ppp = sorted(j['rgDescriptions'].iteritems(), key=lambda x__getitem__('name'): x[1]['tags'][1]['category']=='Rarity')
# 	return render_to_response('hatsdb/static/testpage.html',{'user':user,'user_details':user_details, 'j':t}, context_instance = RequestContext(request))

# def test_view2(request):
# 	user, openid_user, user_details = is_logged(request)
# 	t = None
# 	# from data_collectors import save_items
# 	# items = save_items()
	
# 	# f = open('/tmp/730','r')
# 	# j = json.loads(f.read())
# 	# f.close()
# 	# t = {}

# 	# for i in j['rgInventory']:
# 	# 	itemid = j['rgInventory'][i]['classid'] + '_' + j['rgInventory'][i]['instanceid']
# 	# 	item = j['rgDescriptions'][itemid]
# 	# 	for saved_item in items:
# 	# 		if saved_item['id'] == j['rgInventory'][i]['id']:
# 	# 			item['saved'] = saved_item
# 	# 			q = quality.objects.get(defindex=saved_item['quality'], game_type='csgo')
# 	# 			d = def_item.objects.get(defindex=saved_item['defindex'], game_type='csgo')
# 	# 			item['quality_name'] = q.name
# 	# 			if q.name != 'Normal':
# 	# 				item['saved_name'] = q.name + ' ' + d.name
# 	# 			else:
# 	# 				item['saved_name'] = d.name
# 	# 	item_rarity = 'Common'
# 	# 	for tag in item['tags']:
# 	# 		if tag['category_name'] == 'Rarity':
# 	# 			item_rarity = tag['name']
# 	# 			break
# 	# 	if t.has_key(item_rarity):
# 	# 		t[item_rarity].append(item)
# 	# 	else:
# 	# 		t[item_rarity] = []
# 	# 		t[item_rarity].append(item)
# 	# ppp = sorted(j['rgDescriptions'].iteritems(), key=lambda x__getitem__('name'): x[1]['tags'][1]['category']=='Rarity')
# 	return render_to_response('hatsdb/static/testpage2.html',{'user':user,'user_details':user_details, 'j':t}, context_instance = RequestContext(request))


# def testpage(request, game_type='tf2'):
# 	user = request.user
# 	user_details=""
# 	LIST_OF_OWNERS = []

# 	from celery.exceptions import TimeLimitExceeded

# 	from tasks import cl
# 	tasks_array = []
# 	results_array = []
# 	from data_collectors import to_log
# 	for sid in range(1,20):
# 		tasks_array.append(cl.apply_async((),queue="q1",expires=3))
# 	for task in tasks_array:
# 		try:
# 			task_result = task.get()
# 		except TimeLimitExceeded:
# 			to_log('time limit\n')
# 		else:
# 			results_array.append(task_result)

# 	if user.is_authenticated():
# 		openid_user = UserOpenID.objects.get(user=user)
# 		user_details = userProfile.objects.get(user=openid_user)
# 		unusuals = None
# 		db = select_proper_db('unusuals')
# 		if user_details.tf2_premium and game_type == 'tf2':
# 			unusuals = list(db['unusuals'].find({'game_type':game_type}).sort("_id",-1).limit(50))
# 		if user_details.dota2_premium and game_type == 'dota2':
# 			unusuals = list(db['unusuals'].find({'game_type':game_type,'quality':3}).sort("_id",-1).limit(50))
#                 if user_details.dota2_premium and game_type == 'tournament':
#                         unusuals = list(db['unusuals'].find({'game_type':'dota2','quality':12}).sort("_id",-1).limit(50))
# 		if unusuals:
# 			if admin_stuff.objects.get(id=1).database_status:
# 				owners = select_proper_db('owners')
# 			for un in unusuals:
# 				un['id'] = un["_id"]
# 				if admin_stuff.objects.get(id=1).database_status:
# 					tmp_owner = owners['owners'].find({"_id":un['owner']})
# 				else:
# 					tmp_owner = None
# 					un['owner'] = {"id":un['owner']}
# 					un['owner']['hours'] = '???'

# 				if tmp_owner:
# 					if tmp_owner.count() > 0 :
# 						un['owner'] = tmp_owner[0]
# 						LIST_OF_OWNERS.append(tmp_owner[0]['_id'])
# 						if game_type == 'tf2':
# 							un['owner']['hours'] = un['owner']['tf2_hours']
# 						else:
# 							un['owner']['hours'] = un['owner']['dota2_hours']
# 						un['owner']['id'] = un['owner']['_id']
# 					else:
# 						un['owner'] = {"id":un['owner']}
# 						un['owner']['hours'] = '???'


# 				if un.has_key('effect') and game_type != 'tournament' :
# 					if un['effect'] != -1:
# 						un['effect'] = effect.objects.filter(game_type=game_type,defindex=un['effect'])
# 						if len(un['effect']) > 0:
# 							un['effect'] = un['effect'][0].name
# 						else:
# 							un['effect'] = '???'
# 				else:
# 					un['effect'] = '???'
# 				if game_type != 'tournament':
# 					un['name'] = def_item.objects.filter(game_type=game_type,defindex=un['defindex'])[0].name
# 					un['image_url'] = def_item.objects.filter(game_type=game_type,defindex=un['defindex'])[0].image_url
# 				else:
# 					un['name'] = def_item.objects.filter(game_type='dota2',defindex=un['defindex'])[0].name
# 					un['image_url'] = def_item.objects.filter(game_type='dota2',defindex=un['defindex'])[0].image_url
# 			effects = effect.objects.filter(game_type=game_type, show_on_site=True)
# 			from data_collectors import download_owners_info, resolve_text_status
# 			LIST_OF_OWNERS = list(set(LIST_OF_OWNERS))
# 			statuses = download_owners_info(LIST_OF_OWNERS)
# 			for u in unusuals:
# 				for s in statuses['response']['players']:
# 					if s['steamid'] == u['owner']['id']:
# 						u['owner']['status'] = data_collectors.resolve_text_status(s['personastate'])
# 			return render_to_response('hatsdb/static/testpage.html',{'user':user,'user_details':user_details,"game_type":game_type, 'unusuals':unusuals, "effects":effects}, context_instance = RequestContext(request))	
# 	return render_to_response('hatsdb/static/testpage.html',{'task':results_array,'user':user,'user_details':user_details,"game_type":game_type}, context_instance = RequestContext(request))	




# def secret_page(request):
# 	user = request.user
# 	user_details=""
# 	if user.is_authenticated():
# 		openid_user = UserOpenID.objects.get(user=user)
# 		user_details = userProfile.objects.get(user=openid_user)
# 		steam_id = openid_user.claimed_id[-17:]
# 		return render_to_response('405.html',{'user':user,'user_details':user_details},context_instance = RequestContext(request))
# 	else:
# 		return render_to_response('404.html')
