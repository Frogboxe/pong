
from __future__ import annotations

from functools import cached_property, total_ordering
from math import atan2, cos, hypot, pi, sin, sqrt, tau
from random import randint, random
from typing import Union

__all__ = ["Vector", "V", "Angle", "A"]

from dataclasses import dataclass


def operand_error(op: str, a) -> str:
    return f"unsupported operand type for `{op}`: `Vector` and `{a.__class__.__qualname__}`({a})"

class Angle:
    """
    An angle in radians. Exposes .degrees, .unit
    """
    _angle: float

    def __init__(self, *, degrees: Number = None, radians: Number = None, vector: Vector = None):
        given = sum(kwarg is not None for kwarg in (degrees, radians, vector))
        if given == 0:
            raise TypeError(f"{self.__init__.__qualname__}() recieved no arguments. One keyword argument is required.")
        elif given > 1:
            raise TypeError(f"{self.__init__.__qualname__}() recieved multiple keyword arguments. Max one allowed.")
        if degrees is not None:
            if isinstance(degrees, Number):
                radians = tau * (degrees / 360)
            else:
                raise TypeError(f"Angle(degrees={degrees}) has degrees supplied but is invalid type {degrees.__class__.__qualname__}")
        if vector is not None:
            if isinstance(vector, VectorType):
                radians = -atan2(vector.y, vector.x) + (pi / 2)
            else:
                raise TypeError(f"Angle(vector={vector}) has vector supplied but is invalid type {vector.__class__.__qualname__}")
        if not isinstance(radians, Number):
            raise TypeError(f"Angle(radians={radians}) has radians supplied but is invalid type {radians.__class__.__qualname__}")
        self._angle = radians

    def __hash__(self) -> int:
        return hash(self._angle)

    def __repr__(self) -> str:
        return f"R[{self.degrees, self.radians}]"

    def __eq__(self, ia: Angle) -> bool:
        if not isinstance(ia, AngleType):
            raise TypeError(operand_error("==", ia))
        return (ia._angle == self._angle)

    def __lt__(self, ia: Angle) -> bool:
        if not isinstance(ia, AngleType):
            raise TypeError(operand_error("<", ia))
        return (self._angle < ia._angle)

    def __gt__(self, ia: Angle) -> bool:
        if not isinstance(ia, AngleType):
            raise TypeError(operand_error(">", ia))
        return (self._angle > ia._angle)

    def __le__(self, ia: Angle) -> bool:
        if not isinstance(ia, AngleType):
            raise TypeError(operand_error("<=", ia)) 
        return (self._angle < ia._angle)

    def __add__(self, ia: Angle) -> Angle:
        if not isinstance(ia, Angle):
            raise TypeError(operand_error("+", ia))
        return A(radians=(self.radians + ia.radians))

    def __sub__(self, ia: Angle) -> Angle:
        if not isinstance(ia, Angle):
            raise TypeError(operand_error("-", ia))
        return A(radians=(self.radians - ia.radians))

    def __round__(self, places: int) -> Angle:
        return A(round(self._angle, places))

    @property
    def degrees(self) -> float:
        "this angle as float, measured in degrees and contained in one period"
        return ((self.radians / tau) * 360)

    @property
    def radians(self) -> float:
        "this angle as float, measured in radians and contained in one period"
        return self._angle % tau

    @cached_property
    def unit(self) -> Vector:
        "this angle as Vector, with distance 1 (unit vector)"
        return V.from_angle(self, 1)

class Vector:
    """
    Vector represents a 2D coordernate on a pixel grid with
    backend values being floats.

    .x: int
    .y: int
    ._x: float
    ._y: float
    """

    _x: float
    _y: float

    def __init__(self, x, y, *, vector: VectorType = None, angle: AngleType = None, magnitude: float = 1):
        given = sum(kwarg is not None for kwarg in (vector, angle))
        if given > 1:
            raise TypeError(f"{self.__init__.__qualname__}() recieved multiple keyword arguments. Max one allowed.")
        if vector is not None:
            if isinstance(vector, VectorType):
                x, y = vector._x, vector._y
            else:
                raise TypeError(f"Vector(vector={vector}) has vector supplied but is invalid type {vector.__class__.__qualname__}")
        if angle is not None:
            if isinstance(angle, AngleType):
                x, y = (sin(angle._angle) * magnitude, cos(angle._angle) * magnitude)
            else:
                raise TypeError(f"Vector(angle={angle}) has vector supplied but is invalid type {angle.__class__.__qualname__}")
        if not isinstance(x, Number):
            raise TypeError(f"Supplied value {x.__class__.__qualname__}({x}) is not a Number")
        if not isinstance(y, Number):
            raise TypeError(f"Supplied value {y.__class__.__qualname__}({y}) is not a Number")
        self._x = x
        self._y = y

    def __hash__(self) -> int:
        return hash(self._x) + hash(self._y)

    def __iter__(self):
        """Yield ._x then ._y for unpacking"""
        yield self._x
        yield self._y

    def __len__(self):
        "length of Vector2 is 2"
        return 2

    def __repr__(self) -> str:
        return f"V({self.x}, {self.y})"

    def __str__(self) -> str:
        "__repr__"
        return repr(self)

    def __getitem__(self, i: int) -> int:
        "x == self[0]; y == self[1]"
        "x, y are rounded ints"
        # treats Vector like a tuple and yields x if i == 0 or y if i == 1
        if i not in range(2):
            raise IndexError(f"Vector index `{i}` is not valid")
        return (self.x * ((i + 1) % 2) + self.y * i)

    def __round__(self, places: int) -> Vector:
        "round components of self to `places` decimal places"
        return V(round(self._x, places), round(self._y, places))

    def __abs__(self) -> Vector:
        "this Vector as Vector, reflected so _x and _y are positive"
        return Vector(abs(self._x), abs(self._y))

    def __add__(self, ia: VectorType) -> Vector:
        "add to this Vector the Vector `ia.x, ia.y`"
        if not isinstance(ia, VectorType):
            raise TypeError(operand_error("+", ia))
        x, y = ia
        return Vector(self._x + x, self._y + y)

    def __neg__(self) -> Vector:
        "return Vector equal to V(0, 0) - self"
        return V(-self._x, -self._y)

    def __sub__(self, ia: VectorType) -> Vector:
        "subtract from this Vector the Vector `ia.x, ia.y`"
        if not isinstance(ia, VectorType):
            raise TypeError(operand_error("-", ia))
        x, y = ia
        return Vector(self._x - x, self._y - y)

    def __mul__(self, ia: Union[VectorType, Number]) -> Vector:
        "multiply this Vector by scalar `ia` or Vector `ia.x, ia.y`"
        if isinstance(ia, Number):
            return V(self._x * ia, self._y * ia)
        elif isinstance(ia, VectorType):
            return V(self._x * ia._x, self._y * ia._y)
        else:
            raise TypeError(operand_error("*", ia))

    def __pow__(self, ia: Number) -> Vector:
        "raise Vector's components to power `ia`"
        if not isinstance(ia, Number):
            raise TypeError(operand_error("**", ia))
        return Vector(self._x ** ia, self._y ** ia)

    def __truediv__(self, ia: Union[VectorType, Number]) -> Vector:
        "divide this Vector by scalar `ia` or Vector `ia.x, ia.y`"
        if isinstance(ia, Number):
            return V(self._x / ia, self._y / ia)
        elif isinstance(ia, VectorType):
            return V(self._x / ia._x, self._y / ia._y)
        raise TypeError(operand_error("/", ia))

    def __eq__(self, ia: VectorType) -> bool:
        "unrounded equality with another Vector"
        if isinstance(ia, VectorType):
            return self._x == ia._x and self._y == ia._y
        raise TypeError(operand_error("==", ia))

    def __mod__(self, ia: Union[VectorType, Number]) -> Vector:
        "apply modulo to Vector's components with Vector `ia.x, ia.y`"
        "or with number `ia`"
        if isinstance(ia, Number):
            return Vector(self.x % ia, self.y % ia)
        elif isinstance(ia, VectorType):
            return Vector(self.x % ia.x, self.y % ia.y)
        raise TypeError(operand_error("%", ia))

    def lobind(self, v: VectorType) -> Vector:
        "(min(v._x, self._x)), (min(v._y, self._y))"
        if not isinstance(v, VectorType):
            raise TypeError(operand_error("lobind 'lo'", v))
        return Vector((min(v._x, self._x)), (min(v._y, self._y)))

    def hibind(self, v: VectorType) -> Vector:
        "(max(v._x, self._x)), (max(v._y, self._y))"
        if not isinstance(v, VectorType):
            raise TypeError(operand_error("hibind 'hi'", v))
        return Vector((max(v._x, self._x)), (max(v._y, self._y)))

    def bind(self, lo: VectorType, hi: VectorType) -> Vector:
        "lobind and hibind to force `self` into bounds `lo`, `hi`"
        "inclusive of bounds"
        return self.hibind(lo).lobind(hi)

    def inside(self, lo: Vector, hi: Vector) -> bool:
        "return self "
        return self.bind(lo, hi) == self

    def shift_context(self) -> Vector:
        return V(self._x, -self._y)

    def approach(self, target: Vector, factor: float) -> Vector:
        return self + (target - self) * factor

    def signs(self) -> Vector:
        return V(1 if self.x >= 0 else -1, 1 if self.y >= 0 else -1)

    def force_round(self) -> Vector:
        return V(self.x, self.y)

    def rotate(self, angle: Angle) -> Vector:
        b = angle.radians
        sinb = sin(b)
        cosb = cos(b)
        return V(
            (cosb * self._x) - (sinb * self._y),
            (sinb * self._x) + (cosb * self._y)
        )

    @staticmethod
    def from_angle(angle: Angle, magnitude: float = 1) -> Vector:
        return V(sin(angle._angle) * magnitude, cos(angle._angle) * magnitude)

    @staticmethod
    def from_random_sign() -> Vector:
        return Vector((randint(0, 1) * 2) - 1, (randint(0, 1) * 2) - 1)

    @staticmethod
    def from_random_square(lo: Vector, hi: Vector) -> Vector:
        dv = hi - lo
        return lo + (dv.vx * random() + dv.vy * random())
     
    @property
    def x(self) -> int:
        """Return ._x as rounded int"""
        return round(self._x)

    @property
    def y(self) -> int:
        """Return ._y as rounded int"""
        return round(self._y)

    @property
    def vx(self) -> Vector:
        return V(self._x, 0)

    @property
    def vy(self) -> Vector:
        return V(0, self._y)

    @cached_property
    def length(self) -> float:
        return hypot(self._x, self._y)
        #return sqrt((self._x ** 2) + (self._y ** 2))
        
    @cached_property
    def normal(self) -> Vector:
        return V(self._x / self.length, self._y / self.length)


# shorthand definition of Vector

V = Vector
A = Angle

Number = (float, int)
VectorType = (Vector)
AngleType = (Angle)

