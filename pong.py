
from __future__ import annotations

import os
import sys
import time
from contextlib import suppress
from functools import cached_property
from math import atan, pi, tau

from logdumps import *
from vector import V, Vector, Angle, A

# work out where the program is running to find texture files.
ROUTE = "\\".join(sys.argv[0].split("\\")[:-1:]) + "\\"
ROUTE_ALT = "/".join(sys.argv[0].split("/")[:-1:]) + "/"
# sometimes the route given by sys.argv[0] uses `/` as a split and sometimes `\`
# so this hack fixes that
if len(ROUTE) < len(ROUTE_ALT):
    ROUTE = ROUTE_ALT
LOG_ROUTES = ROUTE + "logs/"

# hacky assemble logs folder
with suppress(OSError):
    os.mkdir(LOG_ROUTES)

# logs setup
LM = initialise_log_manager()
pong = create_log_target("pong", f"{LOG_ROUTES}pong.log")
LM.add_files([pong])

log = LM.create_log({"pong", "stdout"}, defaultKwargs={"flush": True})

PADDLE_ID = "PADDLE_ID"
INPUT = "INPUT"

BALL_POSITIONS = "BALLS"
PADDLE_POSITIONS = "PADDLES"
BALL_VELOCITIES = "BALLSV"
PADDLE_INPUTS = "PADDLESV"

class Pong:

    score: Vector = V(0, 0)
    scoreZoneOffset: Vector = V(10, 0)
    
    paddles: list[Vector]
    balls: list[Vector]

    ballVelocities: list[Vector]

    paddleInput: list[Vector] = []

    pageSize: Vector = V(1500, 1000)

    paddleSize: Vector = V(16, 70)
    paddleOffset: Vector = V(80, 0)
    paddleMaxSpeed: Vector = V(400, 700)
    paddleFriction: Vector = V(1, 1)
    paddlePlayableSize: Vector = pageSize.vy + (pageSize.vx / 3)
    
    ballSize: Vector = V(6, 6)
    ballIdealSpeed: Vector = V(200, 150)
    ballReturnToIdealFactor: float = 0.0006
    ballStartSpeed: Vector = V(150, 80)
    ballSpeedLow: Vector = V(1, 1)
    ballSpeedHigh: Vector = V(2, 2)
    ballSpeedRNGScale: float = 0.5
    ballStartLocation: Vector = (pageSize + ballSize) / 2
    ballBaseSpeed: Vector = V(140, 80)
    ballBumpMultiplier: Vector = V(1.5, 1)

    def random_ball_start_speed(self) -> Vector:
        return self.ballStartSpeed * Vector.from_random_sign() * Vector.from_random_square(self.ballSpeedLow, self.ballSpeedHigh) * self.ballSpeedRNGScale

    def move_paddles(self, dt: float):
        for i, paddle in enumerate(self.paddles):
            paddleInput = self.paddleInput[i].bind(V(-1, -1), V(1, 1))
            if paddle.inside(self.scoreZoneOffset, self.pageSize.vx / 3 + self.pageSize.vy - self.paddleSize):
                self.paddles[i] = (paddle + (self.paddleMaxSpeed * paddleInput * dt)).bind(self.scoreZoneOffset, self.pageSize.vx / 3 + self.pageSize.vy - self.paddleSize)
            else:
                self.paddles[i] = (paddle + (self.paddleMaxSpeed * paddleInput * dt)).bind((self.pageSize.vx / 3) * 2, self.pageSize - self.scoreZoneOffset - self.paddleSize)

    def score_updates(self, i: int, ball: Vector) -> Vector:
        if (ball.x < self.scoreZoneOffset.x) or (ball.x > self.pageSize.x - self.scoreZoneOffset.x - self.ballSize.x):
            if ball.x < self.scoreZoneOffset.x:
                self.score = self.score + V(1, 0)
            elif ball.x > (self.pageSize.x - self.scoreZoneOffset.x - self.ballSize.x):
                self.score = self.score + V(0, 1)
            self.balls[i] = self.ballStartLocation
            self.ballVelocities[i] = self.random_ball_start_speed()
            return self.balls[i]
        return ball

    def passive_speed_modification(self):
        for i, currentVelocity in enumerate(self.ballVelocities):
            signs = currentVelocity.signs()
            self.ballVelocities[i] = signs * abs(currentVelocity).approach(self.ballIdealSpeed, self.ballReturnToIdealFactor)

    def paddle_collision(self, candidate: Vector, i: int, j: int, paddle: Vector):
        paddleCentre = paddle + (self.paddleSize / 2)
        candidateCentre = candidate + (self.ballSize / 2)
        angle = A(vector=(paddleCentre - candidateCentre)).radians
        full = A(degrees=360).radians
        half = A(degrees=180).radians
        theta = self.theta.radians
        #              <initial velocity>                          <paddle velocity>                           <scale up from collision>
        velocity = ((self.ballVelocities[i] + (self.paddleInput[j] * self.paddleMaxSpeed * self.paddleFriction)) * self.ballBumpMultiplier)
        if angle <= theta and angle >= (full - theta):
            # top of paddle
            self.ballVelocities[i] = velocity.vx + -abs(velocity.vy)
        elif angle >= theta and angle <= (half - theta):
            # left side
            self.ballVelocities[i] = -abs(velocity.vx) + velocity.vy
        elif angle >= (half - theta) and angle <= (half + theta):
            # bottom
            self.ballVelocities[i] = velocity.vx + abs(velocity.vy)
        else:
            # right side
            self.ballVelocities[i] = abs(velocity.vx) + velocity.vy

    def wall_collision(self, i: int, candidate: Vector):
        velocity = self.ballVelocities[i]
        # top collision
        if candidate.y < 0:
            self.ballVelocities[i] = velocity.vx + abs(velocity.vy)
        elif candidate.y > (self.pageSize.y - self.ballSize.y):
            self.ballVelocities[i] = velocity.vx + -abs(velocity.vy)
        # side collision
        if candidate.x < 0:
            self.ballVelocities[i] = abs(velocity.vx) + velocity.vy
        elif candidate.x > (self.pageSize.x - self.ballSize.x):
            self.ballVelocities[i] = -abs(velocity.vx) + velocity.vy

    def tick(self, dt: float):
        # move paddles
        self.move_paddles(dt)
        self.passive_speed_modification()
        # ball movement
        for i, ball in enumerate(self.balls):
            # handle score
            ball = self.score_updates(i, ball)
            candidate = ball + self.ballVelocities[i] * dt
            # collision with paddle
            for j, paddle in enumerate(self.paddles):
                if any((
                    candidate.inside(paddle, paddle + self.paddleSize),
                    (candidate + self.ballSize.vx).inside(paddle, paddle + self.paddleSize),
                    (candidate + self.ballSize.vy).inside(paddle, paddle + self.paddleSize),
                    (candidate + self.ballSize).inside(paddle, paddle + self.paddleSize)
                )):
                    # ball hits paddle
                    self.paddle_collision(candidate, i, j, paddle)
                    # note: paddle_collision does not move ball; paddle_collision changes velocity of ball
            # collision with walls
            self.wall_collision(i, candidate)
            # set new position based on collision and existing velocity
            self.balls[i] = candidate

    # ascii rasterisation
    def display(self, ascii: Vector = V(24, 24)):
        "draw the state of the board in text with resolution given as a Vector `ascii`"
        scale = self.pageSize / ascii
        world = [[" " for _ in range(ascii.x)] for _ in range(ascii.y)]
        for ix in range(ascii.x):
            for iy in range(ascii.y):
                scan = V(ix, iy) * scale
                for paddle in self.paddles:
                    if scan.inside(paddle, paddle + self.paddleSize):
                        world[iy][ix] = "P"
                for ball in self.balls:
                    if scan.inside(ball, ball + self.ballSize):
                        world[iy][ix] = "B"
        for line in world:
            print("".join(line))

    @cached_property
    def theta(self) -> float:
        # for a rectangle where the top two points are p1, p2 and the origin is o
        # theta is precisely half the angle described p1 <- o -> p2 (p1 o p2) 
        # this is used to distinguish between which side of the paddle was hit
        # by a ball
        return A(radians=(atan(self.paddleSize.x / self.paddleSize.y)))

    def add_two_paddles(self) -> Pong:
        self.paddles = [(self.pageSize.vy / 2) + self.paddleOffset, self.pageSize.vx + (self.pageSize.vy / 2) - self.paddleOffset]
        self.paddleInput = [V(0, 0), V(0, 0)]
        return pong

    def add_balls(self, ballCount: int):
        self.balls = [self.ballStartLocation] * ballCount
        self.ballVelocities = [self.random_ball_start_speed() for _ in range(ballCount)]
   
    def create_game_normal(self):
        self.add_two_paddles()
        self.add_balls(1)

    def create_game_balls(self, ballCount: int):
        self.add_two_paddles()
        self.add_balls(ballCount)

LM.flush_all()

