"""
    Simple TCP level socket server & client. Serves multiple client requests using the `select` method of
    obtaining non-blocking behavior. 
    
    Developed on Python 2.6.
    
    Credit to Alexander Stepanov for inspiration (https://steelkiwi.com/blog/working-tcp-sockets/)
"""
import socket
import select
import queue
import re
import threading
import logging

class TCPServer(threading.Thread):
    """A non-blocking socket server that listens for messages on the given hostname/IP and port"""

    def __init__(self, ip, port, message_callback):
        threading.Thread.__init__(self)
        if ip == "localhost":
            ip = "127.0.0.1"
        assert re.match(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", ip), "Invalid IP address: %s" % ip
        assert int(port) > 1024, "Port numbers must be greater than 1024 but got: %s" % str(port)

        self.ip = ip
        self.port = int(port)
        self._socket = None
        self._inputs = []
        self._outputs = []
        self._message_queues = {}
        self._message_callback = message_callback
        
    def __enter__(self):
        self.start()
        # may find you need to return `self` here!?
        
    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    def run(self):
        self._outputs = []
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._inputs = [self._socket]
        self._socket.setblocking(0)
        self._socket.bind((self.ip, self.port))
        self._socket.listen(5)

        while self._inputs:
            readable, writable, exceptional = select.select(
                self._inputs, self._outputs, self._inputs)
            for s in readable:
                if s is self._socket:
                    # The readable is a new connection request
                    connection, client_address = s.accept()
                    logging.info('TCPServer thread: Connection established from %s:%d',
                                 client_address[0], client_address[1])
                    connection.setblocking(0)
                    self._inputs.append(connection)
                    self._message_queues[connection] = queue.Queue()
                else:
                    # The readable is an existing connection where the remote side
                    # has sent some data to be collected by the server
                    data = s.recv(1024).decode('utf-8')
                    if data and len(data) > 0:
                        logging.info('TCPServer thread: Message received from %s:%d |%s|',
                                     s.getpeername()[0], s.getpeername()[1], data)
                        handlr_resp = self._request_handler(s, data)

                        # the stop call must set self._inputs to [] which exits the while loop
                        if handlr_resp == 'OK <shutdown>':
                            self.stop()
                            return

                        if s not in self._outputs:
                            self._outputs.append(s)
                    #else:
                    #    self._inputs.remove(s)
                    #    if s in self._outputs:
                    #        self._outputs.remove(s)
                    #    logging.info('TCPServer thread: Connection %s is closing now',
                    #                 ':'.join([str(i) for i in s.getpeername()]))
                    #    s.shutdown(0)
                    #    del self._message_queues[s]

            for s in writable:
                try:
                    response = self._message_queues[s].get_nowait().encode('utf-8')
                except queue.Empty:
                    self._outputs.remove(s)
                else:
                    s.send(response)

            for s in exceptional:
                self._inputs.remove(s)
                if s in self._outputs:
                    self._outputs.remove(s)
                s.shutdown(0)
                del self._message_queues[s]

    def stop(self):
        # The 1st socket in the inputs list is the main server, don't
        # close that one until the end
        for s in self._inputs[1:]:
            s.shutdown(1)
        for s in self._outputs:
            s.shutdown(1)
        self._socket = None
        self._message_queues = {}
        self._outputs = []
        self._inputs = []

    def _request_handler(self, s, request):
        resp = ''
        if request == 'l4_ping':
            resp = 'OK <l4_ping>'
            self._message_queues[s].put(resp)
        elif request == 'shutdown':
            logging.info('TCPServer thread: Received a shutdown message! Goodbye.')
            resp = 'OK <shutdown>'
            self._message_queues[s].put(resp)
        else:
            resp = self._message_callback(request)
            if resp and resp != '':
                self._message_queues[s].put(resp)
            else:
                logging.warning('TCPServer thread: Unknown request received from %s:%s [%s]',
                                s.getpeername()[0], s.getpeername[1], request)
                self._message_queues[s].put('WARNING: server got an unknown request from you: "%s"' % request)
        return resp

        
def message_handler(message):
    """Call back for dealing with incoming messages over the server's socket. Put all the command 
    responses you want here."""
    
    ret_val = 'NOK <unrecognised command>'
    if message == 'hndlr_ping':
        ret_val = 'OK <hndlr_ping>'
    #
    # add more APIs here
    #
    return ret_val

def tcp_send(msg, to_host, to_port):
    """Helper method to send brief TCP payloads to IP hosts and retrieve a response"""
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((to_host, int(to_port)))
    sock.sendall(msg.encode('utf-8'))
    resp = sock.recv(1024).decode('utf-8')
    sock.shutdown(0)
    return resp
    

def ping(host, show_stdout=False, num_pings=1):
    """Ping an IP host by sending at most `num_pings=1` packets."""
    
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    cmd = 'ping' if platform.system().lower() == 'windows' else '/sbin/ping'
    param += ' %d' % num_pings
    command = ' '.join([cmd, param, host])
    if show_stdout is False:
        ret = subprocess.call(command, stdout=subprocess.PIPE)
    else:
        ret = subprocess.call(command)
    return ret == 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with TCPServer('127.0.0.1', 9999, message_handler) as serv:
        resp = tcp_send('l4_ping', '127.0.0.1', 9999)
        assert resp == 'OK <l4_ping>', 'Invalid or no response from server'
        print(resp + '\n')
        
        resp = tcp_send('hndlr_ping', '127.0.0.1', 9999)
        assert resp == 'OK <hndlr_ping>', 'Invalid or no response from server'
        print(resp + '\n')
        
        print('Success!!')
