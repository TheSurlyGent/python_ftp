import sys
import time
import socket
# get server name from command line
if len(sys.argv) != 2:
    print('Usage: myftp ftp_server_name')
    sys.exit()
server = sys.argv[1]
# create connection socket
project_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# initiate control TCP connection
try:
    project_socket.connect((server, 21))
except Exception:
    print(f'Error: server {server} cannot be found.')
    sys.exit()
print(f'Connected to {server}.')
# print message from server
response = project_socket.recv(1024).decode('utf-8').strip()
print(response)
# send username to server
while True:
    username = input('Enter username: ')
    if not username:
        print('Error: username cannot be empty')
    else:
        break
project_socket.send(bytes(f'USER {username}\r\n','utf-8'))
response = project_socket.recv(1024).decode("utf-8").strip()
print(response)
# send password to server
while True:
    password = input('Enter password: ')
    if not password:
        print('Error: password cannot be empty')
    else:
        break
project_socket.send(bytes(f'PASS {password}\r\n','utf-8'))
response = project_socket.recv(1024).decode("utf-8").strip()
print(response)
# login success
if response.startswith("230"):
    # set remote directory to root directory
    remote_dir = '/'
    # main loop
    print('Welcome to my FTP ')
    loop = True
    while loop:
        print('The commands are: "ls","cd","get","put","delete", "quit"')
        print('Please enter a command')
        command = input('myftp> ')
        if command == 'quit':
            #end session
            project_socket.send(bytes('QUIT\r\n', 'utf-8'))
            response = project_socket.recv(1024).decode('utf-8').strip()
            print(response)
            project_socket.close()
            loop = False
        elif command == 'ls':
            # send PASV command
            project_socket.send(bytes('PASV\r\n', 'utf-8'))
            # new socket
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            response = project_socket.recv(1024).decode('utf-8').strip()
            print(response)
            if response.startswith('227'):
                pieces = response.split('(')[1].split(')')[0].split(',')
                ip_address = '.'.join(pieces[:4])
                port = int(pieces[4]) * 256 + int(pieces[5])

                # connect the data socket to IP and Port
                temp_socket.connect((ip_address, port))

                # send ls command
                project_socket.send(bytes(f'LIST {remote_dir}\r\n', 'utf-8'))

                # receive response and print
                response = project_socket.recv(1024).decode('utf-8').strip()
                print(response)
                # check response for success or error
                if response.startswith('150'):
                    # wait for server to finish sending data
                    time.sleep(2)

                    while True:
                        response = project_socket.recv(1024).decode('utf-8').strip()
                        print(response)
                        if response.startswith('226') or response.startswith('425'):
                            # The response starts with "226 Transfer complete" or "425 Can't open data connection",
                            # so we know the data transfer is complete or has failed.
                            break

                    # receive the list of files and directories
                    files_list = ''
                    while True:
                        data = temp_socket.recv(1024)
                        if not data:
                            break
                        files_list += data.decode('utf-8')
                    print(files_list)
                    temp_socket.close()
                else:
                    print(f'Error: {response}')
        elif command.startswith('cd'):
            if len(command.split(' ')) < 2:
                print('Error: cd command requires a dir arg')
            else:
                # create new temp directory
                directory = command.split(' ')[1]
                # send cd command
                project_socket.send(bytes(f'CWD {directory}\r\n','utf-8'))
                response = project_socket.recv(1024).decode('utf-8').strip()
                if response.startswith('250'):
                    print(f'Directory has been changed to {directory}')
                    remote_dir = directory
                    # send PWD command
                    project_socket.send(bytes('PWD\r\n', 'utf-8'))
                    response = project_socket.recv(1024).decode('utf-8')
                    if response.startswith('257'):
                        remote_dir = response.split('"')[1]
                        print(f'Current directory: {remote_dir}')
                    else:
                        print('Error getting current directory')
                else:
                    print(f'There was an error trying to change to {directory}')
        elif command.startswith('get'):
            # download file name
            d_file = command.split(' ')[1]
            # send PASV command
            project_socket.send(bytes('PASV\r\n', 'utf-8'))
            # receive response and extract IP and port
            response = project_socket.recv(1024).decode('utf-8').strip()
            print(response)
            if response.startswith('227'):
                pieces = response.split('(')[1].split(')')[0].split(',')
                ip_address = '.'.join(pieces[:4])
                port = int(pieces[4]) * 256 + int(pieces[5])
                # connect the data socket to IP and Port
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_socket.connect((ip_address, port))
                # send RETR command
                project_socket.send(bytes(f'RETR {d_file}\r\n', 'utf-8'))
                # receive response and print
                response = project_socket.recv(1024).decode('utf-8').strip()
                print(response)
                # check response for success or error
                if response.startswith('150'):
                    with open(d_file, 'wb') as f:
                        while True:
                            file_data = temp_socket.recv(1024)
                            if not file_data:
                                break
                            f.write(file_data)
                    print(f'{d_file} has been downloaded')
                else:
                    print(f'Error: {response}')
            else:
                print(f'Error: {response}')

print("FTP client has finished.")

