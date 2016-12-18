from pymongo import MongoClient
def save_items(items, game_type='tf2'):
	client = MongoClient('localhost', 27017)
	return 0