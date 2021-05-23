
from __future__ import annotations

from functools import lru_cache

import pygame

from element import Element
from pyg import Screen, glog, log
from render import Render
from vector import V, Vector


class Text(Element):
    _text: str
    font: pygame.font.SysFont
    fontName: str="consolas"
    fontSize: int=14
    fontAllias: int=4
    fontColour: tuple[int]=(127, 127, 127)
    def __init__(self, screen: Screen, pos: Vector, text: str = "", background: Render = None, offset: Vector = V(0, 0)):
        super().__init__(screen, pos)
        # pushes font into cache
        self.background = background
        self.offset = offset
        if background is not None:
            self.collision = background.get_size()
        Text.get_font(self.fontSize, self.fontName)
        self.text = text
    
    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str):
        self._text = text
        self.textures = [self.background, Text.get_text(text, self.fontSize, self.fontName, self.fontAllias, self.fontColour, self.offset)]

    @staticmethod
    @lru_cache(maxsize=4)
    def get_font(size: int, font: str):
        return pygame.font.SysFont(font, size)

    @staticmethod
    def get_text(text: str, size: int, fontName: str, allias: int, colour: tuple[int], offset: Vector) -> pygame.Surface:
        font = Text.get_font(size, fontName)
        return Render(font.render(text, allias, colour), offset)

class Typable(Text):
    def __init__(self, screen: Screen, pos: Vector, text: str, chars: str, background: Render, maxLen: int = 30, offset: Vector = V(0, 0)):
        super().__init__(screen, pos, text, background=background, offset=offset)
        self.maxLen = maxLen
        self.collision = background.get_size()
        self.chars = chars

    def type(self, event: pygame.event):
        k, char = event.key, event.unicode
        if k == 8:
            # backspace pressed: remove last char
            self.text = self.text[:-1:]
        elif char in self.chars and len(self.text) < self.maxLen:
            self.text += char

class TypableNumeric(Typable):
    def __init__(self, screen, pos: Vector, text: str, background: Render, maxLen: int = 30, offset: Vector = V(0, 0)):
        super().__init__(screen, pos, text, chars="1234567890:.", background=background, maxLen=maxLen, offset=offset)
































