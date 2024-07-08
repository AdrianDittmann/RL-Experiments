#renderer.py 
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from config import *
import PIL.Image as Img
import math
from OpenGL.GL import *
from OpenGL.GLU import *
from config import FPS, FRAMES_PER_SNAKE_MOVEMENT

class Renderer:
    def __init__(self):
        pygame.init()
        display = (WIDTH, HEIGHT)
        self.window = pygame.display.set_mode(display, pygame.DOUBLEBUF | pygame.OPENGL)
        
        glViewport(0, 0, WIDTH, HEIGHT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (WIDTH / HEIGHT), 0.1, 1000.0)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        self.param_space = ParamSpace()
        print("Param space initialized")

        # Initialize audio playback if play_song is True
        if play_song:
            pygame.mixer.init()
            print(song_path)
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely

        self.frame_count = 0
        self.render_time = 0
        self.snake_movement_counter = 0

        # Initialize skybox
        self.skybox_size = get_skybox_size(self.param_space)
        self.skybox_texture = self.create_skybox_texture()

    def create_skybox_texture(self):
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        return texture

    def draw_skybox(self):
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.skybox_texture)

        base_color = get_skybox_base_color(self.param_space)
        glColor4f(base_color[0]/255.0, base_color[1]/255.0, base_color[2]/255.0, base_color[3]/255.0)

        rot1 = get_rot1_skybox(self.param_space)
        rot2 = get_rot2_skybox(self.param_space)

        glPushMatrix()
        glRotatef(rot1, 1, 0, 0)
        glRotatef(rot2, 0, 1, 0)

        glBegin(GL_QUADS)
        s = self.skybox_size / 2

        # Front face
        glVertex3f(-s, -s, -s)
        glVertex3f(s, -s, -s)
        glVertex3f(s, s, -s)
        glVertex3f(-s, s, -s)

        # Back face
        glVertex3f(-s, -s, s)
        glVertex3f(s, -s, s)
        glVertex3f(s, s, s)
        glVertex3f(-s, s, s)

        # Left face
        glVertex3f(-s, -s, -s)
        glVertex3f(-s, -s, s)
        glVertex3f(-s, s, s)
        glVertex3f(-s, s, -s)

        # Right face
        glVertex3f(s, -s, -s)
        glVertex3f(s, -s, s)
        glVertex3f(s, s, s)
        glVertex3f(s, s, -s)

        # Top face
        glVertex3f(-s, s, -s)
        glVertex3f(s, s, -s)
        glVertex3f(s, s, s)
        glVertex3f(-s, s, s)

        # Bottom face
        glVertex3f(-s, -s, -s)
        glVertex3f(s, -s, -s)
        glVertex3f(s, -s, s)
        glVertex3f(-s, -s, s)

        glEnd()
        glPopMatrix()

        glDisable(GL_TEXTURE_2D)
        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)

    def reset_param_space(self):
        self.param_space = ParamSpace()

    def render(self, snake, apples, frame_output_path=None):
        self.render_time += 1 / FPS
        self.param_space.time = self.render_time
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glLoadIdentity()
        gluLookAt(0, 0, get_zoom(self.param_space),
                  0, 0, 0,
                  0, 1, 0)

        # Draw skybox
        self.draw_skybox()

        glRotatef(get_rot1(self.param_space) * 360, 1, 0, 0)
        glRotatef(get_rot2(self.param_space), 0, 1, 0)

        # Apply cube rotation
        glRotatef(get_rot_cube1(self.param_space), 1, 0, 0)
        glRotatef(get_rot_cube2(self.param_space), 0, 1, 0)

        for u in range(NUM_GRIDS_U):
            for v in range(NUM_GRIDS_V):
                for w in range(NUM_GRIDS_W):
                    glPushMatrix()
                    glTranslatef(
                        (w - (NUM_GRIDS_W - 1) / 2) * (GRID_SIZE + 2),
                        (v - (NUM_GRIDS_V - 1) / 2) * (GRID_SIZE + 2),
                        -(u - (NUM_GRIDS_U - 1) / 2) * (GRID_SIZE + 2)
                    )

                    # Draw subgrid
                    self.draw_subgrid()

                    # Draw snake
                    for segment in snake:
                        if segment[3] == w and segment[4] == v and segment[5] == u:
                            self.draw_cube(segment[:3], get_snake_fill_color(self.param_space), get_snake_line_color(self.param_space))

                    # Draw apples
                    for apple in apples:
                        if apple[3] == w and apple[4] == v and apple[5] == u:
                            self.draw_cube(apple[:3], get_apple_fill_color(self.param_space), get_apple_line_color(self.param_space))

                    glPopMatrix()

        # Draw lines between snake segments
        self.draw_snake_lines(snake)

        # Save frame if frame_output_path is set
        self.frame_count += 1
        if frame_output_path is not None:
            self.save_frame(frame_output_path)

        pygame.display.flip()

        # Increment snake movement counter
        self.snake_movement_counter += 1
        if self.snake_movement_counter >= FRAMES_PER_SNAKE_MOVEMENT:
            self.snake_movement_counter = 0
            return True  # Signal to move the snake
        return False  # Don't move the snake yet



    def save_frame(self, frame_output_path):
        frame_filename = f"{frame_output_path}/frame_{self.frame_count:05d}.png"
        screen = pygame.display.get_surface()
        size = screen.get_size()
        buffer = glReadPixels(0, 0, *size, GL_RGBA, GL_UNSIGNED_BYTE)
        screen_surf = pygame.image.fromstring(buffer, size, "RGBA")
        pygame.image.save(screen_surf, frame_filename)

    def draw_main_grid_axes(self):
        glLineWidth(get_main_grid_line_thickness(self.param_space))
        glBegin(GL_LINES)
        main_grid_color = get_main_grid_axes_color(self.param_space)
        glColor4f(main_grid_color[0]/255.0, main_grid_color[1]/255.0, main_grid_color[2]/255.0, main_grid_color[3]/255.0)
        
        half_w = (NUM_GRIDS_W * (GRID_SIZE + 2)) / 2
        half_v = (NUM_GRIDS_V * (GRID_SIZE + 2)) / 2
        half_u = (NUM_GRIDS_U * (GRID_SIZE + 2)) / 2
        
        # Draw main grid axes
        for i in range(NUM_GRIDS_W + 1):
            x = i * (GRID_SIZE + 2) - half_w
            glVertex3f(x, -half_v, 0)
            glVertex3f(x, half_v, 0)
        
        for j in range(NUM_GRIDS_V + 1):
            y = j * (GRID_SIZE + 2) - half_v
            glVertex3f(-half_w, y, 0)
            glVertex3f(half_w, y, 0)
        
        for k in range(NUM_GRIDS_U + 1):
            z = -k * (GRID_SIZE + 2) + half_u
            glVertex3f(-half_w, 0, z)
            glVertex3f(half_w, 0, z)
            glVertex3f(0, -half_v, z)
            glVertex3f(0, half_v, z)
        
        glEnd()

    def draw_subgrid(self):
        glLineWidth(get_subgrid_line_thickness(self.param_space))
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBegin(GL_LINES)
        
        # Draw subgrid interior
        grid_color = get_grid_color(self.param_space)
        glColor4f(grid_color[0]/255.0, grid_color[1]/255.0, grid_color[2]/255.0, grid_color[3]/255.0)
        
        half_size = GRID_SIZE / 2
        
        for i in range(1, GRID_SIZE):
            x = i - half_size
            y = i - half_size
            z = i - half_size
            
            glVertex3f(x, -half_size, -half_size)
            glVertex3f(x, half_size, -half_size)
            glVertex3f(-half_size, y, -half_size)
            glVertex3f(half_size, y, -half_size)
            glVertex3f(x, -half_size, -half_size)
            glVertex3f(x, -half_size, half_size)
            glVertex3f(-half_size, -half_size, z)
            glVertex3f(half_size, -half_size, z)
            glVertex3f(-half_size, y, -half_size)
            glVertex3f(-half_size, y, half_size)
            glVertex3f(-half_size, -half_size, z)
            glVertex3f(-half_size, half_size, z)

        # Draw subgrid axes
        subgrid_axes_color = get_subgrid_axes_color(self.param_space)
        glColor4f(subgrid_axes_color[0]/255.0, subgrid_axes_color[1]/255.0, subgrid_axes_color[2]/255.0, subgrid_axes_color[3]/255.0)
        glVertex3f(-half_size, -half_size, -half_size)
        glVertex3f(half_size, -half_size, -half_size)
        glVertex3f(-half_size, -half_size, -half_size)
        glVertex3f(-half_size, half_size, -half_size)
        glVertex3f(-half_size, -half_size, -half_size)
        glVertex3f(-half_size, -half_size, half_size)
        glVertex3f(half_size, -half_size, -half_size)
        glVertex3f(half_size, half_size, -half_size)
        glVertex3f(half_size, -half_size, -half_size)
        glVertex3f(half_size, -half_size, half_size)
        glVertex3f(-half_size, half_size, -half_size)
        glVertex3f(half_size, half_size, -half_size)
        glVertex3f(-half_size, half_size, -half_size)
        glVertex3f(-half_size, half_size, half_size)
        glVertex3f(-half_size, -half_size, half_size)
        glVertex3f(half_size, -half_size, half_size)
        glVertex3f(-half_size, -half_size, half_size)
        glVertex3f(-half_size, half_size, half_size)
        
        glEnd()
        glDisable(GL_BLEND)

    def draw_cube(self, position, fill_color, line_color):
        x, y, z = position
        cell_width = get_cell_width(self.param_space)
        cell_height = get_cell_height(self.param_space)
        cell_length = get_cell_length(self.param_space)
        
        half_width = cell_width / 2
        half_height = cell_height / 2
        half_length = cell_length / 2
        
        x -= GRID_SIZE / 2
        y -= GRID_SIZE / 2
        z -= GRID_SIZE / 2
        
        vertices = (
            (x - half_width, y - half_height, z - half_length),
            (x + half_width, y - half_height, z - half_length),
            (x + half_width, y + half_height, z - half_length),
            (x - half_width, y + half_height, z - half_length),
            (x - half_width, y - half_height, z + half_length),
            (x + half_width, y - half_height, z + half_length),
            (x + half_width, y + half_height, z + half_length),
            (x - half_width, y + half_height, z + half_length)
        )

        # Draw filled cube
        glBegin(GL_QUADS)
        glColor4f(fill_color[0]/255.0, fill_color[1]/255.0, fill_color[2]/255.0, fill_color[3]/255.0 if len(fill_color) > 3 else 1.0)
        faces = (
            (0, 1, 2, 3),
            (3, 2, 6, 7),
            (7, 6, 5, 4),
            (4, 5, 1, 0),
            (1, 5, 6, 2),
            (4, 0, 3, 7)
        )
        for face in faces:
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()

        # Draw cube edges
        glBegin(GL_LINES)
        glColor4f(line_color[0]/255.0, line_color[1]/255.0, line_color[2]/255.0, line_color[3]/255.0 if len(line_color) > 3 else 1.0)
        edges = (
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        )
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()

    def draw_snake_lines(self, snake):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glLineWidth(get_snake_line_thickness(self.param_space))

        glBegin(GL_LINE_STRIP)
        snake_line_color = get_snake_line_color(self.param_space)
        glColor4f(snake_line_color[0]/255.0, snake_line_color[1]/255.0, snake_line_color[2]/255.0, SNAKE_CONNECTION_ALPHA)
        cell_width = get_cell_width(self.param_space)
        cell_height = get_cell_height(self.param_space)
        cell_length = get_cell_length(self.param_space)
        for segment in snake:
            x, y, z, w, v, u = segment
            glVertex3f(
                (x - GRID_SIZE / 2 + 0.5) * cell_width + (w - (NUM_GRIDS_W - 1) / 2) * (GRID_SIZE + 2),
                (y - GRID_SIZE / 2 + 0.5) * cell_height + (v - (NUM_GRIDS_V - 1) / 2) * (GRID_SIZE + 2),
                (z - GRID_SIZE / 2 + 0.5) * cell_length - (u - (NUM_GRIDS_U - 1) / 2) * (GRID_SIZE + 2)
            )
        glEnd()

        glDisable(GL_BLEND)
        glDisable(GL_LINE_SMOOTH)

    def draw_text(self, text, position):
        font = pygame.font.Font(None, 36)
        textSurface = font.render(text, True, (255, 255, 255, 255))
        textData = pygame.image.tostring(textSurface, "RGBA", True)
        glWindowPos2d(*position)
        glDrawPixels(textSurface.get_width(), textSurface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, textData)

    def cleanup(self):
        # Stop audio playback when the renderer is done
        if play_song:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
