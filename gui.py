import pygame

class Text:
    def __init__(self, text, pos, font, **kwargs):
        self.pos = pos
        self.font = font
        self.text = text
        
        self.color = kwargs.get('color', (255,255,255))
        
    def draw(self, surface):
        text_render = self.font.render(self.text, False, self.color)
        text_rect = text_render.get_rect(center = self.pos)
        surface.blit(text_render, text_rect)

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
        if self.callback:
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