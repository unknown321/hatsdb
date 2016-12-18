from django.http import HttpResponse
from django.core.files import File
from django_openid_auth.models import UserOpenID, models, User
from mongobase.models import userProfile
from datetime import datetime

class log_entry:
	def __init__(self, time, ip, steam_id, nickname, user_agent, request_string, url, subscription):
		self.time = datetime.strptime(time,"%d/%m/%y %H:%M:%S")
		self.ip = ip
		self.steam_id = steam_id
		self.nickname = nickname
		self.user_agent = user_agent
		self.request_string = request_string
		self.url = url
		if isinstance(subscription,str):
			if subscription == "True":
				self.subscription = True
			else:
				self.subscription = False
		else:
			self.subscription = subscription

	def __str__(self):
		try:
			self.nickname.decode('utf-8')
		except Exception, e:
			self.nickname = 'cyrillic characters guy'
		else:
			pass
		s = (self.time).strftime("%d/%m/%y %H:%M:%S") + "\t" + self.ip + "\t" + self.steam_id + "\t" + self.nickname + "\t" + self.user_agent + "\t" + self.request_string + "\t" + self.url + "\t" + str(self.subscription) + "\t"
		return s

class loggingMiddleware:
	def process_request(self, request):
		today = "logs/daily_logs/" + (datetime.now()).strftime("%d-%m-%y") + '.log'
		myfile = open(today,'a')
		steam_id = "unregistered"
		nickname = "unregistered"
		subscription = False

		auth_user = request.user
		if auth_user.is_authenticated():
			openid_user = UserOpenID.objects.filter(user=auth_user)
			if len(openid_user) > 0:
				user_profile = userProfile.objects.filter(user=openid_user)
				if len(user_profile) > 0:
					steam_id = openid_user[0].claimed_id[-17:]						
					nickname = user_profile[0].nickname
					subscription = user_profile[0].premium
		time = (datetime.now()).strftime("%d/%m/%y %H:%M:%S")  	
		ip = request.META.get('REMOTE_ADDR') 					
		request_string = str(request.REQUEST)				
		url = request.path_info
		if request.META.has_key('HTTP_USER_AGENT'):
			user_agent = request.META.get('HTTP_USER_AGENT')
		else:
			user_agent = 'No useragent found'

		new_log_entry = log_entry(time=time, ip=ip, steam_id=steam_id, nickname=nickname, user_agent=user_agent, request_string=request_string, url=url, subscription=subscription)
		myfile.write(str(new_log_entry) + "\n")
		myfile.close()
		return None
