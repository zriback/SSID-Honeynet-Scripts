import os
from scapy.all import rdpcap, IP

# Directory containing .pcap files
TRAFFIC_SAMPLES_PATH = 'C:\\Users\\zacha\\vscode\\Honeynet-Research\\Traffic Samples'

# Constants for IP addresses
DATABASE_IP = '192.168.1.36'
FTP_IP = '192.168.1.27'
WEBSERVER_IP = '192.168.1.20'
WINDOWS10_IP = '192.168.1.29'
WINDOWS_SERVER_IP = '191.168.1.37'  # Assuming this is correct

# List of all hosts
ALL_HOSTS = [DATABASE_IP, FTP_IP, WEBSERVER_IP, WINDOWS10_IP, WINDOWS_SERVER_IP]

# Mapping of filenames to host IPs
filename_to_ip = {
    # 'database.pcap': DATABASE_IP,
    # 'ftp.pcap': FTP_IP,
    'webserver.pcap': WEBSERVER_IP,
    # 'win10.pcap': WINDOWS10_IP,
    # 'winserv.pcap': WINDOWS_SERVER_IP
}

def get_host_ip_from_filename(filename):
    # Extract the base filename
    base_name = os.path.basename(filename)
    # Get the IP from the mapping
    return filename_to_ip.get(base_name)

# For each .pcap file in the directory
for filename in os.listdir(TRAFFIC_SAMPLES_PATH):
    if not filename.endswith('.pcap'):
        continue

    pcap_file = os.path.join(TRAFFIC_SAMPLES_PATH, filename)
    host_ip = get_host_ip_from_filename(filename)

    if not host_ip:
        print(f"Could not determine host IP for {filename}")
        continue
    
    print(f"Processing {filename} for host IP {host_ip}")
    # Get the other hosts
    other_hosts = [ip for ip in ALL_HOSTS if ip != host_ip]
    
    # Initialize connection dictionaries
    connections = {ip: [] for ip in other_hosts}
    
    # Initialize previous timestamp
    prev_timestamp = None
    
    # Read the pcap file
    packets = rdpcap(pcap_file)
    for packet in packets:
        # Check if packet has IP layer
        if IP in packet:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            # Check if packet is between host_ip and one of the other hosts
            if (src_ip == host_ip and dst_ip in other_hosts) or (dst_ip == host_ip and src_ip in other_hosts):
                # Determine the other host IP
                other_host_ip = dst_ip if src_ip == host_ip else src_ip
                
                # Determine direction
                direction = 'out' if src_ip == host_ip else 'in'
                
                # Get packet size
                size = len(packet)
                
                # Get timestamp
                timestamp = packet.time
                
                # Compute inter-arrival time
                if prev_timestamp is None:
                    inter_arrival_time = 0
                else:
                    inter_arrival_time = timestamp - prev_timestamp
                prev_timestamp = timestamp
                
                # Append features to the list for this connection
                connections[other_host_ip].append([size, direction, float(inter_arrival_time)])

    # Now, connections dictionary contains lists of features for each connection
    # For example, connections['192.168.1.36'] is the list of features for packets between host_ip and 192.168.1.36
    # We can process or output the data as needed
    for other_ip, features_list in connections.items():
        print(f"Connection between {host_ip} and {other_ip}:")
        print(f"Number of packets: {len(features_list)}")
        # For debugging, you can print the features
        for features in features_list:
            print(features)

