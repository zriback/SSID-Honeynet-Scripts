#!/usr/bin/python3

import socket
import subprocess
import threading
import queue

import os
import paramiko
from scp import SCPClient

BACKEND_IP = '192.168.1.26'
BACKEND_CAP_LOCATION = '/data/cowrie/captures/webserver'
LISTEN_INT = '192.168.1.20'
LISTEN_PORT = 54444
SAVE_LOCATION = '/data/caps'

# file rotation is broken
# TCPDUMP_CMD = 'tcpdump -i any -w /etc/caps/{conn_id}.pcap -C 20 -W 54'
TCPDUMP_CMD = 'tcpdump -i any -w {save_loc}/{conn_id}.pcap'

def scp_file(filepath):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(BACKEND_IP, port=2222, username='tsec', password='^YHN3edc8ik,!QAZ', look_for_keys=False)

    with SCPClient(ssh.get_transport()) as scp:
        scp.put(filepath, recursive=False, remote_path=BACKEND_CAP_LOCATION)

# starts a tcpdump that will automatically terminate when receiving FIN packet from the given IP
# TODO: make that true
def start_tcpdump(conn_id, conn_ip):
    cmd = TCPDUMP_CMD.format(save_loc=SAVE_LOCATION, conn_id=conn_id)

    # print('Starting tcpdump...')
    # print(cmd)
    
    tcpdump_proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return tcpdump_proc


def manage_connections(interface, port):
    captures = {}

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((interface, port))
        server_socket.listen()
        
        while True:
            client_socket, client_addr = server_socket.accept()
            with client_socket:
                data = str(client_socket.recv(1024).decode()).split()
                action = data[0]
                conn_id = data[1]
                conn_ip = data[2]
                client_socket.close()

            # start or stop tcp dump processes
            if action == 'open':
                tcpdump_proc = start_tcpdump(conn_id, conn_ip)
                captures[conn_id] = tcpdump_proc
            elif action == 'close':
                tcpdump_proc = captures.get(conn_id)
                if not tcpdump_proc is None:
                    tcpdump_proc.terminate()
                del captures[conn_id]

                # if not running on the backend, send there  and delete here
                if interface != '127.0.0.1':
                    scp_file(f'{SAVE_LOCATION}/{conn_id}.pcap')
                    os.remove(f'{SAVE_LOCATION}/{conn_id}.pcap')


            else:
                # something went really wrong
                exit(10)
            

if __name__ == '__main__':
    manage_connections(LISTEN_INT, LISTEN_PORT)


