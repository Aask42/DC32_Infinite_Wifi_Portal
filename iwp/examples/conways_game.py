"""
Written by: BadAask
Written for: DC32
Date started: 20240726
Copyright: Do what you want because a pirate is free

Description: This function is exactly what it says: Conway's Game. 
    
    This file GENERATES FRAMES for the LED matrix. It does not play them back. 
    
    NOTE: This version of Conway's game always starts with a glider,
    and switches to random on reset
    Made for any matrix of X by Y, with an LED driver providing 
    set_led_list(led_list_x_y) and clear_leds as functions
"""
#
import random

# Define the glider pattern
glider_pattern = [
    [0, 1, 0],
    [0, 0, 1],
    [1, 1, 1]
]

# Function to add the glider pattern to the grid at a specific position
def add_glider(x, y, grid, rows, cols):
    for dx in range(3):
        for dy in range(3):
            grid[(x + dx) % rows][(y + dy) % cols] = glider_pattern[dx][dy]

def count_neighbors(x, y, grid, rows, cols):
    # Count the number of alive neighbors for a cell at (x, y)
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    count = 0
    for dx, dy in directions:
        nx, ny = (x + dx) % rows, (y + dy) % cols
        count += grid[nx][ny]
    return count

def update_grid(grid, rows, cols):
    new_grid = [[0] * cols for _ in range(rows)]
    for x in range(rows):
        for y in range(cols):
            neighbors = count_neighbors(x, y, grid, rows, cols)
            if grid[x][y] == 1:
                if neighbors < 2 or neighbors > 3:
                    new_grid[x][y] = 0
                else:
                    new_grid[x][y] = 1
            else:
                if neighbors == 3:
                    new_grid[x][y] = 1
    return new_grid

def generate_frame(grid, rows, cols):
    frame = [[0] * cols for _ in range(rows)]
    delay = 1.0  # Hardcoded delay of 1 second per frame
    for x in range(rows):
        for y in range(cols):
            frame[x][y] = 1 if grid[x][y] == 1 else 0
    return (frame, delay)

def reset_grid_random(rows, cols):
    return [[random.randint(0, 1) for _ in range(cols)] for _ in range(rows)]

def reset_grid_glider(rows, cols):
    grid = [[0] * cols for _ in range(rows)]
    add_glider(0, 0, grid, rows, cols)
    return grid

def conway_game_init(rows, cols, random_grid=False):
    if random_grid:
        grid = reset_grid_random(rows, cols)
    else:
        grid = reset_grid_glider(rows, cols)
    return grid

def conway_game_next_frame(grid, rows, cols):
    delay = 1.0  # Hardcoded delay of 1 second per frame
    grid = update_grid(grid, rows, cols)
    frame = generate_frame(grid, rows, cols)
    return frame, grid

def generate_conway_frames(rows, cols, random_grid=False, max_frames=10):
    grid = conway_game_init(rows, cols, random_grid)
    frames = []

    for _ in range(max_frames):
        frame, grid = conway_game_next_frame(grid, rows, cols)
        frames.append(frame)

    return frames
