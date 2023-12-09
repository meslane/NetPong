import pygame
import socket
import time
import packet

import random

background_color = (20, 20, 20)
w_screen = 320
h_screen = 180

class Button(pygame.Rect):
    def __init__(self, pos, size, **kwargs):
        super().__init__(pos, size)
        self.center = pos
        
        self.text = kwargs.get('text', None)
        
        if self.text:
            self.text_rect = self.text.get_rect(center = self.center)
        else:
            self.text_rect = None
        
        self.color = kwargs.get('color', (255,255,255))
        self.hover_color = kwargs.get('hover_color', (200,200,200))
        self.click_color = kwargs.get('click_color', (150,150,150))
        
    def draw(self, surface, **kwargs):
        draw_color = self.color
        
        scale = kwargs.get('scale', (1.0,1.0))
        
        if self.collidepoint((pygame.mouse.get_pos()[0] * scale[0], pygame.mouse.get_pos()[1] * scale[1])):
            draw_color = self.hover_color
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                draw_color = self.click_color
        
        pygame.draw.rect(surface, draw_color, self)
        
        if self.text:
            surface.blit(self.text, self.text_rect)

class TextBox(pygame.Rect):
    def __init__(self, pos, size, font, **kwargs)
        super().__init__(pos, size)
        self.center = pos
        
        self.text = kwargs.get('text', '')
        
        self.selected = False
        
        self.color = kwargs.get('color', (255,255,255))
        self.hover_color = kwargs.get('hover_color', (200,200,200))
        self.click_color = kwargs.get('click_color', (150,150,150))
        
        

class Player:
    def __init__(self, name):
        self.name = name
        self.sock = socket.socket()
    
    #connect to server
    def connect(self, ip, port):
        self.sock.connect((ip, port))
    
    def close(self):
        self.sock.close()
        
def main():
    #setup
    pygame.init()
    pygame.display.set_caption("NetPong")
    
    window = pygame.display.set_mode([w_screen,h_screen], pygame.RESIZABLE)
    screen = pygame.Surface((w_screen,h_screen))
    
    font = pygame.font.SysFont("Consolas", 14)
    
    #load logo
    logo_scale = 4
    logo = pygame.image.load('logo.png')
    logo = pygame.transform.scale(logo, (logo_scale * logo.get_width(), logo_scale * logo.get_height()))
    
    #button
    start_button = Button((w_screen//2, h_screen//2 + 60), (60,15),
                            text = font.render("Connect", False, (20, 20, 20)))
    
    #pre-loop
    state = "Menu"
    run = True
    
    while run:
        #print((w_screen / window.get_width(), h_screen / window.get_height()))
    
        #cover screen
        screen.fill(background_color)
        
        #handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
    
        #state machine
        if state == "Menu":
            #draw logo
            screen.blit(logo, (w_screen//2 - logo.get_width()//2, 
                                h_screen//2 - logo.get_height()//2 - 60))
                                
            start_button.draw(screen, scale=(w_screen / window.get_width(), 
                                        h_screen / window.get_height()))
    
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