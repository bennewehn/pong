import numpy as np
from typing import Callable, Any, Tuple


class Game:
    def __init__(self,
                 width: int = 1000,
                 height: int = 650,
                 ball_size: int = 30,
                 ball_velocity: int = 4,
                 bar_height: int = 100,
                 bar_width: int = 20,
                 bar_margin: int = 30,
                 bar_velocity: int = 8,
                 on_score_changed: Callable[[
                     int, int, Any], None] | None = None,
                 on_ball_pos_changed: Callable[[
                     Tuple[float, float], Any], None] | None = None,
                 on_left_block_pos_changed: Callable[[
                     int, Any], None] | None = None,
                 on_right_block_pos_changed: Callable[[
                     int, Any], None] | None = None,
                on_left_block_collided: Callable[[], None] | None = None,
                 args: Any = None):

        self.width = width
        self.height = height
        self.__score_p1 = 0
        self.__score_p2 = 0

        # callbacks
        self.on_ball_pos_changed = on_ball_pos_changed
        self.on_left_block_pos_changed = on_left_block_pos_changed
        self.on_right_block_pos_changed = on_right_block_pos_changed
        self.on_score_changed = on_score_changed
        self.on_left_block_collided = on_left_block_collided
        self.args = args

        self.ball = Ball(self, ball_size, ball_velocity)
        self.left_block = Block(
            self,
            bar_height,
            bar_width,
            bar_velocity,
            bar_margin,
            on_pos_changed=on_left_block_pos_changed)
        self.right_block = Block(
            self,
            bar_height,
            bar_width,
            bar_velocity,
            bar_margin,
            on_pos_changed=on_right_block_pos_changed)

        self.right_blockX = self.width - self.right_block.margin - self.right_block.width

    def increase_score_p1(self) -> None:
        self.__score_p1 += 1
        self.__invoke_on_score_changed()

    def increase_score_p2(self) -> None:
        self.__score_p2 += 1
        self.__invoke_on_score_changed()

    def __invoke_on_score_changed(self) -> None:
        if self.on_score_changed is not None:
            self.on_score_changed(self.__score_p1, self.__score_p2, self.args)


class Ball:
    def __init__(self, game: Game, size: int, velocity: int):
        self.game = game
        self.size = size
        self.velocity = velocity
        self.pos = np.array([0, 0], dtype=np.float32)
        self.direction = np.array([0, 0], dtype=np.float32)
        self.on_pos_changed = self.game.on_ball_pos_changed
        self.set_init_state()

    def set_init_state(self) -> None:
        self.pos = 0.5 * np.array(
            [self.game.width - self.size,
             self.game.height - self.size]
        )
        self.direction[0] = np.random.uniform(
            0.8, 1) * -1 if np.random.random() < 0.5 else 1
        self.direction[1] = np.random.uniform(-1, 1)
        self.direction /= np.linalg.norm(self.direction)

    def move(self) -> None:
        '''
        Moves ball in self.direction with self.velocity
        and handles all collisions.
        '''
        self.pos += self.velocity * self.direction
        self.__invoke_on_pos_changed()
        self.handle_collision()

    def handle_collision(self) -> None:
        # wall collision
        if self.pos[1] <= 0 or self.pos[1] + self.size >= self.game.height:
            self.direction[1] *= -1
            return
        # scores
        elif self.pos[0] + self.size >= self.game.width:
            # left scored
            self.game.increase_score_p1()
        elif self.pos[0] <= 0:
            # right scored
            self.game.increase_score_p2()
        # left bar collision
        elif (self.pos[0] <= self.game.left_block.margin + self.game.left_block.width
              and self.pos[0] >= self.game.left_block.margin
              and self.pos[1] + self.game.ball.size >= self.game.left_block.posY
              and self.pos[1] <= self.game.left_block.posY + self.game.left_block.height):
            mid = self.game.left_block.posY + self.game.left_block.height / 2
            newDir = np.array(
                [self.game.left_block.height * 0.8,
                 (self.pos[1] + self.game.ball.size/2)-mid], dtype=np.float32)
            newDir /= np.linalg.norm(newDir)
            self.direction = newDir
            if self.game.on_left_block_collided is not None:
                self.game.on_left_block_collided()
            return
        elif (self.pos[0] + self.size >= self.game.right_blockX
                and self.pos[0] <= self.game.right_blockX + self.game.right_block.width
                and self.pos[1] + self.size >= self.game.right_block.posY
                and self.pos[1] <= self.game.right_block.posY + self.game.right_block.height):
            mid = self.game.right_block.posY + self.game.right_block.height / 2
            newDir = np.array(
                [self.game.right_block.height * -0.8,
                 (self.pos[1] + self.size / 2) - mid], dtype=np.float32
            )
            newDir /= np.linalg.norm(newDir)
            self.direction = newDir
            return
        else:
            return
        # set init states
        self.set_init_state()

    def __invoke_on_pos_changed(self):
        if self.on_pos_changed is not None:
            self.on_pos_changed(tuple(self.pos), self.game.args)


class Block:
    def __init__(self,
                 game: Game,
                 height: int,
                 width: int,
                 velocity: int,
                 margin: int,
                 on_pos_changed: Callable[[int, Any], None] | None = None):
        self.game = game
        self.height = height
        self.width = width
        self.velocity = velocity
        self.margin = margin
        self.posY = 0
        self.on_pos_changed = on_pos_changed
        self.set_init_state()

    def set_init_state(self) -> None:
        self.posY = (self.game.height - self.height) / 2

    def move(self, direction: int) -> None:
        '''
        Moves block in given direction.

        Direction:
            0: down
            1: up
        '''
        newPosY = self.posY
        if direction == 0:
            newPosY += self.velocity
        else:
            newPosY -= self.velocity
        if newPosY + self.height <= self.game.height and newPosY >= 0:
            self.posY = newPosY
            self.__invoke_on_pos_changed()

    def __invoke_on_pos_changed(self):
        if self.on_pos_changed is not None:
            self.on_pos_changed(int(self.posY), self.game.args)
