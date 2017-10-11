import pygame as pg
from pygame.math import Vector2 as V2
from math import pi, sin, cos, tan, atan2


class Player:
    def __init__(self, pos):
        self.pos = V2(pos)  # Pixels
        self.vel = V2(0, 0)  # Pixels / Frame
        self.turn_vel = 0.0  # Radians / Frame
        self.angle = 0.0  # Radians

        self.radius = 20
        self.speed = 1  # Pixels / Frame
        self.turn_speed = 0.1  # Radians / Frame
        self.fov = 2 * pi * 0.3  # Radians

    # Returns a unit direction vector
    def get_direction_vector(self):
        return V2(cos(self.angle), sin(self.angle))

    def draw_on(self, surface):
        pg.draw.circle(surface, (0, 255, 0), (int(self.pos.x), int(self.pos.y)), self.radius, 0)
        pg.draw.line(surface, (255, 0, 0), self.pos, self.pos + self.get_direction_vector() * self.radius, 3)


def draw_map(surface, board, block_size):
    for y in range(len(board)):
        for x in range(len(board)):
            if board[y][x]:
                pg.draw.rect(surface, (0, 0, 0), pg.Rect(x * block_size, y * block_size, block_size, block_size), 0)


def ccw(A, B, C):
    return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)


# Return true if line segments AB and CD intersect
def line_intersect(A, B, C, D):
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


# Finds ray intersections using vector math
def draw_view_proper(surface, board, player):
    walls = [V2(x, y) for x in range(len(board[0])) for y in range(len(board)) if board[y][x]]
    # print(walls)
    dist_from_screen = (surface.get_width() / 2) / tan(player.fov / 2)
    for x in range(0, surface.get_width()):
        x_angle = atan2(x - surface.get_width() // 2, dist_from_screen)
        sight_ray = (player.pos, (
            player.pos.x + 1000 * cos(x_angle + player.angle), player.pos.y + 1000 * sin(x_angle + player.angle)))
        # print("sight ray:", sight_ray)
        for wall in walls:
            sides = [
                (wall * block_size, (wall + V2(1, 0)) * block_size),
                (wall * block_size, (wall + V2(0, 1)) * block_size),
                ((wall + V2(1, 0)) * block_size, (wall + V2(1, 1)) * block_size),
                ((wall + V2(0, 1)) * block_size, (wall + V2(1, 1)) * block_size)
            ]
            hits = []
            for side in sides:
                intersection = line_intersection(side, sight_ray)

                if intersection is not None:
                    if V2(intersection).distance_to(player.pos) > 0.00001:
                        hits.append((side, V2(intersection).distance_to(player.pos)))

            closest_side, distance = min(hits, key=lambda x: x[1])
            print(closest_side, distance, "\n")
            # n = min(1.0, 100.0 / distance)
            # color = (int(255 * n), int(255 * n), int(255 * n))
            # draw_height = min(screen.get_height(), 10000.0 / distance)
            # pg.draw.line(surface, color, (x, (surface.get_height() - draw_height) / 2), (x, (surface.get_height() + draw_height) / 2), 1)


# Finds ray intersections using a primitive stepped scan
def draw_view_slow(surface, board, block_size, player):
    scan_steps = 200
    max_scan_distance = screen.get_width()

    for x in range(0, surface.get_width()):
        angle = ((x / surface.get_width()) - 0.5) * player.fov + player.angle  # absolute map angle
        horizon_point = max_scan_distance * V2(cos(angle), sin(angle))
        step = (horizon_point - player.pos) / scan_steps

        # scan along ray, checking for intersections
        scan_pos = V2(player.pos.x, player.pos.y)  # copy player position
        for i in range(scan_steps):
            scan_pos += step
            grid_x, grid_y = int(scan_pos.x / block_size), int(scan_pos.y / block_size)
            if grid_x < 0 or grid_y < 0:
                break
            if grid_x >= len(board[0]) or grid_y >= len(board):
                break
            if board[grid_y][grid_x]:
                distance = player.pos.distance_to(scan_pos)
                n = distance / max_scan_distance
                color = (n * 255, n * 255, n * 255)
                height = 20000 / distance
                pg.draw.line(surface, color, (x, surface.get_height() // 2 - height // 2),
                             (x, surface.get_height() // 2 + height // 2), 1)
                break


# Finds ray intersections using a multistage stepped scan
# emulates accuracy of scan_steps * secondary_scan_steps while only performing scan_steps + secondary_scan_steps checks
def draw_view_fast(surface, board, block_size, player):
    # Draw Scenery
    pg.draw.rect(surface, (135, 206, 250), pg.Rect(0, 0, surface.get_width(), surface.get_height() // 2), 0)  # Sky
    pg.draw.rect(surface, (87, 59, 12), pg.Rect(0, surface.get_height() // 2, surface.get_width(), surface.get_height() // 2), 0)  # Ground

    # Draw Walls
    focal_length = (surface.get_width() / 2) / tan(player.fov / 2)
    scan_steps = 300
    secondary_scan_steps = 30
    max_scan_distance = screen.get_width()

    for x in range(0, surface.get_width()):
        angle = ((x / surface.get_width()) - 0.5) * player.fov + player.angle  # absolute map angle
        horizon_point = max_scan_distance * V2(cos(angle), sin(angle))
        step = (horizon_point - player.pos) / scan_steps
        secondary_step = -step / secondary_scan_steps

        # scan along ray, checking for intersections
        scan_pos = V2(player.pos.x, player.pos.y)  # copy player position
        for _ in range(scan_steps):
            scan_pos += step
            grid_x, grid_y = int(scan_pos.x / block_size), int(scan_pos.y / block_size)
            if grid_x < 0 or grid_y < 0:
                break
            if grid_x >= len(board[0]) or grid_y >= len(board):
                break
            if board[grid_y][grid_x]:
                # After finding a rough intersection point, scan backwards along the ray with a smaller step until open square is found
                for _ in range(secondary_scan_steps):
                    scan_pos += secondary_step
                    grid_x, grid_y = int(scan_pos.x / block_size), int(scan_pos.y / block_size)
                    if not board[grid_y][grid_x]:
                        distance = player.pos.distance_to(scan_pos)
                        n = distance / max_scan_distance
                        n = max(0.1, n)
                        color = (n * 255, n * 255, n * 255)
                        # height = 20000 / distance
                        height = block_size * focal_length / distance
                        pg.draw.line(surface, color, (x, surface.get_height() // 2 - height // 2),
                                     (x, surface.get_height() // 2 + height // 2), 1)
                        break
                break


def update_screen(screen, board, block_size, player):
    map_surface = pg.Surface((width // 2, height))
    view_surface = pg.Surface((width // 2, height))
    map_surface.fill((255, 255, 255))
    view_surface.fill((255, 255, 255))

    draw_map(map_surface, board, block_size)
    player.draw_on(map_surface)
    draw_view_fast(view_surface, board, block_size, player)

    screen.blit(map_surface, (0, 0))
    screen.blit(view_surface, (width // 2, 0))
    pg.draw.line(screen, (0, 0, 0), (screen.get_width() // 2 - 1, 0),
                 (screen.get_width() // 2 - 1, screen.get_height()), 2)
    pg.display.update()


if __name__ == "__main__":
    board = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]
    # board = [
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # ]

    width, height = 1200, 600

    player = Player((width // 4, height // 2))

    block_size = height // max(len(board), len(board[0]))

    screen = pg.display.set_mode((width, height))

    update_screen(screen, board, block_size, player)

    left, right, up, down = False, False, False, False
    clock = pg.time.Clock()
    done = False
    while not done:
        clock.tick(60)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                done = True
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_a:
                    left = True
                    player.turn_vel = -player.turn_speed
                elif event.key == pg.K_d:
                    right = True
                    player.turn_vel = player.turn_speed
                elif event.key == pg.K_w:
                    up = True
                    player.vel = player.get_direction_vector() * player.speed
                elif event.key == pg.K_s:
                    down = True
                    player.vel = -player.get_direction_vector() * player.speed
            elif event.type == pg.KEYUP:
                if event.key == pg.K_a:
                    left = False
                    player.turn_vel = 0
                elif event.key == pg.K_d:
                    right = False
                    player.turn_vel = 0
                elif event.key == pg.K_w:
                    up = False
                    player.vel = V2(0, 0)
                elif event.key == pg.K_s:
                    down = False
                    player.vel = V2(0, 0)

        if left or right:
            if up:
                player.vel = player.get_direction_vector() * player.speed
            elif down:
                player.vel = -player.get_direction_vector() * player.speed

        player.pos += player.vel
        player.angle += player.turn_vel

        if player.turn_vel != 0 or player.vel.x != 0 or player.vel.y != 0:
            update_screen(screen, board, block_size, player)

    pg.quit()
