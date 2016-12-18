import scanner, get_numbers, data_collectors, admin_functions
from hatsdb import settings
from mongobase.scanner import *
from django.template.loader import render_to_string
from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
from django.template import Context, loader, RequestContext
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
import re, urllib2, json, time

import logging
# Get an instance of a logger
logger = logging.getLogger('mongobase.data_collectors')

# works
@dajaxice_register
def scanner_results_ajax(request, steam_ids, marketable_check, uncraft_check, untrade_check, game_type):
	from celery.exceptions import SoftTimeLimitExceeded
	from data_collectors import convert_steam_id, get_blacklist, get_user_limit
	from views import is_logged
	user, openid_user, user_details = is_logged(request)

	tasks_ids = []
	if user.is_authenticated():
		startTime = datetime.now()

		blacklist = get_blacklist(user_details, game_type)
		USER_LIMIT = get_user_limit(user_details, game_type)

		if game_type not in settings.GAMES_LIST:
			render = 6 
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
				#too many players to scan
				render = '<div class="row"><div class="large-8 columns large-centered">\
				  <div class="panel"><center><h5>Too many players to scan!</h5></center></div>\
				  </div></div>'										
			marketable 	= True if marketable_check 	else False
			untrade = True if untrade_check else False
			uncraft = True if uncraft_check else False

			results_array = []
			tasks_array = []
			from tasks import scan_task
			countdown = 0
			for sid in id64_list[::4]:
				tasks_array.append(scan_task.apply_async((sid, game_type, marketable, uncraft, untrade, blacklist),queue="q1", expires=60, countdown=countdown))
				countdown = countdown + 8
			countdown = 2
			for sid in id64_list[1::4]:
				tasks_array.append(scan_task.apply_async((sid, game_type, marketable, uncraft, untrade, blacklist),queue="q2", expires=60, countdown=countdown))
				countdown = countdown + 8
			countdown = 4
			for sid in id64_list[2::4]:
				tasks_array.append(scan_task.apply_async((sid, game_type, marketable, uncraft, untrade, blacklist),queue="q3", expires=60, countdown=countdown))
				countdown = countdown + 8
			countdown = 6
			for sid in id64_list[3::4]:
				tasks_array.append(scan_task.apply_async((sid, game_type, marketable, uncraft, untrade, blacklist),queue="q4", expires=60, countdown=countdown))
				countdown = countdown + 8

			for task in tasks_array:
				tasks_ids.append(task.id)
		else:
			render = '<div class="row"><div class="large-8 columns large-centered">\
				  <div class="panel"><center><h5>Umm, can you please enter some ids in the box above?</h5></center></div>\
				  </div></div>'
	else:
		#not logged in
		render = '<div class="row"><div class="large-8 columns large-centered">\
				  <div class="panel"><center><h5>How about logging in?</h5></center></div>\
				  </div></div>'
	# else:
	# 	game_id = settings.APPS[game_type]
	# 	render = render_to_string('hatsdb/ajax/scanner_ajax.html', {"time":items["time"], "results":items["results"],
	# 															 "game_type":game_type, 'game_id':game_id,
	# 															 "timed_out":items['timed_out']},context_instance=RequestContext(request))
	dajax = Dajax()
	dajax.assign('#tasks', 'value', tasks_ids)
	dajax.script('$("#scan_button").text("Scan");\
	              $("#scan_button").removeAttr("disabled");\
	              $("#steam_ids").val("");\
				  check_for_results()')


	# dajax.assign('#scanner_results', 'innerHTML', render)
	# dajax.script('$(document).foundation();\
	# 			  $(function() {\
 #    				$("img.lazy").lazyload();\
	# 			  });\
	# 			 $("#scan_button").text("Scan");\
	# 			 $("#scan_button").removeAttr("disabled");\
	# 			 $("#steam_ids").val("");\
	# 			 stickyFooter()')
	return dajax.json()

# works
@dajaxice_register
def scan_friends_ajax(request, steam_ids, marketable_check, uncraft_check, untrade_check, game_type):
	from celery.exceptions import SoftTimeLimitExceeded
	from views import is_logged
	from data_collectors import convert_steam_id
	from tasks import friend_task
	from get_numbers import get_friends
	user, openid_user, user_details = is_logged(request)
	USER_LIMIT = settings.NONPREMIUM_LIMIT
	TIMED_OUT = 0
	tasks_ids = []
	game_id = settings.APPS[game_type]
	if user.is_authenticated():
		f = False
		if (user_details.premium_tf2 and game_type == 'tf2'):
			f = True
		if (user_details.premium_dota2 and game_type == 'dota2'):
			f = True
		if (user_details.premium_csgo and game_type == 'csgo'):
			f = True
		if not f:
			if not user_details.donator:
				dajax = Dajax()
				dajax.alert('You cannot use this feature, sorry')
				return dajax.json()

		id64_list = []
		# we are looking for STEAM_0:0:000000, U:1:0000000 and 76561197960265728
		id_list = re.findall(settings.SID64_PATTERN, steam_ids)\
				  + re.findall(settings.SID_PATTERN_NEW, steam_ids)\
				  + re.findall(settings.SID_PATTERN_OLD, steam_ids)		
				  	
		for id in id_list:
			i = convert_steam_id(id)
			id64_list.append(i)

	if len(id64_list) == 0:							
		# no ids in input
		render = '<div class="row"><div class="large-8 columns large-centered">\
				  <div class="panel"><center><h5>No friends here, reload the page.</h5></center></div>\
				  </div></div>'

	else:
		marketable 	= True if marketable_check 	else False
		untrade = True if untrade_check else False
		uncraft = True if uncraft_check else False

		real_friends = get_friends(user_details.steamid)
		if isinstance(real_friends, list):
			for i in id64_list:
				if str(i) not in real_friends:
					# logger.info(str(i))
					dajax = Dajax()
					dajax.alert('THESE ARE NOT YOUR FRIENDS')
					return dajax.json()
		else:
			dajax = Dajax()
			dajax.alert('Cannot get friends, reload the page')
			return dajax.json()

		results_array = []
		tasks_array = []
		blacklist = []
		countdown = 0
		for sid in id64_list[::4]:
			tasks_array.append(friend_task.apply_async((sid, game_type, marketable, uncraft, untrade, blacklist),queue="q1", expires=240, countdown=countdown))
			countdown = countdown +8
		countdown = 2					
		for sid in id64_list[1::4]:
			tasks_array.append(friend_task.apply_async((sid, game_type, marketable, uncraft, untrade, blacklist),queue="q2", expires=240, countdown=countdown))
			countdown = countdown +8
		countdown = 4	
		for sid in id64_list[2::4]:
			tasks_array.append(friend_task.apply_async((sid, game_type, marketable, uncraft, untrade, blacklist),queue="q3", expires=240, countdown=countdown))
			countdown = countdown +8
		countdown = 6	
		for sid in id64_list[3::4]:
			tasks_array.append(friend_task.apply_async((sid, game_type, marketable, uncraft, untrade, blacklist),queue="q4", expires=240, countdown=countdown))
			countdown = countdown +8
		countdown = 0	
	
		for task in tasks_array:
			tasks_ids.append(task.id)
	dajax = Dajax()
	dajax.assign('#tasks', 'value', tasks_ids)
	dajax.script('check_for_results()')
	return dajax.json()

# works, rename the function
# sends results of scanner one by one, uses task ids
@dajaxice_register
def send_data_ajax(request, task_id, game_type, task_type='friend'):
	from tasks import friend_task, scan_task
	if task_type == 'scanner':
		result = scan_task.AsyncResult(task_id)
	else:
		result = friend_task.AsyncResult(task_id)
	game_id = settings.APPS[game_type]
	task_result = None
	try:
		task_result = result.get()
	except Exception, e:
		render = 'expired'
	else:
		pass
	
	dajax = Dajax()
	render = render_to_string('hatsdb/ajax/scanner_friends_ajax.html', {"result":task_result, 
												 "game_type":game_type, 'game_id':game_id},context_instance=RequestContext(request))
	if task_type == 'scanner':
		dajax.append('#scanner_results', 'innerHTML', render)	
	else:
		dajax.prepend('#scanner_results', 'innerHTML', render)
	dajax.remove('#'+task_id)
	dajax.script('stickyFooter(); $("img.lazy").lazyload();')
	return dajax.json()

# works
# used to load names of defitems on blacklist page
@dajaxice_register
def load_names_ajax(request, text, game_type):
	from models import def_item
	defitems = def_item.objects.filter(name__icontains=text, game_type=game_type)
	render = render_to_string('hatsdb/ajax/blacklist_defitems_ajax.html', {"defitems":defitems},context_instance=RequestContext(request))
	dajax = Dajax()
	dajax.assign('#items', 'innerHTML', render)
	return dajax.json()

# works
@dajaxice_register
def save_blacklist_ajax(request, blacklist_items, game_type):
	from views import is_logged
	user, openid_user, user_details = is_logged(request)
	if user.is_authenticated():
		blacklist = []
		for item in blacklist_items.split(';'):
			if len(item) > 2:
				blacklist.append(item)

		blacklist = ';'.join(blacklist)
		if game_type == 'tf2':
			user_details.blacklist_tf2 = blacklist
		if game_type == 'dota2':
			user_details.blacklist_dota2 = blacklist
		if game_type == 'csgo':
			user_details.blacklist_csgo = blacklist
		user_details.save()

	dajax = Dajax()
	dajax.script("$('#save_button').html('<i class=\"fi-check\"></i> Saved')")
	return dajax.json()

# works
@dajaxice_register
def load_default_blacklist_ajax(request, game_type):
	from views import is_logged
	user, openid_user, user_details = is_logged(request)
	blacklist = ''
	if user.is_authenticated():
		from data_collectors import get_default_blacklist
		blacklist = get_default_blacklist(game_type)
	dajax = Dajax()
	dajax.assign('#blacklist', 'value', blacklist)
	return dajax.json()

# works
# used to load names of defitems on blacklist page
@dajaxice_register
def get_defitems_ajax(request, text, game_type):
	from models import def_item
	defitems = def_item.objects.filter(name__icontains=text, game_type=game_type)
	render = render_to_string('hatsdb/ajax/search_defitems_ajax.html', {"defitems":defitems},context_instance=RequestContext(request))
	dajax = Dajax()
	dajax.assign('#loaded_defitems', 'innerHTML', render)
	dajax.script('stickyFooter();')
	return dajax.json()

# works?
@dajaxice_register
def search_results_ajax(request, data):
	from data_collectors import search_results
	from views import is_logged
	user, openid_user, user_details = is_logged(request)
	if user.is_authenticated:
		game_type = data['game_type']
		results = search_results(request, data)
		# if data.has_key('skip'):
		# 	skip = {'next_page':0, 'prev_page': 0, 'to_add': 0}
		# 	if return_int(data['skip']) is None:
		# 		data['skip'] = 0
		# 	skip['next_page'] = return_int(data['skip']) + 20
		# 	skip['prev_page'] = return_int(data['skip']) - 20
		# 	if skip['prev_page'] < 0:
		# 		skip['prev_page'] = 0
		# 	skip['to_add'] = (skip['next_page'] + skip['prev_page'])/2
		# 	if skip['to_add'] == 10:
		# 		skip['to_add'] = 0
		# else:
		# 	data['skip'] = 0

	dajax = Dajax()
	render = render_to_string('hatsdb/ajax/search_results_ajax.html', {"results":results, 'game_type':game_type, 'user_details':user_details},context_instance=RequestContext(request))
	dajax.assign('#results', 'innerHTML', render)
	dajax.assign('#page','value',results['page'])
	dajax.script('stickyFooter()')
	return dajax.json()

# works
@dajaxice_register
def filter_unusuals_ajax(request, data):
	render = ""
	from views import is_logged
	user, openid_user, user_details = is_logged(request)
	if user.is_authenticated() and data.has_key('game_type'):
		if data['game_type'] in settings.APPS.keys():
			from data_collectors import filter_unusuals
			results = filter_unusuals(data)
			render = render_to_string('hatsdb/ajax/unusuals_'+data['game_type'] + '.html', 
									 {'user_details':user_details, 'data':results, 'game_type':data['game_type']},context_instance=RequestContext(request))
	dajax = Dajax()
	dajax.assign('#results_wrapper', 'innerHTML', render)
	dajax.assign('#page', 'value', results['page'])
	dajax.script('stickyFooter()')
	return dajax.json()

# works
@dajaxice_register
def filter_australiums_ajax(request, data):
	render = ""
	from views import is_logged
	user, openid_user, user_details = is_logged(request)
	if user.is_authenticated():
		data['game_type'] = 'tf2'
		from data_collectors import filter_australiums
		results = filter_australiums(data)
		render = render_to_string('hatsdb/ajax/australium_items.html', 
										{'user_details':user_details, 'results':results},context_instance=RequestContext(request))
	dajax = Dajax()
	dajax.assign('#results_wrapper', 'innerHTML', render)
	dajax.assign('#page','value', results['page'])
	dajax.script('stickyFooter()')
	return dajax.json()

# works
# used to load team names on tournaments page
@dajaxice_register
def get_team_names_ajax(request, text, game_type):
	from models import dota_tournament_team, csgo_tournament_team
	if game_type == 'csgo':
		defitems = csgo_tournament_team.objects.filter(name__icontains=text)
	else:
		defitems = dota_tournament_team.objects.filter(name__icontains=text)
	render = render_to_string('hatsdb/ajax/blacklist_defitems_ajax.html', {"defitems":defitems},context_instance=RequestContext(request))
	dajax = Dajax()
	dajax.assign('#teams', 'innerHTML', render)
	return dajax.json()

# works
# used to load teams on tournaments page
@dajaxice_register
def get_teams_ajax(request, text, game_type, team_number):
	from models import dota_tournament_team, csgo_tournament_team
	from get_numbers import return_int
	team_number = return_int(team_number)
	if game_type == 'csgo':
		defitems = csgo_tournament_team.objects.filter(name__icontains=text)
	else:
		defitems = dota_tournament_team.objects.filter(name__icontains=text)
	render = render_to_string('hatsdb/ajax/tournament_teams_ajax.html', {"defitems":defitems, 'team_number':team_number},context_instance=RequestContext(request))
	dajax = Dajax()
	dajax.assign('#loaded_defitems', 'innerHTML', render)
	dajax.script('stickyFooter();')
	return dajax.json()

# works
@dajaxice_register
def filter_tourneys_ajax(request, data):
	render = ""
	results = None
	from views import is_logged
	user, openid_user, user_details = is_logged(request)
	if user.is_authenticated() and data.has_key('game_type'):
		if data['game_type'] in ['dota2','csgo']:
			from data_collectors import filter_tourneys
			results = filter_tourneys(data)
			render = render_to_string('hatsdb/ajax/tournament_'+data['game_type'] + '.html', 
										 {'user_details':user_details, 'data':results, 'game_type':data['game_type']},context_instance=RequestContext(request))
	dajax = Dajax()
	dajax.assign('#results_wrapper', 'innerHTML', render)
	if results:
		dajax.assign('#page', 'value', results['page'])
	dajax.script('stickyFooter()')
	return dajax.json()

# works
@dajaxice_register
def find_user_ajax(request,steam_id):
	render = ""
	if request.user.is_superuser:
		from admin_functions import find_user
		results = find_user(request, steam_id)
		render = render_to_string('hatsdb/ajax/user_ajax.html', {"results":results},context_instance=RequestContext(request))
	dajax = Dajax()
	dajax.assign('#ajax_user', 'innerHTML', render)
	return dajax.json()

# works
@dajaxice_register
def save_user_ajax(request, steam_id, tf2_sub, dota2_sub, csgo_sub, donator):
	render = ""
	if request.user.is_superuser:
		from admin_functions import save_user
		results = save_user(request, steam_id,tf2_sub, dota2_sub, csgo_sub, donator)
		render = 'saved'
	dajax = Dajax()
	dajax.assign('#savebutton', 'innerHTML', render)
	return dajax.json()

# works
@dajaxice_register
def get_item_stats_ajax(request, defindex, game_type):
	render = ""
	stats = None
	try:
		stats = list(item_stats.objects.filter(defindex=defindex, game_type=game_type).order_by('count'))
	except Exception, e:
		render = ""
	else:
		for s in stats:
			if game_type == 'csgo':
				s.quality = exterior.objects.get(defindex=s.quality)
			else:
				s.quality = quality.objects.get(defindex=s.quality ,game_type=game_type)
	render = render_to_string('hatsdb/ajax/item_stats_ajax.html', {"stats":stats},context_instance=RequestContext(request))
	dajax = Dajax()
	dajax.assign('#quality_stats', 'innerHTML', render)
	return dajax.json()

@dajaxice_register
def buy_ajax(request, game_type):
	from views import is_logged
	user, openid_user, user_details = is_logged(request)
	render = ""
	donator = False
	if user.is_authenticated():
		payment, created = pending_payment.objects.get_or_create(id=user_details.steamid)
		if game_type in settings.APPS.keys():
			payment.add(game_type)
		else:
			payment.add('donator')
			donator = True
		payment.save()

		if donator:
			message = ""
		else:
			message = "Now you are ready to get premium! Add the bot to proceed: <a href='http://steamcommunity/profiles/' target='_blank'></a>"

		render = "<div class='large-12 columns'><div class='alert-box secondary'>" + message + "</div></div>"
	dajax = Dajax()
	if donator:
		dajax.script("$('.fi-check').show()")
	else:
		dajax.assign('#message', 'innerHTML', render)
	return dajax.json()



# #DOESNT work
# @dajaxice_register
# def owner_info_ajax(request, game_type, owner_id):
# 	from mongobase.data_collectors import get_owner_info
# 	results = get_owner_info(request, owner_id)
# 	if results == 1:		#network error
# 		render = '<tr><td colspan=10><div class="panel"><center><h5>Hmm, an error. Maybe Steam Community is down?</h5></center></div></td></tr>'
# 	elif results == 2:		#not logged in
# 		render = '<tr><td colspan=10><div class="panel"><center><h5>How about logging in?</h5></center></div></td></tr>'
# 	else:
# 		render = render_to_string('mongobase/owner_info_ajax.html', {"results":results},context_instance=RequestContext(request))

# 	dajax = Dajax()
# 	dajax.assign('#'+str(owner_id), 'innerHTML', render)
# 	return dajax.json()

# #DOESNT work
# @dajaxice_register
# def still_available_ajax(request, game_type, defindex, item_id):
# 	from mongobase.data_collectors import still_available
# 	results = still_available(request, game_type, defindex, item_id)
# 	render = results
# 	if results == 1:		#network error
# 		render = "<span class='has-tip tip-top noradius' title='Hmm, network error. Maybe Steam Community or item server is down?'><font color='#c60f13' size=5>&#9888;</font></span>"
# 	if results == 2:		#not logged in
# 		render = "<span class='has-tip tip-top noradius' title='You are not logged in, how could this happen?'><font color='#c60f13' size=5>&#9888;</font></span>"
# 	# if results == 3: 		#
# 	# 	render = 'db error'
# 	if results == 4:		#yea,exists
# 		render = "<font color='#5da423'>&#10004</font>"
# 	if results == 5:		#nope
# 		render = "<font color='#c60f13'>&#10008</font>"
# 	if results == 6:		#bp is private
# 		render = "<span class='has-tip tip-top noradius' title='This BP is private. You should add owner of this item and ask him if he still has it'><font color='#c60f13' size=5>&#9888;</font></span>"
# 	if results == 7:		#timeout
# 		render = "<div id="+ str(defindex) + " class=\"tiny button alert\" onclick=\"is_available(" + str(item_id) + "," + str(defindex) + ")\">Timeout</div>"
# 	dajax = Dajax()
# 	dajax.assign('#'+str(item_id), 'innerHTML', render)
# 	return dajax.json()

# #DOESNT work
# @dajaxice_register
# def filter_item_ajax(request, text, game_type):
# 	if len(text) > 0:
# 		try:
# 			items = list(def_item.objects.filter(name__iregex = text, game_type = game_type))
# 			if game_type == 'tf2':
# 				items += list(def_item.objects.filter(used_by__iregex = text, game_type = game_type))	
# 			if game_type == 'dota2':
# 				items += list(def_item.objects.filter(rarity__iregex = text, game_type = game_type))
# 		except Exception, e:
# 			render = ""
# 		else:
# 			render = render_to_string('mongobase/find_item_ajax.html', {"items":items},context_instance=RequestContext(request))
# 	else:
# 		render = ""
# 	dajax = Dajax()
# 	dajax.assign('#items', 'innerHTML', render)
# 	return dajax.json()



#------------admin------------
# #DOESNT work
# @dajaxice_register
# def update_db_ajax(request,game_type,cache):
# 	if request.user.is_superuser:
# 		from admin_functions import update_db
# 		results = update_db(game_type,cache)
# 		render = game_type +' DB updated! Items before: ' + str(results["items_before"]) + ", items after: " + str(results['items']) + "; qualities before: " +  str(results['qualities_before']) + ", qualities after: " + str(results['qualities']) +	"; effects before: " + str(results['effects_before']) + ", effects after: " + str(results['effects']) + "\n"
# 	else:
# 		render = ""
# 	dajax = Dajax()
# 	dajax.append('#update_log', 'value', render)
# 	return dajax.json()


#DOESNT work
# @dajaxice_register
# def stats_ajax(request,show_on_site):
# 	render = ""
# 	if request.user.is_superuser:
# 		from admin_functions import gather_stats
# 		results = gather_stats(show_on_site)
# 		render = render_to_string('mongobase/stats_ajax_template.html', {"stats":results},context_instance=RequestContext(request))
# 	else:
# 		render = ""
# 	dajax = Dajax()
# 	dajax.assign('#stats', 'innerHTML', render)
# 	return dajax.json()

#DOESNT work
# @dajaxice_register
# def load_defitems_ajax(request,game_type):
# 	render = ""
# 	if request.user.is_superuser:
# 		from data_collectors import get_defitems
# 		defitems = get_defitems(game_type)
# 		render = render_to_string('mongobase/defitems_ajax_template.html', {"defitems":defitems},context_instance=RequestContext(request))
# 	dajax = Dajax()
# 	dajax.assign('#results', 'innerHTML', render)
# 	return dajax.json()

# #DOESNT work
# @dajaxice_register
# def load_qualities_ajax(request,game_type):
# 	render = ""
# 	if request.user.is_superuser:
# 		from data_collectors import get_qualities
# 		qualities = get_qualities(game_type)
# 		render = render_to_string('mongobase/qualities_ajax_template.html', {"qualities":qualities},context_instance=RequestContext(request))
# 	dajax = Dajax()
# 	dajax.assign('#results', 'innerHTML', render)
# 	return dajax.json()

# #DOESNT work
# @dajaxice_register
# def load_effects_ajax(request,game_type):
# 	render = ""
# 	if request.user.is_superuser:
# 		from data_collectors import get_effects
# 		effects = get_effects(game_type)
# 		render = render_to_string('mongobase/effects_ajax_template.html', {"effects":effects},context_instance=RequestContext(request))
# 	dajax = Dajax()
# 	dajax.assign('#results', 'innerHTML', render)
# 	return dajax.json()

			
# @dajaxice_register
# def save_effect_ajax(request,defindex,game_type,show):
# 	render = ""
# 	if request.user.is_superuser:
# 		from admin_functions import save_effect
# 		result = save_effect(defindex, game_type, show)
# 		if result == 0:
# 			render = 'saved'
# 		else:
# 			render = 'error'
			
# 	dajax = Dajax()
# 	dajax.assign('#savebutton'+str(defindex), 'innerHTML', render)
# 	return dajax.json()

# @dajaxice_register
# def save_quality_ajax(request,defindex,game_type,show, colour):
# 	render = ""
# 	if request.user.is_superuser:
# 		from admin_functions import save_quality
# 		result = save_quality(defindex, game_type, show, colour)
# 		if result == 0:
# 			render = 'saved'
# 		else:
# 			render = 'error'
			
# 	dajax = Dajax()
# 	dajax.assign('#savebutton'+str(defindex), 'innerHTML', render)
# 	return dajax.json()


# @dajaxice_register
# def save_item_ajax(request,defindex,game_type,show):
# 	render = ""
# 	if request.user.is_superuser:
# 		from admin_functions import save_item
# 		result = save_item(defindex,game_type,show)
# 		if result == 0:
# 			render = 'saved'
# 		else:
# 			render = 'error'
			
# 	dajax = Dajax()
# 	dajax.assign('#savebutton'+str(defindex), 'innerHTML', render)
# 	return dajax.json()

# @dajaxice_register
# def log_ajax(request,log_date):
# 	render = ""
# 	if request.user.is_superuser:
# 		from admin_functions import read_log
# 		results = read_log('logs/daily_logs/' + log_date +'.log')
# 		render = render_to_string('mongobase/log_ajax_template.html', {"log":results},context_instance=RequestContext(request))
# 	else:
# 		render = ""
# 	dajax = Dajax()
# 	dajax.assign('#log', 'innerHTML', render)
# 	return dajax.json()


# @dajaxice_register
# def get_progress_ajax(request,progress_id):
# 	render = ""
# 	if request.user.is_authenticated:
# 		from data_collectors import get_progress
# #		progress = get_progress(progress_id)
# 		progress = 0
# 		dajax = Dajax()
# 		if progress == 2:					#progress not found
# 			render = '<div class="row"><div class="eight columns centered"><div class="panel"><center><h5>Something bad happened! Reload the page, it may help.</h5></center></div></div></div>'
# 			dajax.assign('#scanner_results', 'innerHTML', render)
# 		else:
# #render = str(progress)+"%"
# 			render = "12%"
# 			dajax.script('$(\'#progressbar\').width(\''+render+'\')')
# 	return dajax.json()

	
# @dajaxice_register
# def scan_friends_ajax(request,steam_id,game_type):
# 	render = ""
# 	results = scan_friends_forreal(request,steam_id,game_type)
# 	render = render_to_string('mongobase/scan_friends_ajax.html', {"results":results[0], "time":results[1], "lost_res":results[2], "game_type":results[3]},context_instance=RequestContext(request))
# 	dajax = Dajax()
# 	dajax.assign('#results', 'innerHTML', render)
# 	return dajax.json()


# @dajaxice_register
# def default_items_detail_ajax(request, game_type, item_id, quality_id):
# 	from mongobase.data_collectors import get_default_items_detail
# 	if len(quality_id) > 0:
# 		results = get_default_items_detail(request, game_type, item_id, quality_id)
# 	else:
# 		results = 3
# 	if results == 1:		#no items found
# 		render = '<div class="panel"><center><h5>We have no items with this quality.</h5></center></div>'
# 	elif results == 2:		#not logged in
# 		render = '<div class="panel"><center><h5>How about logging in?</h5></center></div>'
# 	elif results == 3:		#no quality specified
# 		render = '<div class="panel"><center><h5>Please select the quality first.</h5></center></div>'
# 	else:
# 		render = render_to_string('mongobase/default_items_ajax.html', {"all_items":results['sorted_list'], "quality":results['qual'],"game_type":game_type},context_instance=RequestContext(request))
# 	dajax = Dajax()
# 	dajax.assign('#results', 'innerHTML', render)
# 	return dajax.json()