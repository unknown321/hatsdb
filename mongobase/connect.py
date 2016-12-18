tf_db_r = None
tf_db_w = None
dota_db_r = None
dota_db_w = None
owners_db_r = None
owners_db_w = None
unusuals_r = None
unusuals_w = None

from pymongo import MongoClient, errors

import logging

# Get an instance of a logger
logger = logging.getLogger('mongobase.data_collectors')

class HatsdbClient:
	"""docstring for HatsdbClient"""
	def __init__(self, read_only=True):
		self.client = None
		self.read_only = read_only
	def connect(self, game_type='tf2', login='', password=''):
		from hatsdb import settings
		if self.read_only:
			login = settings.AUTH_R['login']
			password = settings.AUTH_R['password']
		else:
			login = settings.AUTH_W['login']
			password = settings.AUTH_W['password']
		self.client = MongoClient('localhost', 27017)
		self.dbname = game_type
		try:
			self.client[game_type].authenticate(login, password)
		except Exception, e:
			auth_status = False
		else:
			auth_status = True
		return auth_status
	def disconnect(self):
		self.client.disconnect()
		return 0
	def save_to_collection(self, item, collection_id, db_type):
		#should be used to save single items - like knifes and unusuals
		return self.client[db_type][str(collection_id)].save(item)
	def bulk_save(self, items, game_type):
		#should be used to save whole backpacks
		for item in items:
			self.save_to_collection(self, item, item.defindex, game_type)
		return 0
	def find(self, collection_id, query, skip=0, limit=0, sort='hours', sort_order=1):
		if skip <= 0:
			c =  self.client[self.dbname][str(collection_id)].find(query).sort(sort, sort_order).limit(limit)
		else:
			c =  self.client[self.dbname][str(collection_id)].find(query).sort(sort, sort_order).skip(skip).limit(limit)
		return c
	def get_count(self, collection_id, query):
		return self.client[self.dbname][str(collection_id)].find(query).count()