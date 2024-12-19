import os
from scapy.all import rdpcap, IP

# Directory containing .pcap files
TRAFFIC_SAMPLES_PATH = 'C:\\Users\\zacha\\vscode\\Honeynet-Research\\Traffic Samples'

# Constants for IP addresses
DATABASE_IP = '192.168.1.36'
FTP_IP = '192.168.1.27'
WEBSERVER_IP = '192.168.1.20'
WINDOWS10_IP = '192.168.1.29'
WINDOWS_SERVER_IP = '192.168.1.37'  # Assuming this is correct

# List of all hosts
ALL_HOSTS = [DATABASE_IP, FTP_IP, WEBSERVER_IP, WINDOWS10_IP, WINDOWS_SERVER_IP]

# Mapping of filenames to host IPs
filename_to_ip = {
    'database.pcap': DATABASE_IP,
    'ftp.pcap': FTP_IP,
    'webserver.pcap': WEBSERVER_IP,
    'win10.pcap': WINDOWS10_IP,
    'winserv.pcap': WINDOWS_SERVER_IP
}

def get_host_ip_from_filename(filename):
    # Extract the base filename
    base_name = os.path.basename(filename)
    # Get the IP from the mapping
    return filename_to_ip.get(base_name)


# print out the connections directory stucture
def print_connections(connections: dict):
    for ip, packets in connections.items():
        print(ip)
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
        connections[other_host_ip].append([size, direction, float(timestamp)])
    
    return connections


# analyze all the pcap files in one given directory
# return a list of results (what is actually returning?)
def analyze_directory(directory: str):
    # list to hold dictionaries containing connectios for each machine
    all_host_connections = []

    # For each .pcap file in the directory
    for filename in os.listdir(directory):
        if not filename.endswith('.pcap'):
            continue
        pcap_file = os.path.join(directory, filename)
        host_ip = get_host_ip_from_filename(filename)
        if not host_ip:
            print(f"Could not determine host IP for {filename}")
            continue
        else:
            print(f'Analyzing {host_ip} from {filename}')
            connections = analyze_file(pcap_file, host_ip)

            print_connections(connections)

            all_host_connections.append(connections)
        
    return all_host_connections


def main():
    analyze_directory(TRAFFIC_SAMPLES_PATH)


if __name__ == '__main__':
    main()

