#!/bin/sh
PORT=1337
while /bin/true; do
	echo "(re)starting listener on port $PORT"
	nc -lp $PORT -q 0 -e ./cat
	echo "listener stopped, press ^C (again) to exit"
	sleep 1
done
