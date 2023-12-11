import socket
import threading
import queue
import random

import packet

class User:
    def __init__(self, **kwargs):
        self.sock = kwargs.get('sock', None) #client connection object
        self.addr = kwargs.get('addr', None) #client address

        self.tx = queue.Queue() #outgoing packet queue
        self.rx = queue.Queue() #incoming packet queue
        
        self.timeout = 5
        self.open = True #TEMPORARY
        
        self.user_thread = threading.Thread(target = self.loop, daemon = True)
    
    def init_socket(self):
        self.sock.settimeout(self.timeout) #timeout after 1 sec
        self.open = True
    
    def loop(self): #TX/RX loop
        while self.open == True:
            try:
                p = self.sock.recv(1024)
                self.rx.put(p) #grab player state into RX queue
                
                if p == b'': #close loop if client died
                    print("Client closed connection")
                    self.close()
                    break
            except (socket.timeout, ConnectionResetError):
                print("User timed out, closing connection")
                self.rx.put(b'') #send swan song to avoid crashing main loop
                self.close() #close socket if timed out
                break
                
            t = self.tx.get(timeout=1)
            self.sock.sendall(t) #send latest game state from TX queue
           
            while not self.tx.empty(): #clear queue to avoid sending old data
                self.tx.get_nowait()
    
    def start_thread(self):
        self.user_thread.start()
        
    def join_thread(self):
        self.user_thread.join()
    
    def close(self):
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
            #update game state
            s.state.ball = (random.randint(0,160), random.randint(0,90))
            s.state.p1y = random.randint(0,90)
            s.state.p2y = random.randint(0,90)
            s.state.p1_name = 'Player 1'
            s.state.p2_name = 'Player 2'
        
            #remvoe inactive users
            for i in range(len(self.users) -1, -1, -1): #go backwards to delete
                if self.users[i].open == False:
                    self.users[i].join_thread()
                    del self.users[i]
                    print("removed user")
            
            #respond to users
            for user in s.users:
                if not user.rx.empty():
                    user.rx.get_nowait() #respond if got packet
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