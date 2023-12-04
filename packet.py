import socket
import struct

'''
Incoming packet format:
    -user ID
    -user position (y)

Outgoing packet format:
    -ball position (x, y)
    -user #1 position (y)
    -user #2 position (y)
    -user score (p1, p2)
'''


'''
Base packet class
'''
class Packet:
    def __init__(self):
        self.packstring = None
        
    def pack_bytes():
        return None
    
    def unpack_bytes():
        return None
        
'''
Server -> Client Packet
'''
class GamePacket(Packet):
    def __init__(self):
        self.packstring = 'hhhhBB'
    
        self.ball = (0,0) #ball position (x, y)
        self.p1 = 0 #player 1 y coordinate
        self.p2 = 0 #player 2 y coordinate
        self.score = (0,0) #player score (p1, p2)
        
    def pack_bytes(self):
        return struct.pack(self.packstring, 
                            self.ball[0], self.ball[1], 
                            self.p1, self.p2, 
                            self.score[0], self.score[1])
    
    def unpack_bytes(self, raw):
        data = struct.unpack(self.packstring, raw)
        
        self.ball = (data[0], data[1])
        self.p1 = data[2]
        self.p2 = data[3]
        self.score = (data[4], data[5])
        
    def __str__(self):
        return "Ball: {}, P1: {}, P2: {}, Score: {}".format(self.ball, self.p1, self.p2, self.score)

'''
Client -> Server Packet
'''
class PlayerPacket(Packet):
    def __init__(self):
        self.packstring = 'Bh'
        
        self.player = 1 #p1 or p2
        self.pos = 0 #y position
        
    def pack_bytes(self):
        return struct.pack(self.packstring, self.player, self.pos)
    
    def unpack_bytes(self, raw):
        data = struct.unpack(self.packstring, raw)
        self.player, self.pos = data
        
    def __str__(self):
        return "Player {}, Pos: {}".format(self.player, self.pos)
    
if __name__ == '__main__':
    packet = GamePacket()
    packet.ball = (123, 45)
    packet.score = (3, 4)
    print(packet)
    
    b = packet.pack_bytes()
    
    print(b)
    
    packet2 = GamePacket()
    packet2.unpack_bytes(b)
    print(packet2)
    
    
    p3 = PlayerPacket()
    p4 = PlayerPacket()
    
    p3.player = 2
    p3.pos = 69
    
    b = p3.pack_bytes()
    print(b)
    
    p4.unpack_bytes(b)
    print(p4)
    