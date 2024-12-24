#!/usr/bin/bash

# Sets up the backend from the scripts in this repo

set -x

cp client_transport.py /data/cowrie/client_transport.py
cp server_transport.py /data/cowrie/server_transport.py
cp tpot.yml-Offline /opt/tpot/etc/tpot.yml-Offline
cp tpot.yml-Online /opt/tpot/etc/tpot.yml-Online
cp tpot.yml-Online /opt/tpot/etc/tpot.yml

set +x
