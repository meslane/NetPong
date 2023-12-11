import pygame
import socket
import time
import threading
import queue
import random

import packet
import gui

background_color = (20, 20, 20)
w_screen = 320
h_screen = 180

class Game:
    def __init__(self, **kwargs):
        self.color = kwargs.get('color', (255,255,255))
    
        self.ball = pygame.Rect(0, 0, 1, 1)
        self.state = packet.GamePacket()
    
    #take packet data and use it to draw the game surface
    def draw(self, surface):
        #draw ball
        self.ball.center = self.state.ball
        pygame.draw.rect(surface, self.color, self.ball)

class Player:
    def __init__(self, username):
        self.name = username
        self.sock = socket.socket()
    
        self.timeout = 5 #socket timeout
    
        self.tx = queue.Queue() #outgoing packet queue
        self.rx = queue.Queue() #incoming packet queue
        self.state = queue.Queue() #thread state queue
        
        self.net_thread = None
    
        self.y = 0 #paddle y position
    
    #connect to server
    def connect(self, ip, port):
        self.sock.connect((ip, port))
    
    def close(self):
        self.sock.close()

    def network_thread(self, ip, port, username):
        network_state = "Connecting"

        p = Player(username)
        
        player_packet = packet.PlayerPacket(self.name, self.y)

        count = 0
    
        print("Starting loop")
        while True:
            #broadcase state
            self.state.put_nowait(network_state)
        
            #actions + transitions
            if network_state == "Connecting":
                try:
                    p.connect(ip, port)
                    network_state = "Connected"
                except (ConnectionRefusedError, TimeoutError):
                    network_state = "Failed"
            elif network_state == "Connected":
                try:
                    server_packet = packet.GamePacket()
                    p.sock.sendall(player_packet.pack_bytes())
                    server_packet.unpack_bytes(p.sock.recv(64))
                    
                    self.rx.put_nowait(server_packet) #send rx packet out of thread
                    #count += 1
                    #print(count)
                except ConnectionResetError:
                    network_state = 'Failed'
            elif network_state == "Failed":
                break
        
        p.close()
    
    def start_thread(self, ip, port): #init networking thread
        self.sock.settimeout(self.timeout)
        self.net_thread = threading.Thread(target = self.network_thread, 
                                                args = (ip, port, self.name),
                                                daemon = True)
        self.net_thread.start()

def main():
    #setup
    pygame.init()
    pygame.display.set_caption("NetPong")
    
    window = pygame.display.set_mode([w_screen,h_screen], pygame.RESIZABLE)
    screen = pygame.Surface((w_screen,h_screen))
    
    font = pygame.font.SysFont("Consolas", 14)
    big_font = pygame.font.SysFont("Consolas", 20)
    
    #load logo
    logo_scale = 4
    logo = pygame.image.load('logo.png')
    logo = pygame.transform.scale(logo, (logo_scale * logo.get_width(), logo_scale * logo.get_height()))
    
    #text boxes
    ip_text = gui.Text("Server IP", (w_screen//2 - 80, h_screen//2 - 15), font)
    ip_box = gui.TextBox((w_screen//2 + 40, h_screen//2 - 15), (140,15),
                        text = "127.0.0.1",
                        max_chars = 15)
                        
    name_text = gui.Text("Username", (w_screen//2 - 80, h_screen//2 + 15), font)
    name_box = gui.TextBox((w_screen//2 + 40, h_screen//2 + 15), (140,15),
                        text = '',
                        max_chars = 16)
    
    connecting_text = big_font.render("Connecting...", False, (255,255,255))
    
    failed_text = big_font.render("Connection Failed", False, (128, 0, 0))
    
    success_text = big_font.render("Connected", False, (255,255,255))
    
    #start button
    start_button = gui.Button((w_screen//2, h_screen//2 + 60), (60,15),
                            text = "Connect",
                            callback = None)
    
    #ok button for failed menu
    fail_ok_button = gui.Button((w_screen//2, h_screen//2 + 30), (60,15),
                            text = "OK",
                            callback = None)
                            
    #pause menu buttons
    pause_resume_button = gui.Button((w_screen//2, h_screen//2 - 30), (60,15),
                            text = "Resume",
                            callback = None)
    
    pause_quit_button = gui.Button((w_screen//2, h_screen//2 + 30), (60,15),
                            text = "Quit",
                            callback = None)
    
    #pre-loop
    state = "Menu"
    run = True
    
    #player class
    client = Player('')
    client_net_state = None
    
    game = Game()
    
    while run:
        key_event = None
        
        #cover screen
        screen.fill(background_color)
        
        #handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                key_event = event
    
        #grab client thread state
        while not client.state.empty():
            client_net_state = client.state.get_nowait()
    
        #state machine (transitions)
        if state == "Menu":
            if start_button.clicked:
                client.name = name_box.text
                client.start_thread(ip_box.text, 10000)
                state = "Connect"
        elif state == "Connect":
            if client_net_state == "Connected":
                state = "Game"
            elif client_net_state == "Failed":
                state = "Failed"
        elif state == "Game":
            if client_net_state == "Connected":
                state = "Game"
                if key_event and key_event.key == pygame.K_ESCAPE: #pause if user hits escape key
                    state = "Pause"
            else:
                state = "Failed"
            pass
        elif state == "Failed":
            if fail_ok_button.clicked:
                state = "Menu"
        elif state == "Pause":
            if pause_resume_button.clicked:
                state = "Game"
            elif pause_quit_button.clicked:
                state = "Menu"
    
        #state machine (actions)
        if state == "Menu":
            #draw logo
            screen.blit(logo, (w_screen//2 - logo.get_width()//2, 
                                h_screen//2 - logo.get_height()//2 - 60))
            
            #input boxes
            ip_text.draw(screen)
            ip_box.draw(screen, key_event, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
           
            name_text.draw(screen)
            name_box.draw(screen, key_event, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
            
            #start button
            start_button.draw(screen, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
    
        elif state == "Connect":
            connecting_text_rect = connecting_text.get_rect(center = (w_screen//2, h_screen//2))
            screen.blit(connecting_text, connecting_text_rect)
    
        elif state == "Game":
            #update state if new data is available
            if not client.rx.empty():
                game.state = client.rx.get_nowait()
            
            game.draw(screen)
        elif state == "Failed":
            failed_text_rect = failed_text.get_rect(center = (w_screen//2, h_screen//2))
            screen.blit(failed_text, failed_text_rect)
            
            fail_ok_button.draw(screen, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
        elif state == "Pause":
            pause_resume_button.draw(screen, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
            
            pause_quit_button.draw(screen, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
    
        #draw window
        window.blit(pygame.transform.scale(screen, window.get_rect().size), (0, 0))
        pygame.display.flip()

if __name__ == '__main__':
    main()