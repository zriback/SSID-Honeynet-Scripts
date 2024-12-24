# SSID-Honeynet-Scripts

This repository contains the files and scripts needed to run the backend machine for the Honeynet portion of the RIT SSID project. This includes a system for automating network traffic captures from all the pivot hosts during attacker SSH sessions. The remainder of this readme file contains detailed information for all these files and for how to set up the automatic capture system and the parts of T-Pot unique to this project. 

## T-Pot Setup

 The backend machine for this project utlizes the T-Pot architecture available at https://github.com/telekom-security/tpotce. T-Pot has a central tpot.yml file located at ```/opt/tpot/etc/tpot.yml``` to configure all of its parts. This repository contains two version of this file:

 - ```tpot.yml-Offline```

 - ```tpot.yml-Online```

 The offline version will start the components of the T-Pot necessary for viewing saved data and connecting to the online Kibana portal but will not allow attackers to connect. The online version will allow attackers to connect, too. Both these yml files are also edited to include a webserver docker container with a web root of /opt/tpot/etc/htdocs.

Part of this uses Cowrie, an SSH Honeypot. Further information on Cowrie is available at https://github.com/cowrie/cowrie. For our setup, we modify some of cowrie's backend python code. These files with the slight modifications are in this repository as:

 - ```client_transport.py```

 - ```server_transport.py```

 These files are the same as the originals but have certain hooks present that log when a connection is open/closed from a specific IP to the file ```/opt/tpot/etc/markers/conn.log```. This is how the auto-capture system knows when to start/stop network traffic captures. Note that ```/opt/tpot/etc/markers``` is set up as a shared volume between the docker container running cowrie and the host backend machine. 

 After cloning this repository, ```setup.sh``` can be used to move the files covered in this section to their necessary locations on the backend machine. 

 ## Auto-capture setup

 To collect attackers samples automatically, an auto-capture system has been implemented. When an attacker first connects via SSH, a signal is sent out to every host on the honeynet to start capturing network traffic. When the attacker disconnects, a signal is sent to those hosts to stop capturing, and send the file (in pcap format) to the backend to be stored. 

 The auto-capture system deploys using ansible. Use the following command in the ansible directory to enable to automatic capturing.

 ```ansible-playbook -i inventory.ini -K deploy.yml```

 When prompted, the become password is 'ansible'. To shutdown the system, use

 ```ansible-playbook -i inventory.ini -K shutdown.yml```

 The playbook works by copying (using SCP for the remote hosts) the scripts in the ansible/files directory to the necessary locations around the honeynet and starting them running. Note that all the IP addresses and file locations are hardcoded. If this info needs to change, then it would have to be manually changed in the scripts and in deploy.yml/shutdown.yml when the scripts are started using command-line arguments. 

 ## Automatic attack generation and analysis

 In order to collect large amounts of pivot attack samples using this honeynet, an externally run script is used that is included in this repository as ```auto_ssh.py```. This script should be run on a host machine located outside of the honeynet. It has a pre-made list of commands and methods for accessing the honeynet, running information gathering commands, pivoting to a second host, running more information gathering commands, and then running certain "flag getting" commands to locate and read out the flag.txt file that was put on all machines in the network. Overall, the script is meant to simulate a real human attacker carrying out stepping-stone attacks in the honeynet.

 Each and every attacker connection results in pcap files saved from every relavant host on the honeynet. The output structure might look like:

```
├───backend
│       000000001.pcap
│       000000002.pcap
│
├───ftpserver
│       000000001.pcap
│       000000002.pcap
│
├───webserver
|       000000001.pcap
|       000000002.pcap
|        
...
```

Pcap files are named using the timestamp of when the attacker first connects. Pcap files with the same timestamp therefore correspond to the same attack instance. In the above structure, '000000001' is the reference given for the first attack, and each subdirectory that '000000001.pcap' is found in corresonds to which host on the honeynet that capture was taken on.

Another script, ```analyze_samples.py``` is included in this repository to analyze the resulting directory output from ```auto_ssh.py```. This script looks at each session individually, which in the above directory structure is denoted by the family of files with the same timestamped name. It looks at each capture in that family from each machine on the network and separates out all the streams of packets from that host to the other hosts in the network we are interested in. For each stream, it will pull out features that we are interested in ([packet length, direction, time]). 

By default, the output of this process is saved to ```output.obj``` via the Python pickle library. Each call of ```pickle.load('output.obj')``` will return the data from one attacker session. The structure of the output for one attacker session is as follows:

The top level dictionary has keys corresponding to the IP addresses for each machine in the honeynet. The value for each of these keys is another dictionary that stores all the connection streams between that host and every other host in the honeynet. So, the subdictionary has keys representing the IP addresses of every OTHER host in the network besides the one identified in the key of the top level dictionary. The values of the subdictionary are simply lists of our features, where each feature is saved as a numpy array. So, the data from one attacker session is in the form of a dictionary of dictionaries of lists of features.

To load the data from multiple attacker sessions from ```output.obj``` into a list in Python, your code might look similar to the following.

```
import pickle

all_sessions_data = []
try:
    with open('output.obj', 'rb') as f:
        session_data = pickle.load(f)
        all_sessions_data.append(session_data)
except EOFError:
    pass
```
