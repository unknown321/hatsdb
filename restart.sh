#!/bin/bash
#kill -9 `cat /tmp/server.pid`
/etc/init.d/uwsgi stop
cd /home/scanner/
#/etc/init.d/mongodb restart
sleep 5
killall python -s 9
sleep 5
/etc/init.d/celeryd start
echo "killed"
a=`/etc/init.d/rabbitmq-server status | grep nodedown | wc -l`
if [[ $a -gt 0 ]]
then
	/etc/init.d/rabbitmq-server restart
else
	echo "rabbitmq is running"
fi
#cd /home/hatsdb/

/etc/init.d/uwsgi start

#/home/hatsdb/manage.py runfcgi method=prefork host=127.0.0.1 port=8881 pidfile=/tmp/server.pid daemonize=false WORKDIR=/home/hatsdb maxchildren=1000 errlog=/home/hatsdb/logs/site_errors.log &
