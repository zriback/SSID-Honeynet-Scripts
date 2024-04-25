#!/usr/bin/bash

python3 /opt/tpot/etc/log_mon.py &
log_mon_pid=$!

python3 /opt/tpot/etc/start_captures.py &
start_captures_pid=$!

cleanup () {
	kill -9 $log_mon_pid 2>/dev/null
	kill -9 $start_captures_pid 2>/dev/null

	exit 1
}

# monitor both processes
while sleep 1; do
	ps_out=$(ps $log_mon_pid | tail -n -1 | awk -F' ' '{print $1}')
	if [[ $ps_out != $log_mon_pid ]]; then
		# it has died
		cleanup
	fi

	ps_out=$(ps $start_captures_pid | tail -n 1 | awk -F' ' '{print $1}')
	if [[ $ps_out != $start_captures_pid ]]; then
		# it has died
		cleanup
	fi
done

