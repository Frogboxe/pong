
from __future__ import annotations

import pygame

from render import Render
from vector import V, Vector

class Element:
    """
    Simple drawable screen element. Has optional collision and multiple texture support
    (for layering).

    """

    _pos: Vector
    _textures: list[pygame.Surface]
    render: bool = True
    collision: Vector
    selectable: bool = False

    def __init__(self, screen, pos: Vector, collision: Vector = V(0, 0), texture=None):
        self.screen = screen
        self.screen.add_element(self)
        self.pos = pos
        self.collision = collision
        self._textures = [texture]

    def update(self, dt: float):
        pass

    def inside(self, vec: Vector) -> bool:
        """Return True when vec is inside the collision bounds of self"""
        vec1, vec2 = self.pos, self.pos + self.collision
        return (isinstance(vec, Vector)
            and vec1.x <= vec.x <= vec2.x
            and vec1.y <= vec.y <= vec2.y
        )

    def clicked(self):
        pass

    @property
    def textures(self) -> list[Render]:
        return self._textures

    @textures.setter
    def textures(self, textures: list[Render]):
        self._textures = textures

    @property
    def size(self) -> Vector:
        return V(*self.textures[-1].get_size())

    @size.setter
    def size(self, size: Vector):
        self._size = size

    @property
    def texture(self) -> Render:
        return self._textures[0]

    @texture.setter
    def texture(self, texture: Render):
        self._textures[0] = texture
        self.size = texture.get_size()

    @property
    def hasCollision(self) -> bool:
        return self.collision != V(0, 0)
    """
    @property
    def pos(self) -> Vector:
        return self._pos

    @pos.setter
    def pos(self, pos: Vector):
        self._pos = pos
    """
    @property
    def centre(self) -> Vector:
        return self.pos + (self.size / 2)

