#!/usr/bin/python3

import socket
import subprocess
import threading

LISTEN_INT = '192.168.1.20'
LISTEN_PORT = 54444

# file rotation is broken
# TCPDUMP_CMD = 'tcpdump -i any -w /etc/caps/{conn_id}.pcap -C 20 -W 54'
TCPDUMP_CMD = 'tcpdump -i any -w /etc/data/{conn_id}.pcap'

# starts a tcpdump that will automatically terminate when receiving FIN packet from the given IP
# TODO: make that true
def start_tcpdump(conn_id, conn_ip):
    cmd = TCPDUMP_CMD.format(conn_id=conn_id)

    print('Starting tcpdump...')
    print(cmd)
    
    tcpdump_process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        for line in iter(tcpdump_process.stdout.readline, ''):
            print(line.strip())
    finally:
        tcpdump_process.terminate()
        tcpdump_process.wait()

def listen_for_connections(interface, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((interface, port))
        server_socket.listen()
        
        while True:
            client_socket, client_addr = server_socket.accept()
            with client_socket:
                data = str(client_socket.recv(1024).decode())
                conn_id = data.split()[0]
                conn_ip = data.split()[1]
                client_socket.close()

            # start tcp dump process now
            start_tcpdump(conn_id, conn_ip)

                

if __name__ == '__main__':
    listen_for_connections(LISTEN_INT, LISTEN_PORT)


