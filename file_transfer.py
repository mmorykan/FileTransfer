"""
Server and client program to transfer files between two computers.

AUTHOR: Mark Morykan

Answers to questions:
1: We should be using TCP for this assignment because TCP is much more reliable since 
   we are sending files with information across the network. TCP forces the client and 
   server to connect to each other using a handshake, limiting the amount of dropped packets. 
   This will result in all information being sent and received properly. UDP does not use handshakes 
   and therefore, drops packets much more often.

2: The server needs to send a version number so that it can connect properly to the client. 
   For example, on larger systems or programs, the server and client may not be set up exactly 
   the same way with the same code and functions. But if we are sending the version number, we 
   will be able to see whether or not the server can even connect to the client properly. 

3: I would like to add a music feature where the server owns a certain amount of song files for each genre of music.
   After the client sends True of False, the client will also send a string with either says 'music' or 'info'.
   Then the server will know where to look for its files. The server would then need to know the genre of music which the 
   client will then also send as a string. Then the server will randomly choose a song file within the genre and send it to the client.
   Or if the client is putting a song file, the server will know which genre's directory to store the file in. An old version might not
   work after this change to protocol because the client would not know whether or not to include the 'music' or 'info' argument when 
   starting up the program.
"""

import os
import argparse
import socket
import struct


#######################################
########## Utility Functions ##########
#######################################
def read_file(filename):
    """Read and return the binary data for a file."""
    with open(filename, 'rb') as file:
        return file.read()


def save_file(filename, data):
    """Save the binary data for a file."""
    with open(filename, 'wb') as file:
        file.write(data)


def recv_all(sock, num_bytes):
    """Read the given number of bytes from the socket. Don't stop until all data is recieved."""
    """Saves the maximum amount of bytes and then keeps saving more bytes until there are no more bytes to save"""
    data = sock.recv(num_bytes)
    while len(data) != num_bytes:
        data += sock.recv(num_bytes)

    return data


def recv_formatted_data(sock, frmt):
    """
    Receives struct-formatted data from the given socket according to the struct format given and
    returns a tuple of values.
    """
    return struct.unpack(frmt, recv_all(sock, struct.calcsize(frmt)))


def recv_single_value(sock, frmt):
    """
    Receives a single value from the given socket according to the struct format given and returns
    it.
    """
    return recv_formatted_data(sock, frmt)[0]


def recv_str(sock):
    """
    Receives a string using the socket. The string must be prefixed with its length and encoded.
    """
    """Gets the length of the string being sent and then receives that many bytes and returns that byte string decoded"""
    length = recv_single_value(sock, '<i')
    data = recv_all(sock, length)
    return data.decode()


def recv_str_list(sock):
    """
    Receives a list of strings from the socket. The list is prefixed with the length and each string
    is prefixed with recv_str().
    """
    """Gets the length of the list being sent. Then receives each string in the list and appends each string to a list."""
    length = recv_single_value(sock, '<i')
    lst = []
    for i in range(length):
        lst.append(recv_str(sock))
    
    return lst


def send_str(sock, string):
    """
    Sends a string using the socket. The string is encoded then prefixed with the length as a 4-byte
    integer.
    """
    """Encodes the string, packs the string with the length first. Then sends the string with length first"""
    string = string.encode()
    data = struct.pack('<i', len(string))
    data += struct.pack(str(len(string)) + 's', string)
    sock.sendall(data)


def send_str_list(sock, strings):
    """
    Sends a list of strings using the socket. The list is prefixed with its length as a 4-byte
    integer. Each string is sent with send_str().
    """
    """Packs the length of the list and sends it. Then sends each string within the list separately"""
    data = struct.pack('<i', len(strings))
    sock.sendall(data)
    for string in strings:
        send_str(sock, string)


def send_bool(sock, boolean):
    """Used this function to send a boolean value"""
    data = struct.pack('<?', boolean)
    sock.sendall(data)
    

######################################
########## Client Functions ##########
######################################
def get_files(addr, port, filenames):
    """Gets the files from the server at addr:port."""
    client = socket.socket()
    client.connect((addr, port))
    with client:
        version_number = recv_single_value(client, '<i')
        if version_number != 1:           # Checks the version number to be 1
            print('You are on the wrong version.')
            return 
        send_bool(client, True)
        send_str_list(client, filenames)
        for filename in filenames:          # Loop through every file trying to be saved
            file_exists = recv_single_value(client, '<?')
            if file_exists:                 # Executes if the file exists on the server
                size_of_file = recv_single_value(client, '<i')
                file_data = recv_all(client, size_of_file)
                save_file(filename, file_data)        # Receives the length of the file's data and then the data and saves the file data into a file
            else:
                print(f'{filename} doesn\'t exist on the server')
        

def put_files(addr, port, filenames):
    """Gets the files from the server at addr:port."""

    client = socket.socket()
    client.connect((addr, port))
    with client:
        version_number = recv_single_value(client, '<i')
        if version_number != 1:     
            print('You are on the wrong version.')                    # Checks the version number and continues if it is 1
            return 
        send_bool(client, False)
        client.sendall(struct.pack('<i', len(filenames)))
        for filename in filenames:                      # Loops through all files trying to be uploaded
            file_data = read_file(filename)             # Save the binary data of the file into file_data 
            send_str(client, filename)
            client.sendall(struct.pack('<i', len(file_data)))
            client.sendall(file_data)                   # Sends the file data length and then the file data


######################################
########## Server Functions ##########
######################################
def server_handle_request(sock):
    """
    Handles a single request using the given socket for the server.
    """
    with sock:
        sock.sendall(struct.pack('<i', 1))                  # Sends the version number 
        client_connected = recv_single_value(sock, '<?')
        if client_connected:                                # True if the client properly connects to the server 
            filenames = recv_str_list(sock)
            for filename in filenames:                      # Loops through all files being taken from the server 
                if os.path.isfile(filename):                # Checks if the file exists on the server 
                    file_data = read_file(filename)         # Saves the binary data of the file into file_data
                    send_bool(sock, True)           
                    sock.sendall(struct.pack('<i', len(file_data)))
                    sock.sendall(file_data)                 # Sends the length of the file data and then the file data

        else:
            amount_of_files = recv_single_value(sock, '<i')     # Saves the amount of files being uploaded from the client
            for i in range(amount_of_files):                    # Iterates amount of dfiles times
                filename = recv_str(sock)                       # Saves the name of the file being uploaded
                size_of_file = recv_single_value(sock, '<i')    # Saves the size of the file being uploaded
                file_data = recv_all(sock, size_of_file)        # Saves the data in the file being uploaded
                save_file(filename, file_data)                  


def run_server(port):
    server = socket.socket()
    server.bind(('', port))
    server.listen() 
    with server:
        while True:
            try:
                (s, addr) = server.accept()
                with s:
                    server_handle_request(s)
            except Exception as exception:          # Ensures that one exception does not stop the loop for connecting clients
                print(exception)


    """
    Start the server running on the given port. The server accepts clients, handles their requests,
    then goes back to accept another client (i.e. it has an infinite loop). To handle requests this
    calls the server_handle_request() function. If a client causes a problem it is reported then the
    server keeps going (i.e. if server_handle_request() raises any exception it is printed and then
    the next client is accepted).
    """



###################################
########## Main Function ##########
###################################
def main():
    """
    The main function uses an Argument Parser to get the command-line arguments and then calls ones
    of the functions: run_server(), get_files(), or put_files().
    """
    
    parser = argparse.ArgumentParser(description='Transfer files between two computers')
    parser.add_argument('--port', type=int, help='set the port number to use', default=2222)
    subparsers = parser.add_subparsers(title='command', dest='cmd', required=True)
    subparsers.add_parser(name='server', description='run the server')
    get_cmd = subparsers.add_parser(name='get', description='get files from the server')
    get_cmd.add_argument('address', help='the hostname/IP address of the server')
    get_cmd.add_argument('file', nargs='+', help='the names of the files to get')
    put_cmd = subparsers.add_parser(name='put', description='put files onto the server')
    put_cmd.add_argument('address', help='the IP address of the server')
    put_cmd.add_argument('file', nargs='+', help='the names of the files to put')
    args = parser.parse_args()
    if args.cmd == 'server':
        run_server(args.port)
    elif args.cmd == 'get':
        get_files(args.address, args.port, args.file)
    elif args.cmd == 'put':
        if not all(os.path.isfile(filename) for filename in args.file):
            print("Not all of the given files exist, not trying")
            return
        put_files(args.address, args.port, args.file)

if __name__ == "__main__":
    main()

