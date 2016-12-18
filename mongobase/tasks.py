from celery.decorators import task
from celery.decorators import periodic_task
from celery.task.schedules import crontab
import time
from scanner import scan_wrapper
import gc
import logging

logger = logging.getLogger(__name__)

@task(soft_time_limit=50)
def scan_task(steam_id,  game_type, marketable, uncraft, untrade, blacklist):
	# from celery.exceptions import SoftTimeLimitExceeded
	# try:
	# except (SoftTimeLimitExceeded, Exception):
		# a = None
	logger.info(str(steam_id))
	a = scan_wrapper(steam_id,  game_type, marketable, uncraft, untrade, blacklist)
	gc.collect(0)
	gc.collect(1)
	gc.collect(2)
	return a

@task(soft_time_limit=120)
def friend_task(steam_id,  game_type, marketable, uncraft, untrade, blacklist):
	logger.info('friend ' + str(steam_id))
	a = scan_wrapper(steam_id,  game_type, marketable, uncraft, untrade, blacklist)
	gc.collect(0)
	gc.collect(1)
	gc.collect(2)
	return a

@task(soft_time_limit=120)
def save_task(scanned_player, game_type):
	from data_collectors import save_items
	a = save_items(scanned_player, game_type)
	return None

@task(soft_time_limit=50)
def heroic_task(steam_id, game_type):
	a = download_legacy_items(steam_id, game_type)
	return a