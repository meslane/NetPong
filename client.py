import socket
import time

import packet

class Player:
    def __init__(self, name):
        self.name = name
        self.sock = socket.socket()
    
    #connect to server
    def connect(self, ip, port):
        self.sock.connect((ip, port))
    
    def close(self):
        self.sock.close()

if __name__ == '__main__':
    p = Player("bingus")
    p.connect('127.0.0.1', 10000)
    
    dummy_packet = packet.PlayerPacket()
    
    try:
        while True:
            p.sock.sendall(dummy_packet.pack_bytes())
            print(p.sock.recv(1024))
            time.sleep(0.5)
    except KeyboardInterrupt:
        exit()
    
    p.close()