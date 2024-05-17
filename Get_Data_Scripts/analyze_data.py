import json

# convert json into python dict
def load_json(filename: str):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

# load data from honeynet from data.json file
data = load_json('data.json')

# new dictionary to store organized information about sessions based on IP
sessions = {}

for i, entry in enumerate(data['hits']['hits']):
    ip = entry['fields']['src_ip'][0]
    timestamp = entry['fields']['@timestamp'][0]
    cmd = entry['fields']['input.keyword'][0]

    # if first time seeing this ip, add it to the dictionary
    # each ip will be a list of dictionaries
    if ip not in sessions:
        sessions[ip] = {}
    # sessions[ip].append({'time': timestamp, 'cmd': cmd})
    sessions[ip][timestamp] = cmd

    # print(f'{ip} @ {timestamp}: {cmd}')

# also write to file
with open('commands.txt', 'w') as f:
    for ip, cmds in sessions.items():
        print(ip)
        f.write(f'{ip}\n')
        for time, cmd in cmds.items():
            print(f'\t{time}\t{cmd}')
            f.write(f'\t{time}\t{cmd}\n')
        print()
        f.write('\n')