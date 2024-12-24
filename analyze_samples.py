import os
from scapy.all import rdpcap, IP
import sys
import numpy as np
import pickle

# Directory containing .pcap files
TRAFFIC_SAMPLES_PATH = 'C:\\Users\\zacha\\vscode\\Honeynet-Research\\SSID-Honeynet-Scripts\\captures'

# Pickle output file
PICKLE_OUTPUT_FILE = 'output.obj'

# Colors
DEFAULT_COLOR = '\x1b[39m'
GREEN_COLOR = '\x1b[32m'
RED_COLOR = '\x1b[31m'
YELLOW_COLOR = '\x1b[33m'

# Constants for IP addresses
BACKEND_IP = '192.168.1.26'
DATABASE_IP = '192.168.1.36'
FTP_IP = '192.168.1.27'
WEBSERVER_IP = '192.168.1.20'
WINDOWS10_IP = '192.168.1.29'
WINDOWS_SERVER_IP = '192.168.1.37'

# List of all hosts
# to include analysis with the backend, add it to this list
ALL_HOSTS = [DATABASE_IP, FTP_IP, WEBSERVER_IP, WINDOWS10_IP, WINDOWS_SERVER_IP]

# Mapping of filenames to host IPs
# to analyze backend.pcap, add it to this structure
dirname_to_ip = {
    #'backend':BACKEND_IP,
    'database': DATABASE_IP,
    'ftp-server': FTP_IP,
    'webserver': WEBSERVER_IP,
    'windows10': WINDOWS10_IP,
    'winserv': WINDOWS_SERVER_IP
}

def get_host_ip_from_dirname(filename):
    # Extract the base filename
    base_name = os.path.basename(filename)
    # Get the IP from the mapping
    return dirname_to_ip.get(base_name)


# print out the connections directory stucture
def print_connections(connections: dict):
    for ip, packets in connections.items():
        print('With', ip)
        if not packets:
            print('\tNone')
        for packet in packets:
            print(f'\t{packet}')
        print()

# analyze one file 
def analyze_file(pcap_file: str, host_ip: str):
    # Get the other hosts
    other_hosts = [ip for ip in ALL_HOSTS if ip != host_ip]
    
    # Initialize connection dictionaries
    connections = {ip: [] for ip in other_hosts}
    
    # Read the pcap file
    packets = rdpcap(pcap_file)
    for packet in packets:
        # Check if packet has IP layer
        if IP not in packet:
            continue

        src_ip = packet[IP].src
        dst_ip = packet[IP].dst

        # Check if packet is between host_ip and one of the other hosts
        if not (src_ip == host_ip and dst_ip in other_hosts) and not (dst_ip == host_ip and src_ip in other_hosts):
            continue

        # Determine the other host IP
        other_host_ip = dst_ip if src_ip == host_ip else src_ip
        
        # Determine direction
        direction = 1 if src_ip == host_ip else -1
        
        # Get packet size
        # size = len(packet)  # getting size this way does not account for packets truncated during capture
        # get length from the IP header field then add 14 for the Ethernet header
        size = packet[IP].len + 14
        
        # Get timestamp
        timestamp = packet.time
        
        # Append features to the list for this connection
        connections[other_host_ip].append(np.array([size, direction, float(timestamp)]))
    
    return connections


# analyze all the pcap files associated with one attacker session
# returns a dict where each key is the IP of a host in the honeynet and the value is the connections dict for that host
    # Each connections dictionary has a key for every other IP on the network
    # the value for each key is the list (nparray) of features between this host and the key IP
    # each feature is [packet_length, direction, timestamp]
def analyze_session(files: list[str], host_ips: list[str]):
    # list to hold dictionaries containing connections for each machine
    all_host_connections = {}

    # For each .pcap file in the directory
    for filename, host_ip in zip(files, host_ips):
        connections = analyze_file(filename, host_ip)
        all_host_connections[host_ip] = connections
        
    return all_host_connections


# analyze one directory with multiple attacker samples in it
# expected structure is a subdir for each host with all the packet captures from that host
# packet captures from different hosts but from the same attacker connection are correlated together by having identical names
def analyze_directory(directory: str):
    primary_dir = None
    num_samples = 0
    # dir names and associated IPs will align with one another
    dir_names = []
    host_ips = []
    for dir in os.listdir(directory):
        host_ip = get_host_ip_from_dirname(dir)
        if host_ip is None:  # we don't care about or know about this host
            continue
        host_ips.append(host_ip)
        if primary_dir is None:  # this is a first dir we can use to iterate over later
            primary_dir = os.path.join(directory, dir)
        dir_names.append(os.path.join(directory, dir))
    
    for pcap in os.listdir(primary_dir):
        if not pcap.endswith('.pcap'):
            continue
        session_files = [os.path.join(capture_dir, pcap) for capture_dir in dir_names]
        session_connections = analyze_session(session_files, host_ips)

        # pickle session_connections to output file
        with open(PICKLE_OUTPUT_FILE, 'ab+') as f:
            pickle.dump(session_connections, f)
        
        num_samples += 1
        print(f'{YELLOW_COLOR}Analyzed sample {num_samples} ({pcap}){DEFAULT_COLOR}')
    
    print(f'{GREEN_COLOR}Saved {num_samples} samples{DEFAULT_COLOR}')


def main():
    if len(sys.argv) != 2:
        print(f'{RED_COLOR}Incorrect command-line format.{DEFAULT_COLOR} Usage:\n{sys.argv[0]} [traffic samples file path]\n')
        exit()

    traffic_sample_filepath = sys.argv[1]

    if not os.path.exists(traffic_sample_filepath):
        print(f'{RED_COLOR}That file path does not exist :({DEFAULT_COLOR}')
        exit()

    print(f'{GREEN_COLOR}Analyzing...{DEFAULT_COLOR}')

    analyze_directory(TRAFFIC_SAMPLES_PATH)

    print(f'{GREEN_COLOR}Results have been saved to {PICKLE_OUTPUT_FILE}{DEFAULT_COLOR}')


if __name__ == '__main__':
    main()

