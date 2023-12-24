import socket
import select
import threading
import random
import struct
import time
import math

import packet

def vec2add(a, b):
    return (a[0] + b[0], a[1] + b[1])

def vec2mul(a, b):
    return (a[0] * b[0], a[1] * b[1])

def vec2scalarmul(a, b):
    return (a * b[0], a * b[1])

def vec2div(a,b):
    return (a[0] / b[0], a[1] / b[1])

def vec2quantize(a):
    return (int(a[0]), int(a[1]))
    
def vec2mag(a): #returns scalar
    return math.sqrt(a[0] ** 2 + a[1] ** 2)

def init_socket(sock):
    #sock.settimeout(5)
    sock.setblocking(False)

class Server:
    def __init__(self, port, **kwargs):
        self.port = port
        self.sock = socket.socket()
        self.state = packet.GamePacket() #current game state to be sent to users
        self.state.server = 3
        
        self.ball_subpixel = (-2,-2) #float vector to convert to int for sending out state
        self.ball_velocity = (0,0) #vector describing ball velocity
        
        self.w_court = 160
        self.h_court = 90
        self.paddle_sep = 5
        self.paddle_len = 9
        
        self.last_tx = 0
        self.tx_interval = 0.033
        
        self.last_tick = 0
        self.tick_interval = 0.01
        
        self.last_hit = 0
        self.hit_interval = 0.2
        
        self.end_start = 0
        self.end_interval = 5
        
        self.users = [] #list of user sockets
        self.open = True
        
        self.p1_key = 0 #user key presses (for serving)
        self.p2_key = 0
        
        self.win_score = 10
        
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
    
    #only call during a hit
    def get_velocity_from_hit(self, player_y, ball_pos, ball_v):
        v = vec2mul(ball_v, (-1,1))
        m = vec2mag(v) #vector magnitude
        v_x = v[0] / abs(v[0])#1 = right, -1 = left
    
        if abs(player_y - ball_pos[1]) <= self.paddle_len/6: #center hit (center 1/3 of paddle)
            return (m * v_x, 0) #go straight
        elif player_y - ball_pos[1] < 0: #if ball is below
            return (m * v_x * 1/math.sqrt(2), m * 1/math.sqrt(2)) #go down
        elif player_y - ball_pos[1] > 0: #if ball is above
            return (m * v_x * 1/math.sqrt(2), m * -1/math.sqrt(2)) #go up
    
    #server tick function
    def tick(self):
        loop_time = time.time()
    
        user_packet = packet.PlayerPacket(None, None)
        
        '''
        Server State Machine:
        -0 = game
        -1 = p1_serve
        -2 = p2_serve
        -3 = waiting
        -4 = end
        '''
        try:
            if len(self.users) > 0:
                r, w, e = select.select(self.users, self.users, self.users, 1)
            
                for user in r: #readable sockets
                    user_index = self.users.index(user)
                
                    try:
                        user_packet.unpack_bytes(user.recv(user_packet.length))
                        name_str = user_packet.name.rstrip(b'\x00').decode("utf_8")
                        
                        if user_index == 0:
                            self.state.p1y = user_packet.pos
                            self.state.p1_name = name_str
                            self.p1_key = user_packet.key
                        elif user_index == 1:
                            self.state.p2y = user_packet.pos
                            self.state.p2_name = name_str
                            self.p2_key = user_packet.key
                    except (ConnectionResetError, struct.error):
                        self.users.remove(user)
                        
                        if user_index == 0:
                            if len(self.users) > 0:
                                self.state.p1_name = self.state.p2_name
                                self.state.score = (self.state.score[1], self.state.score[0])
                                self.state.p2_name = ""
                            else:
                                self.state.p1_name = ""
                        elif user_index == 1:
                            self.state.p2_name = ""
                        
                        print("Disconnected User")
                    
                '''
                Do Game Logic + State machine
                '''
                if loop_time - self.last_tick >= self.tick_interval:
                    '''
                    State machine transitions
                    '''
                    if self.state.server == 0:
                        #out of bounds
                        if self.ball_subpixel[0] < 0: #out on player 1
                            self.ball_subpixel = (80,100)
                            self.state.score = vec2add(self.state.score,(0,1))
                            self.state.server = 2
                        elif self.ball_subpixel[0] > self.w_court: #out on player 2
                            self.ball_subpixel = (80,100)
                            self.state.score = vec2add(self.state.score,(1,0))
                            self.state.server = 1
                            
                        if self.state.score[0] > self.win_score or self.state.score[1] > self.win_score:
                            self.end_start = loop_time
                            self.state.server = 4 #win mode
                    elif self.state.server == 1:
                        if len(self.users) < 2:
                            self.state.server = 3
                        elif self.p1_key == 32:
                            self.ball_subpixel = (self.paddle_sep + 1, self.state.p1y)
                            self.ball_velocity = (1,0)
                            self.state.server = 0
                            self.p1_key = 0
                    elif self.state.server == 2:
                        if len(self.users) < 2:
                            self.state.server = 3
                        elif self.p2_key == 32:
                            self.ball_subpixel = (self.w_court - self.paddle_sep - 1, self.state.p2y)
                            self.ball_velocity = (-1,0)
                            self.state.server = 0
                            self.p2_key = 0
                    elif self.state.server == 3: #wait for players
                        if len(self.users) >= 2:
                            self.state.server = 1 #start game
                    elif self.state.server == 4: #end
                        if loop_time - self.end_start > self.end_interval:
                            #determine who serves first based on winner
                            if self.state.score[0] > self.state.score[1] and len(self.users) >= 2:
                                self.state.server = 1
                            elif self.state.score[1] > self.state.score[0] and len(self.users) >= 2:
                                self.state.server = 2
                            else:
                                self.state.server = 3
                                
                            self.state.score = (0,0)
                            self.state.ball = (80,100)
                            self.p1y = 45
                            self.p2y = 45
                    '''
                    State machine actions
                    '''
                    if self.state.server == 0: #game
                        self.ball_subpixel = vec2add(self.ball_subpixel, self.ball_velocity)
                            
                        #wall bounce
                        if self.ball_subpixel[1] <= 0 or self.ball_subpixel[1] >= self.h_court:
                            self.ball_velocity = vec2mul(self.ball_velocity, (1,-1))
                    
                        #paddle hit (left)
                        if int(self.ball_subpixel[0]) == self.paddle_sep:
                            if abs(self.state.p1y - self.ball_subpixel[1]) <= self.paddle_len/2 and (loop_time - self.last_hit) > self.hit_interval:
                                self.ball_velocity = self.get_velocity_from_hit(self.state.p1y,
                                                                            self.ball_subpixel,
                                                                            self.ball_velocity)
                                self.last_hit = loop_time                                               
                        #paddle hit (right)
                        elif int(self.ball_subpixel[0]) == self.w_court - self.paddle_sep:
                            if abs(self.state.p2y - self.ball_subpixel[1]) <= self.paddle_len/2 and (loop_time - self.last_hit) > self.hit_interval:
                                self.ball_velocity = self.get_velocity_from_hit(self.state.p2y,
                                                                            self.ball_subpixel,
                                                                            self.ball_velocity)
                                self.last_hit = loop_time
                    elif self.state.server == 1: #p1 serve
                        pass
                    elif self.state.server == 2: #p2 serve
                        pass
                    elif self.state.server == 3: #waiting for players
                        pass
                    elif self.state.server == 4:
                        pass
                    
                    '''
                    Universal Actions
                    '''
                    self.state.ball = vec2quantize(self.ball_subpixel)
                    
                    self.last_tick = loop_time
                
                '''
                Send updates to users
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