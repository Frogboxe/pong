
from __future__ import annotations

from dataclasses import dataclass

import pygame

from vector import Vector


class Render:
    """
    A pygame.Surface wrapped with a Vector to simply
    allow textures to have an offset from their parent's
    Vector pos. This is slotted.

    .texture: pygame.Surface
    .offset: Vector
    """

    texture: pygame.Surface
    offset: Vector

    __slots__ = ["texture", "offset"]

    def __init__(self, texture, offset):
        self.texture, self.offset = texture, offset

    def __repr__(self):
        return f"{self.__class__.__qualname__}{self.texture, self.offset}"
    
    def get_size(self):
        return self.texture.get_size()


