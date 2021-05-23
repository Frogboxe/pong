
from __future__ import annotations

import pygame

from vector import V, Vector


class ContextReset(Exception):
    pass

class PygContext:

    def __init__(self, screen):
        self.screen = screen
        self.outcode = 0

    def start(self):
        self.screen.new_context(self)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, execls, exeins, tb):
        self.screen.elements = []

    def starting(self):
        pass

    def mouse_move(self, event: pygame.event): pass
    def key_down(self, key: int): pass
    def key_up(self, key: int): pass
    def mouse_down(self, key: int, pos: tuple[int]): pass
    def mouse_up(self, key: int, pos: tuple[int]): pass
    def window_shown(self, event: pygame.event): pass
    def activated(self, event: pygame.event): pass
    def focussed(self, event: pygame.event): pass
    def video(self, event: pygame.event): pass
    def exposed(self, event: pygame.event): pass
    def typing(self, event: pygame.event): pass
    def unfocussed(self, event: pygame.event): pass
    def mouse_wheel(self, event: pygame.event): pass
    def resize(self, size: Vector): pass
    def post_init(self): pass
    def quit(self): pass
    def update(self): pass

