import paramiko
import time
from functools import partial
import re

LINUX_OS = 0
WINDOWS_OS = 1

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
    if command == 'exit' or command == 'quit':
        prompt = primary_prompt

    print('Sending:', command)
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
    print(return_value)
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


def ftp_chain(channel, server_info):
    ftp_command = f'ftp {server_info["hostname"]}'

    # tell it to expect the ftp prompt now
    global prompt
    prompt = server_info['prompt']

    # in this case we are using the password as the username because we are signing in an anon account
    send_command(
        channel,
        ftp_command,
        password_prompt='Name (',
        password=server_info['username'],
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
pivot_servers = [
    {
        'name'    : 'Database Server',
        'hostname': '192.168.1.36',
        'username': 'uws-it',
        'password': 'uwsit2021',
        'prompt'  : 'PROMPT2$>'
    },
    {
        'name'   : 'FTP Server',
        'hostname': '192.168.1.27',
        'username': 'anonymous',
        'password': '',
        'prompt'  : 'ftp>'
    },
    {
        'name'   : 'Windows Host',
        'hostname': '192.168.1.29',
        'username': 'user',
        'password': 'win-pass',
        'prompt'  : 'PROMPT3$>'
    },
    {
        'name'   : 'Windows Server',
        'hostname': '192.168.1.24',
        'username': 'Administrator',
        'password': 'Admin123!',
        'prompt'  : 'PROMPT4$>'
    } 
]


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
    pivot_windows_host = partial(ssh_chain, channel=channel, server_info=pivot_servers[2], os=WINDOWS_OS)
    pivot_windows_server = partial(ssh_chain, channel=channel, server_info=pivot_servers[3], os=WINDOWS_OS)

    # Set unique shell prompts
    prompt = primary_prompt
    set_prompt(prompt, channel, LINUX_OS)

    # send commands on first pivot host
    send_command(channel, 'whoami', os=LINUX_OS)

    pivot_windows_host()
    send_command(channel, 'hostname', os=WINDOWS_OS)
    send_command(channel, 'exit', os=WINDOWS_OS)

    # Close the SSH connection to the first server
    ssh_client.close()


if __name__ == '__main__':
    main()

