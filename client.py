import pygame
import socket
import time
import packet
import threading

import random

background_color = (20, 20, 20)
w_screen = 320
h_screen = 180

class Button(pygame.Rect):
    def __init__(self, pos, size, **kwargs):
        super().__init__(pos, size)
        self.center = pos
        
        self.text = kwargs.get('text', None)
        self.font = kwargs.get('font', pygame.font.SysFont("Consolas", 14))
        
        self.color = kwargs.get('color', (255,255,255))
        self.hover_color = kwargs.get('hover_color', (200,200,200))
        self.click_color = kwargs.get('click_color', (100,100,100))
        
        self.callback = kwargs.get('callback', None)
        self.callback_args = kwargs.get('callback_args', None)
        
        self.clicked = False
        
    def draw(self, surface, **kwargs):
        draw_color = self.color
        
        scale = kwargs.get('scale', (1.0,1.0))
        
        #check for clicks
        if self.collidepoint((pygame.mouse.get_pos()[0] * scale[0], pygame.mouse.get_pos()[1] * scale[1])):
            draw_color = self.hover_color
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                if not self.clicked:
                    self.clicked = True
            
                draw_color = self.click_color
            else:
                if self.clicked:
                    self.clicked = False
                    self.on_click_func() #trigger callback on falling edge
        else:
            self.clicked = False
        
        pygame.draw.rect(surface, draw_color, self)
        
        if self.text:
            text_render = self.font.render(self.text, False, (20, 20, 20))
            text_rect = text_render.get_rect(center = self.center)
            surface.blit(text_render, text_rect)

    def on_click_func(self):
        self.callback(self.callback_args)

class TextBox(Button):
    def __init__(self, pos, size, **kwargs):
        super().__init__(pos, size, **kwargs)
        
        self.text = kwargs.get('text', '')
        self.max_chars = kwargs.get('max_chars', 16)
        self.selected = False
    
    def draw(self, surface, event, **kwargs):
        draw_color = self.color
        scale = kwargs.get('scale', (1.0,1.0))
        
        #check for clicks
        if self.collidepoint((pygame.mouse.get_pos()[0] * scale[0], pygame.mouse.get_pos()[1] * scale[1])):
            draw_color = self.hover_color
            
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                self.selected = True
        else:
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                self.selected = False
        
        if self.selected and event != None:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif len(self.text) < self.max_chars:
                    self.text += event.unicode
        
        if self.selected:
            draw_color = self.click_color
        
        pygame.draw.rect(surface, draw_color, self)

        text_render = self.font.render(self.text, False, (20, 20, 20))
        text_rect = text_render.get_rect(center = self.center)
        surface.blit(text_render, text_rect)

def dummy_callback(*args):
    print("Click")

class Player:
    def __init__(self, name):
        self.name = name
        self.sock = socket.socket()
    
    #connect to server
    def connect(self, ip, port):
        self.sock.connect((ip, port))
    
    def close(self):
        self.sock.close()

def network_thread(ip, port, username):
    p = Player(username)
    p.connect(ip, port)
    
    dummy_packet = packet.PlayerPacket()
    
    try:
        while True:
            p.sock.sendall(dummy_packet.pack_bytes())
            print(p.sock.recv(1024))
            #time.sleep(0.5)
    except KeyboardInterrupt:
        exit()
    
    p.close()

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
    ip_text = font.render("Server IP", False, (255, 255, 255))
    ip_box = TextBox((w_screen//2 + 40, h_screen//2 - 15), (140,15),
                        text = "127.0.0.1",
                        max_chars = 15)
                        
    name_text = font.render("Username", False, (255,255,255))
    name_box = TextBox((w_screen//2 + 40, h_screen//2 + 15), (140,15),
                        text = '',
                        max_chars = 16)
    
    connecting_text = big_font.render("Connecting...", False, (255,255,255))
    
    failed_text = big_font.render("Connection Failed", False, (128, 0, 0))
    
    success_text = big_font.render("Connected", False, (255,255,255))
    
    #button
    start_button = Button((w_screen//2, h_screen//2 + 60), (60,15),
                            text = "Connect",
                            callback = dummy_callback)
    
    #pre-loop
    net_thread = None
    
    state = "Menu"
    run = True
    
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
    
        #state machine (transitions)
        if state == "Menu":
            if start_button.clicked:
                state = "Connect"
                net_thread = threading.Thread(target = network_thread, 
                                                args = (ip_box.text, 10000, name_box.text),
                                                daemon = True)
                net_thread.start()
        elif state == "Connect":
            if net_thread.is_alive():
                state = "Game"
            else:
                state = "Failed"
        elif state == "Game":
            if net_thread.is_alive():
                state = "Game"
            else:
                state = "Failed"
            pass
        elif state == "Failed":
            pass
    
        #state machine (actions)
        if state == "Menu":
            #draw logo
            screen.blit(logo, (w_screen//2 - logo.get_width()//2, 
                                h_screen//2 - logo.get_height()//2 - 60))
            
            #input boxes
            screen.blit(ip_text, (w_screen//2 - 120, h_screen//2 - 20))
            ip_box.draw(screen, key_event, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
            
            screen.blit(name_text, (w_screen//2 - 120, h_screen//2 + 9))
            name_box.draw(screen, key_event, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
            
            #start button
            start_button.draw(screen, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
    
        elif state == "Connect":
            connecting_text_rect = connecting_text.get_rect(center = (w_screen//2, h_screen//2))
            screen.blit(connecting_text, connecting_text_rect)
    
        elif state == "Game":
            success_text_rect = success_text.get_rect(center = (w_screen//2, h_screen//2))
            screen.blit(success_text, success_text_rect)
            
        elif state == "Failed":
            failed_text_rect = failed_text.get_rect(center = (w_screen//2, h_screen//2))
            screen.blit(failed_text, failed_text_rect)
    
        #draw window
        window.blit(pygame.transform.scale(screen, window.get_rect().size), (0, 0))
        pygame.display.flip()

if __name__ == '__main__':
    '''
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
    '''
    
    main()