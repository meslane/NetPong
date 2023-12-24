import socket
import struct

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
        self.packstring = 'hhhh16s16sBBB'
    
        self.ball = (0,0) #ball position (x, y)
        self.p1y = 0 #player 1 y coordinate
        self.p2y = 0 #player 2 y coordinate
        self.p1_name = " "
        self.p2_name = " "
        self.score = (0,0) #player score (p1, p2)
        self.server = 0 #0 = game, 1 = p1, 2 = p2, 3 = waiting, 4 = end
        
        self.length = struct.calcsize(self.packstring)
        
    def pack_bytes(self):
        return struct.pack(self.packstring,
                            self.ball[0], self.ball[1], 
                            self.p1y, self.p2y,
                            bytes(self.p1_name, 'utf-8'), bytes(self.p2_name, 'utf-8'),
                            self.score[0], self.score[1],
                            self.server)
    
    def unpack_bytes(self, raw):
        data = struct.unpack(self.packstring, raw)
        
        self.ball = (data[0], data[1])
        self.p1y = data[2]
        self.p2y = data[3]
        self.p1_name = data[4]
        self.p2_name = data[5]
        self.score = (data[6], data[7])
        self.server = data[8]
        
    def __str__(self):
        return "Ball: {}, P1 Y: {}, P2 Y: {}, P1: {}, P2: {}, Score: {}, Server".format(self.ball, 
                                                                                        self.p1y, self.p2y, 
                                                                                        self.p1_name, self.p2_name, 
                                                                                        self.score, 
                                                                                        self.server)

'''
Client -> Server Game Packet
'''
class PlayerPacket(Packet):
    def __init__(self, username, pos):
        self.packstring = '16shB'
        
        self.name = username #p1 or p2
        self.pos = pos #y position
        self.key = 0
        
        self.length = struct.calcsize(self.packstring)
        
    def pack_bytes(self):
        return struct.pack(self.packstring, bytes(self.name, 'utf-8'), self.pos, self.key)
    
    def unpack_bytes(self, raw):
        data = struct.unpack(self.packstring, raw)
        self.name, self.pos, self.key = data
        
    def __str__(self):
        return "Username {}, Pos: {}".format(self.name, self.pos)