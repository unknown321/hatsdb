#!/bin/bash
mkdir /var/log/celery
mkdir /var/run/celery

for i in $(seq 1 4); 
	do
		touch /var/log/celery/baka$i.log; 
		touch /var/run/celery/baka$i.pid; 
	done
touch /var/log/celery/save_baka.log
touch /var/run/celery/save_baka.pid
chgrp hatsdb /var/log/celery/*
chown hatsdb /var/log/celery/*
chgrp hatsdb /var/run/celery/
chown hatsdb /var/run/celery/
chgrp hatsdb /var/run/celery/*
chown hatsdb /var/run/celery/*
/etc/init.d/celeryd start
