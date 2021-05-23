
from __future__ import annotations

import os
import shutil
import sys
import time
from collections.abc import Sequence
from contextlib import suppress
from functools import cache, lru_cache

import pygame

from element import Element
from pygcontext import PygContext
from logdumps import *
from render import Render
from vector import A, Angle, V, Vector

# event codes. VSCODE doesn't recognise pygame.<event_name> properly so they're relisted here.
MMOTION, KDOWN, KUP, MBDOWN, MBUP, QUIT = 1024, 768, 769, 1025, 1026, 256
WINSHOW, ACTIVATED, FOCUS = 32774, 32768, 32785
TEXT_EDIT, VIDEO, WINEXPOSED = 770, 32770, 32776
TEXT_ENTER, UNFOCUS = 771, 32786
M_WHEEL, RESIZE = 1027, 32778
SET_RESIZABLE = 16
NOT_RESIZABLE = 0
LEFT_CLICK = 1
SRCALPHA = 65536
# this is purely a vscode workaround
# no longer needed due to PyLance update but will stay for now

# keyboard keys.
PAGE_UP, PAGE_DOWN = 1073741899, 1073741902

# work out where the program is running to find texture files.
ROUTE = "\\".join(sys.argv[0].split("\\")[:-1:]) + "\\"
ROUTE_ALT = "/".join(sys.argv[0].split("/")[:-1:]) + "/"
# sometimes the route given by sys.argv[0] uses `/` as a split and sometimes `\`
if len(ROUTE) < len(ROUTE_ALT):
    ROUTE = ROUTE_ALT
TEXTURE_ROUTES = ROUTE + "assets/"
LOG_ROUTES = ROUTE + "logs/"

try:
    os.mkdir(TEXTURE_ROUTES)
except OSError:
    pass

IMAGE_EXTENSIONS = (".jpg", ".png")
# pull files from top level and place in assets/
for route in os.listdir("."):
    if os.path.isfile(route) and route[-4::] in IMAGE_EXTENSIONS:
        try:
            shutil.copy(route, TEXTURE_ROUTES + route)
        except shutil.SameFileError:
            pass
        try:
            os.remove(route)
        except FileNotFoundError:
            pass

# logs setup (don't need to do texture hackery here because it's done in logdumps.py)
LM = initialise_log_manager()
gout = create_log_target("gout", f"{LOG_ROUTES}graphics.log")
rout = create_log_target("rout", f"{LOG_ROUTES}out.log")
LM.add_files([gout, rout])

# active logs
log = LM.create_log({"rout", "stdout"}, defaultKwargs={"flush": True})
glog = LM.create_log({"gout",}, defaultKwargs={"flush": False})

log(f"Running at {sys.argv}")

# texture loading utilities
# all textures loaded once are cached until the application closes
@cache 
def load_texture(route: str, offset: Vector = V(0, 0)) -> Render:
    try:
        return Render(pygame.image.load(TEXTURE_ROUTES + route).convert_alpha(), offset)
    except FileNotFoundError:
        log(f"File not found: {route}")
        raise

# a large amount of cache is allocated to scaling since lots of scaled draw calls
# need to be made when the screen chages that are expensive even if most of the
# objects on screen will have the exact same scale as they had previously
@lru_cache(maxsize=128)
def load_and_scale(route: str, scale: Vector, offset: Vector = V(0, 0)) -> Render:
    start = load_texture(route, offset).texture
    tSize = V(*start.get_size()) * scale
    clean = pygame.Surface(tSize, SRCALPHA)
    pygame.transform.smoothscale(start, tSize, clean)
    return Render(clean, offset)

# a very large cache is allocated to rotation because, in most cases, it is only
# expected that small textures are being rotated and only one at a time, increasing
# the chance of cache hits and reducing the cost of each cached element
@lru_cache(maxsize=512)
def load_and_scale_and_rotate(route: str, scale: Vector, rotation: Angle, offset: Vector = V(0, 0)) -> Render:
    start = load_and_scale(route, scale, offset).texture
    return Render(pygame.transform.rotate(start, -rotation.angle), offset)

# mass loading not cached to reduce redundency
def load_textures(routes: Sequence[str]) -> tuple[pygame.Surface]:
    return tuple((load_texture(route) for route in routes))

def load_and_scale_all(routes: str, scale: Vector) -> tuple[pygame.Surface]:
    return tuple((load_and_scale(route, scale) for route in routes))

class Screen:
    done: bool = False
    elements: list[Element]
    surface: pygame.Surface
    colour: pygame.Color
    flags: int = NOT_RESIZABLE
    _caption: str = "Pyg Renderer"
    _size: Vector = V(800, 600)
    keys: set[int]
    mkeys: set[int]
    selectedID: int
    selectable: list[Element]
    context: PygContext
    def __init__(self):
        self.context = None
        self.elements = []
        pygame.font.init()
        pygame.display.set_mode(self._size, self.flags)
        pygame.display.set_caption(self.caption)
        self.surface = pygame.display.get_surface()
        self.keys, self.mkeys = set(), set()
        self.caption = Screen._caption

    def new_context(self, context: PygContext):
        self.context = context
        self.handlers = {
            MMOTION: self._mouse_move,
            KDOWN: self._key_down,
            KUP: self._key_up,
            MBDOWN: self._mouse_down,
            MBUP: self._mouse_up,
            QUIT: self._quit,
            WINSHOW: self._window_shown,
            ACTIVATED: self._activated,
            FOCUS: self._focussed,
            TEXT_EDIT: lambda e: None,
            VIDEO: self._video,
            WINEXPOSED: self._exposed,
            TEXT_ENTER: self._typing,
            UNFOCUS: self._unfocussed,
            M_WHEEL: self._mouse_wheel,
            RESIZE: self._resize,
            32783: lambda e: None, # window enter
            32784: lambda e: None, # window leave
            32777: lambda e: None, # window moved
            32779: lambda e: None, # window size changed
            32769: lambda e: None, # video resize
            32787: lambda e: None, # window closed
            32780: lambda e: None, # window minimised
            32782: lambda e: None, # window restored
            32781: lambda e: None, # window maximised
            2304: lambda e: None, # capture frame
        }

    def add_element(self, element: Element):
        self.elements.append(element)

    def _mouse_move(self, event: pygame.event): 
        self.context.mouse_move(event)

    def _window_shown(self, event: pygame.event): 
        self.context.window_shown(event)

    def _activated(self, event: pygame.event): 
        self.context.activated(event)

    def _focussed(self, event: pygame.event): 
        self.context.focussed(event)

    def _video(self, event: pygame.event): 
        self.context.video(event)

    def _exposed(self, event: pygame.event): 
        self.context.exposed(event)

    def _typing(self, event: pygame.event): 
        self.context.typing(event)

    def _unfocussed(self, event: pygame.event): 
        self.context.unfocussed(event)

    def _mouse_wheel(self, event: pygame.event): 
        self.context.mouse_wheel(event)

    def _resize(self, size: Vector): 
        self.context.resize()

    def _post_init(self): 
        self.context.post_init()

    def _quit(self): 
        self.context.quit()

    def _update(self): 
        self.context.update()

    def _key_down(self, event: pygame.event): 
        self.keys.add(event.key)
        self.context.key_down(event.key)
    
    def _key_up(self, event: pygame.event): 
        self.keys.remove(event.key)
        self.context.key_up(event.key)

    def _mouse_down(self, event: pygame.event): 
        self.mkeys.add(event.button)
        self.context.mouse_down(event.button, V(*event.pos))

    def _mouse_up(self, event: pygame.event): 
        self.mkeys.remove(event.button)
        self.context.mouse_up(event.button, V(*event.pos))

    def _resize(self, event: pygame.event):
        self.size = V(*self.surface.get_size())
        self.context.resize(V(self.size.x, self.size.y))
        self.changed = True

    def _quit(self, event: pygame.event):
        self.changed = True
        self.done = True
        self.context.quit()

    def draw(self, texture: pygame.Surface, pos: tuple[int]):
        try:
            self.surface.blit(texture.texture, pos + texture.offset) if texture is not None else 0
        except TypeError:
            # default error message not terribly clear
            log(f"Invalid Type. Pos is likely None pos: `{pos}` for object `{texture, texture.__class__.__qualname__}`")
            raise

    def render(self, fr: int):
        self.context.update()
        if self.changed:
            for element in self.elements:
                if element.render:
                    for texture in element.textures:
                        self.draw(texture, element.pos)
            pygame.display.flip()
        self.clock.tick(fr)
        self.changed = False

    def prepare_context(self):
        if not isinstance(self.context, PygContext):
            raise AttributeError(f"Pyg <{self.__class__.__qualname__}> {self} has context {self.context} {self.context.__class__.__qualname__}")
        log(f"Running new display with context {self.context.__class__.__qualname__}")
        self.last = time.time()
        self.changed = True
        self.clock = pygame.time.Clock()
        self.done = False
        log(f"Setting up context {self.context.__class__.__qualname__}")
        self._post_init()
        self.context.resize(V(*self.surface.get_size()))
        self.context.starting()

    def run(self, highFR: float, lowFR: float):
        self.highFR, self.lowFR = highFR, lowFR
        self.prepare_context()
        modHigh = highFR - lowFR
        while not self.done:
            for event in pygame.event.get():
                with suppress(KeyError):
                    self.handlers[event.type](event)
            self.render(lowFR + modHigh * self.changed)
        self.context.quit()
    
    @property
    def caption(self) -> str:
        return self._caption

    @caption.setter
    def caption(self, caption: str):
        log("caption set")
        self._caption = caption
        pygame.display.set_caption(caption)

    @property
    def selected(self) -> Element:
        return self.selectable[self.selectedID % len(self.selectable)]

    @selected.setter
    def selected(self, selected: Element):
        if isinstance(selected, Element):
            index = self.selectable.index(selected)
            if index != -1:
                self.selectedID = self.selectable.index(selected)

    @property
    def size(self) -> Vector:
        return V(*self.surface.get_size())

def main():
    Screen.size = V(1600, 1200)
    s = Screen()
    with PygContext(s):
        s.run(144, 30)

if __name__ == "__main__":
    main()
    LM.flush_all()




