import socket
import subprocess
import threading
import queue
import argparse
import os
import paramiko
from scp import SCPClient

BACKEND_IP = '192.168.1.26'
BACKEND_SSH_PORT = 2222
LISTEN_PORT = 54444

def scp_file(filepath, send_location):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(BACKEND_IP, port=BACKEND_SSH_PORT, username='tsec', password='^YHN3edc8ik,!QAZ', look_for_keys=False)

    with SCPClient(ssh.get_transport()) as scp:
        scp.put(filepath, recursive=False, remote_path=send_location)

def start_windump(conn_id, conn_ip, save_location):
    pcap_file = os.path.join(save_location, f'{conn_id}.pcap')
    cmd = ['windump', '-i', 'any', '-w', pcap_file]
    windump_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return windump_proc

def manage_connections(listen_int, port, save_location, backend_save_location):
    captures = {}

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((listen_int, port))
        server_socket.listen()
        
        while True:
            client_socket, client_addr = server_socket.accept()
            with client_socket:
                data = client_socket.recv(1024).decode().split()
                if len(data) < 3:
                    continue  # invalid data
                action = data[0]
                conn_id = data[1]
                conn_ip = data[2]
                client_socket.close()

            if action == 'open':
                windump_proc = start_windump(conn_id, conn_ip, save_location)
                captures[conn_id] = windump_proc
            elif action == 'close':
                windump_proc = captures.get(conn_id)
                if windump_proc is not None:
                    windump_proc.terminate()
                    del captures[conn_id]

                    if listen_int != '127.0.0.1':
                        pcap_file = os.path.join(save_location, f'{conn_id}.pcap')
                        scp_file(pcap_file, backend_save_location)
                        os.remove(pcap_file)
                else:
                    print(f"No capture process found for conn_id {conn_id}")
            else:
                exit(10)
                

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Set up listener')

    parser.add_argument('--listen-int', type=str, required=True, help='Listening IP address')
    parser.add_argument('--save-loc', type=str, required=True, help='Temporary save location for captures')
    parser.add_argument('--backend-save-loc', type=str, required=True, help='Save location on backend machine')

    args = parser.parse_args()

    listen_int = args.listen_int
    save_location = args.save_loc
    backend_save_location = args.backend_save_loc

    manage_connections(listen_int, LISTEN_PORT, save_location, backend_save_location)
