#!/usr/bin/env python3

from math import pi, sin, cos

import time, json, math
from pyglet.gl import *
from random import random
from collections import deque, OrderedDict
from housepy import config, log, util, animation

def update(dt):
    global rx, ry, rz
    rx += dt * 1
    ry += dt * 80
    rz += dt * 30
    rx %= 360
    ry %= 360
    rz %= 360

def draw():
    glTranslatef(0, 0, -4)
    glRotatef(*rotate_x)
    glRotatef(*rotate_y)
    # ctx.line(0, 0, 1, 1)
    # ctx.line(0, 1, 1, 0)

    # glRotatef(ry, 0, 1, 0)

    # ctx.line3D(-1, -1, 0, 1, 1, 0, color=(1., 0., 0., 1.))
    # ctx.line3D(-1, 1, 0, 1, -1, 0, color=(0., 1., 0., 1.))
    ctx.line3D(-1, 0, 0, 1, 0, 0, color=(1., 0., 0., 1.))
    ctx.line3D(0, -1, 0, 0, 1, 0, color=(0., 1., 0., 1.))
    ctx.line3D(0, 0, -1, 0, 0, 1, color=(0., 0., 1., 1.))

    ctx.rect(-1, -1, 2., 2., color=(0., 0., 0., .5))

    # ctx.line(0, 0, 1, 1, color=(1., 0., 1., 1.), thickness=10.0)

    # glRotatef(rz, 0, 0, 1)
    
    # glRotatef(rx, 1, 0, 0)
    # torus.draw()


class Torus(object):
    def __init__(self, radius, inner_radius, slices, inner_slices):

        # Create the vertex and normal arrays.
        vertices = []
        normals = []

        u_step = 2 * pi / (slices - 1)
        v_step = 2 * pi / (inner_slices - 1)
        u = 0.
        for i in range(slices):
            cos_u = cos(u)
            sin_u = sin(u)
            v = 0.
            for j in range(inner_slices):
                cos_v = cos(v)
                sin_v = sin(v)

                d = (radius + inner_radius * cos_v)
                x = d * cos_u
                y = d * sin_u
                z = inner_radius * sin_v

                nx = cos_u * cos_v
                ny = sin_u * cos_v
                nz = sin_v

                vertices.extend([x, y, z])
                normals.extend([nx, ny, nz])
                v += v_step
            u += u_step

        # Create ctypes arrays of the lists
        vertices = (GLfloat * len(vertices))(*vertices)
        normals = (GLfloat * len(normals))(*normals)

        # Create a list of triangle indices.
        indices = []
        for i in range(slices - 1):
            for j in range(inner_slices - 1):
                p = i * inner_slices + j
                indices.extend([p, p + inner_slices, p + inner_slices + 1])
                indices.extend([p,  p + inner_slices + 1, p + 1])
        indices = (GLuint * len(indices))(*indices)

        # Compile a display list
        self.list = glGenLists(1)
        glNewList(self.list, GL_COMPILE)

        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, vertices)
        glNormalPointer(GL_FLOAT, 0, normals)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)
        glPopClientAttrib()

        glEndList()

    def draw(self):
        glColor4f(0., 0., 0., 1.)    
        glLineWidth(1.0)         
        glCallList(self.list)    





ctx = animation.Context(1000, 300, background=(1., 1., 1., 1.), fullscreen=False, title="TREE", _3d=True) 

torus = Torus(1, 0.3, 50, 30)
rx = ry = rz = 0

rotate_x = 0, 0, 0, 0
rotate_y = 0, 0, 0, 0


def on_mouse_drag(data):
    x, y, dx, dy, button, modifers = data
    print(data)
    global rotate_x, rotate_y
    SCALE = -0.5
    rotate_x = (dx * SCALE) + rotate_x[0], 0, 1, 0
    rotate_y = (dy * SCALE) + rotate_y[0], 1, 0, 0
ctx.add_callback("mouse_drag", on_mouse_drag)

ctx.start(draw, update)

