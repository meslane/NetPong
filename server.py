import socket
import select
import threading
import queue
import random
import struct
import time

import packet

def init_socket(sock):
    #sock.settimeout(5)
    sock.setblocking(False)
    
class Server:
    def __init__(self, port, **kwargs):
        self.port = port
        self.sock = socket.socket()
        self.state = packet.GamePacket() #current game state to be sent to users
        
        self.ball_subpixel = (80,45) #float vector to convert to int for sending out state
        self.ball_velocity = (1,0) #vector describing ball velocity
        
        self.last_tx = 0
        self.tx_interval = 0.033
        
        self.users = [] #list of user sockets
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
            self.users.append(conn)
            init_socket(conn)
            print("Connection Accepted!")
    
    #server tick function
    def tick(self):
        loop_time = time.time()
    
        user_packet = packet.PlayerPacket(None, None)
        
        try:
            if len(self.users) > 0:
                r, w, e = select.select(self.users, self.users, self.users, 1)
            
                for user in r: #readable sockets
                    user_index = self.users.index(user)
                
                    try:
                        user_packet.unpack_bytes(user.recv(18))
                        name_str = user_packet.name.rstrip(b'\x00').decode("utf_8")
                        
                        if user_index == 0:
                            self.state.p1y = user_packet.pos
                            self.state.p1_name = name_str
                        elif user_index == 1:
                            self.state.p2y = user_packet.pos
                            self.state.p2_name = name_str
                    except ConnectionResetError:
                        self.users.remove(user)
                        
                        if user_index == 0:
                            self.state.p1_name = ""
                        elif user_index == 1:
                            self.state.p2_name = ""
                        
                        print("Disconnected User")
                    
                    #print(user_packet)
                    
                '''
                Do Game Logic
                '''
                if loop_time - self.last_tx >= self.tx_interval:
                    
                
                    for user in w: #writable sockets 
                        user.sendall(self.state.pack_bytes())
                        
                    self.last_tx = loop_time

        except KeyboardInterrupt:
            print("Keyboard interrupt: killing server")
            exit()
        
if __name__ == '__main__':
    s = Server(10000)
    s.state.ball = (80,45)
    s.start()
    
    s.listen()
    print("Waiting for connections...")
    
    s.connection_thread.start()
        
    while True:
        s.tick()
    
    print("Exiting...")