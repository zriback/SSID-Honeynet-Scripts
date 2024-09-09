#!/usr/bin/bash

# Sets up the backend from the scripts in this repo

set -x

cp client_transport.py /data/cowrie/client_transport.py
cp cowrie-capture.service /etc/systemd/system/cowrie-capture.service
cp log_mon.py /opt/tpot/etc/log_mon.py
cp server_transport.py /data/cowrie/server_transport.py
cp start_captures_backend.py /opt/tpot/etc/start_captures.py
cp start_captures_service.sh /opt/tpot/etc/start_captures_service.sh
cp tpot.yml-Offline /opt/tpot/etc/tpot.yml-Offline
cp tpot.yml-Online /opt/tpot/etc/tpot.yml-Online

set +x
