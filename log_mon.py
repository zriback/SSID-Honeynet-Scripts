#!/usr/bin/python3

# Monitor markers/log.conn for changes and call out to remote hosts when they need to start tcpdump processes

import os
import time
import socket

LOG_FILE = 'markers/conn.log'

LISTEN_IP_ADDRS = ['127.0.0.1', '192.168.1.20']
LISTEN_PORT = 54444

# returns the last line of the passed file
def get_last_line(filename):
    with open(filename, 'rb') as f:
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR)
        last_line = f.readline().decode()
    return last_line.strip()

def get_second_last_line(filename):
    with open(filename, 'rb')  as f:
        f.seek(-2, os.SEEK_END)
        newlines_found = 0
        while True:
            if f.read(1) == b'\n':
                newlines_found += 1
                if newlines_found == 2:
                    break
            f.seek(-2, os.SEEK_CUR)
        second_last_line = f.readline().decode().strip()
    return second_last_line

def get_file_size(filename):
    with open(filename, 'r') as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
    return size

# notifies all the listners at globally defined ip addresses and ports of the new connection
def notify_listeners(conn_id, conn_ip):
    message = conn_id + " " + conn_ip
    print(f'message is {message}')
    for ip in LISTEN_IP_ADDRS:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, LISTEN_PORT))
                s.sendall(message.encode())
        except Exception as err:
            print(f'Error connecting with {ip}: {err}')


def monitor_log(filename):
    old_pos = get_file_size(filename)
    while True:
        new_pos = get_file_size(filename)
        if new_pos != old_pos: # something has been added to the file
            old_pos = new_pos
            line = get_last_line(filename)

            # if this line shows us a successfull connection has been made, we need to act
            if line.split()[0] == 'open':
                conn_id = line.split()[1]
                conn_ip = get_second_last_line(filename)
                # print(f'id={conn_id}, ip={conn_ip}\n')
                notify_listeners(conn_id, conn_ip)
        else:
            # nothing new in the file, sleep for a bit then try again
            time.sleep(1)


if __name__ == '__main__':
    monitor_log(LOG_FILE)

