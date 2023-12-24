import pygame
import socket
import select
import time
import threading
import queue
import random

import packet
import gui

background_color = (20, 20, 20)
w_screen = 320
h_screen = 180

paddle_sep = 10
paddle_len = 9

class Game:
    def __init__(self, **kwargs):
        self.color = kwargs.get('color', (255,255,255))
    
        self.state = packet.GamePacket()
        self.sock = socket.socket()
        
        self.connect_thread = None
        self.connect_state = "Attempt" #Attempt, Connected, Fail
        self.connect_state_queue = queue.Queue()
        
        self.ball = pygame.Rect(0, 0, 2, 2)
        self.left_paddle = pygame.Rect(0,0,2,2*paddle_len)
        self.right_paddle = pygame.Rect(0,0,2,2*paddle_len)
        
        self.font = pygame.font.SysFont("Consolas", 14)
        self.big_font = pygame.font.SysFont("Consolas", 20)
        
        self.player1_name = gui.Text('', (w_screen//2 - 90, h_screen - 20), 
                                    self.font, color = (100,100,100))
        self.player2_name = gui.Text('', (w_screen//2 + 90, h_screen - 20), 
                                    self.font, color = (100,100,100))
                                    
        self.player1_score = gui.Text('', (w_screen//2 - 100, 20), 
                                    self.big_font, color = (100,100,100))
        self.player2_score = gui.Text('', (w_screen//2 + 100, 20), 
                                    self.big_font, color = (100,100,100))
        
        self.arrow = pygame.image.load('arrow.png')
        
        self.last_update = 0
        self.update_interval = 0.01 
    
    def attempt_connection(self, ip, port):
        self.connect_thread = threading.Thread(target = self.await_connection,
                                            args = (ip, port),
                                            daemon = True)
        self.connect_thread.start()
        
    def await_connection(self, ip, port):
        try:
            self.sock = socket.socket()
            self.sock.connect((ip, port))
            self.sock.setblocking(False)
            self.connect_state_queue.put("Connected")
        except (ConnectionRefusedError, TimeoutError, socket.gaierror, OSError):
            self.connect_state_queue.put("Failed")
    
    #take packet data and use it to draw the game surface
    def draw(self, surface):
        #draw ball
        self.ball.center = (self.state.ball[0] * 2, self.state.ball[1] * 2)
        self.left_paddle.center = (paddle_sep, self.state.p1y * 2)
        self.right_paddle.center = (w_screen - paddle_sep, self.state.p2y * 2)
        
        try: #convert from bytes and fail over to string otherwise
            self.player1_name.text = self.state.p1_name.rstrip(b'\x00').decode("utf_8")
            self.player2_name.text = self.state.p2_name.rstrip(b'\x00').decode("utf_8")
        except TypeError:
            self.player1_name.text = self.state.p1_name
            self.player2_name.text = self.state.p2_name
           
        self.player1_score.text = '{}'.format(self.state.score[0])
        self.player2_score.text = '{}'.format(self.state.score[1])
        
        self.player1_name.draw(surface)
        self.player2_name.draw(surface)

        self.player1_score.draw(surface)
        self.player2_score.draw(surface)
        
        if self.state.server != 0:
            if self.state.server == 1:
                arrow_x = -100
            else:
                arrow_x = 100
        
            surface.blit(self.arrow, (w_screen//2 - self.arrow.get_width()//2 + arrow_x, 
                                h_screen//2 - self.arrow.get_height()//2 - 85))
    
        pygame.draw.rect(surface, self.color, self.ball)
        pygame.draw.rect(surface, self.color, self.left_paddle)
        pygame.draw.rect(surface, self.color, self.right_paddle)

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
    
    connecting_text = gui.Text("Connecting...", (w_screen//2, h_screen//2), big_font)
    
    failed_text = gui.Text("Connection Failed", (w_screen//2, h_screen//2), big_font, color = (128,0,0))
    
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
    
    game = Game()
    
    i = 0
    player_y = 45
    last_y = 0
    player_key = 0
    last_key = 0
    
    connect_thread = None
    while run:
        #cover screen
        screen.fill(background_color)
        
        #handle events
        key_event = None #contains current keypress
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                key_event = event
    
        '''
        State Machine Transitions
        '''
        if state == "Menu":
            if start_button.clicked:
                player_y = 45
                last_y = 0
                game.attempt_connection(ip_box.text, 10000)
                state = "Connect"
        elif state == "Connect":
            if not game.connect_state_queue.empty(): #if finished
                state = game.connect_state_queue.get()
                
                if state == "Connected":
                    state = "Game"
                elif state == "Failed":
                    state = "Failed"
        elif state == "Game":
            state = "Game"
            if key_event and key_event.key == pygame.K_ESCAPE: #pause if user hits escape key
                state = "Pause"
        elif state == "Failed":
            if fail_ok_button.clicked:
                state = "Menu"
        elif state == "Pause":
            if pause_resume_button.clicked:
                state = "Game"
            elif pause_quit_button.clicked:
                state = "Menu"
    
        '''
        State Machine Actions
        '''
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
            connecting_text.draw(screen)
        elif state == "Game":
            if time.time() - game.last_update > game.update_interval:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_UP]: #move up
                    if player_y > 0:
                        player_y -= 1
                elif keys[pygame.K_DOWN]: #move down
                    if player_y < h_screen // 2:
                        player_y += 1
                        
                if keys[pygame.K_SPACE]:
                    player_key = 32
                else:
                    player_key = 0
                        
                game.last_update = time.time()
            
            r, w, e = select.select([game.sock], [game.sock], [game.sock], 1)
            
            if r:
                try:
                    p = game.sock.recv(game.state.length)
                    game.state.unpack_bytes(p)
                except ConnectionResetError:
                    state = "Failed"
            if w and player_y != last_y or player_key != last_key:
                player_packet = packet.PlayerPacket(name_box.text, player_y)
                player_packet.key = player_key
                game.sock.sendall(player_packet.pack_bytes())
                last_y = player_y
                last_key = player_key
            
            game.draw(screen)
        elif state == "Failed":
            game.sock.close()
            failed_text.draw(screen)
            fail_ok_button.draw(screen, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
        elif state == "Pause":
            pause_resume_button.draw(screen, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
            
            pause_quit_button.draw(screen, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
    
        '''
        Draw Window
        '''
        window.blit(pygame.transform.scale(screen, window.get_rect().size), (0, 0))
        pygame.display.flip()
        
        i += 1

if __name__ == '__main__':
    main()