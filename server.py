import socket
import threading
import queue
import random
import struct

import packet

class User:
    def __init__(self, **kwargs):
        self.sock = kwargs.get('sock', None) #client connection object
        self.addr = kwargs.get('addr', None) #client address

        self.tx = queue.Queue() #outgoing packet queue
        self.rx = queue.Queue() #incoming packet queue
        
        self.timeout = 1
        self.open = True #TEMPORARY
        
        self.user_thread = threading.Thread(target = self.loop, daemon = True)
    
    def init_socket(self):
        self.sock.settimeout(self.timeout) #timeout after 1 sec
        self.sock.setblocking(False)
        self.open = True
    
    def loop(self): #TX/RX loop
        while self.open == True:
            #print("RX: {}, TX: {}".format(self.rx.qsize(), self.tx.qsize()))
        
            try:
                p = self.sock.recv(18)
                self.rx.put_nowait(p) #grab player state into RX queue
                
                if p == b'': #close loop if client died
                    print("Client closed connection")
                    self.close()
                    break
            except socket.error: #if not timed out but no data
                pass
            except (socket.timeout, ConnectionResetError):
                print("User timed out, closing connection")
                self.close() #close socket if timed out
                break
            
            try:
                t = self.tx.get(timeout=1)
                self.sock.sendall(t) #send latest game state from TX queue
            except (ConnectionResetError):
                print("User timed out, closing connection")
                self.close() #close socket if timed out
                break
           
            while not self.tx.empty(): #clear queue to avoid sending old data
                self.tx.get_nowait()
    
    def start_thread(self):
        self.user_thread.start()
        
    def join_thread(self):
        self.user_thread.join()
    
    def close(self):
        self.rx.put_nowait(b'') #send swan song to avoid crashing main loop
        self.open = False
        self.sock.close()

class Server:
    def __init__(self, port, **kwargs):
        self.port = port
        self.sock = socket.socket()
        self.state = packet.GamePacket() #current game state to be sent to users
        
        self.users = []
        self.open = True
        
        self.connection_thread = threading.Thread(target = self.await_connection, daemon = True)
        
    def start(self):
        self.sock.bind(('',self.port))
    
    def listen(self):
        self.sock.listen()
    
    def accept(self):
        return self.sock.accept()
    
    def await_connection(self): #wait for connection and spawn user when connected
        while self.open == True:
            conn, addr = self.sock.accept()
            self.users.append(User(sock=conn, addr=addr))
            self.users[-1].init_socket()
            print("Connection Accepted!")
            self.users[-1].start_thread()
    
    #server tick function
    def tick(self):
        try:
            #remove inactive users
            for i in range(len(self.users) -1, -1, -1): #go backwards to delete
                if self.users[i].open == False:
                    self.users[i].join_thread()
                    del self.users[i]
                    print("removed user")
                    
                    if i == 0:
                        s.state.p1_name = ""
                    elif i == 1:
                        s.state.p2_name = ""
            
            #get data, respond to users
            for i, user in enumerate(s.users):
                user_packet = packet.PlayerPacket(None, None)
            
                if not user.rx.empty():
                    try:
                        user_packet.unpack_bytes(user.rx.get_nowait()) #respond if got packet
                    
                        name_str = user_packet.name.rstrip(b'\x00').decode("utf_8")
                        
                        if i == 0:
                            s.state.p1y = user_packet.pos
                            s.state.p1_name = name_str
                        elif i == 1:
                            s.state.p2y = user_packet.pos
                            s.state.p2_name = name_str
                    except struct.error:
                        print("ERROR: attempting to unpack incomplete packet")
                
                user.tx.put_nowait(s.state.pack_bytes())
        except KeyboardInterrupt:
            print("Keyboard interrupt: killing server")
            for user in s.users:
                user.join_thread()
            exit()
        
if __name__ == '__main__':
    s = Server(10000)
    s.start()
    
    s.listen()
    print("Waiting for connections...")
    
    s.connection_thread.start()
        
    while True:
        s.tick()
    
    print("Exiting...")