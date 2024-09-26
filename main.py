#!/usr/bin/env python

from random import choice
import sched, time, math
from panda3d.core import Point3, Vec4
from direct.showbase.ShowBase import ShowBase
from direct.motiontrail.MotionTrail import MotionTrail
from direct.interval.LerpInterval import LerpPosInterval, LerpHprInterval
from direct.interval.LerpInterval import LerpScaleInterval
from direct.interval.LerpInterval import LerpTexOffsetInterval
from direct.interval.IntervalGlobal import Sequence
from direct.task.TaskManagerGlobal import taskMgr

class OscillatingTree(ShowBase):
    spheres = 15
    radius = 0
    h = 0
    c = 0

    def __init__(self):
        ShowBase.__init__(self)

        self.set_background_color(0.0, 0.0, 0.0, 1)
        self.cam.set_pos(0, -120, 0)
        # self.cam.look_at(render)

        flame_colors = (
            Vec4(1.0, 0.0, 0.0, 1),
            Vec4(1.0, 0.5, 0.0, 1),
            Vec4(0.0, 0.0, 0.9, 1),
            Vec4(0.0, 0.0, 0.2, 1),
        )
        
        taskMgr.doMethodLater(1 / 30, self.updateParameter, "update_r")

        pivot = [None] * self.spheres
        self.charcoal = [None] * self.spheres
        fire_trail = [None] * self.spheres

        for kk in range(self.spheres):
            pivot[kk] = render.attach_new_node("pivot")
            pivot[kk].hprInterval(6 + kk, (360, 0, 0)).loop()
            Sequence( 
                LerpPosInterval(
                    pivot[kk], 
                    2 - kk / 30, 
                    (0, 0,-2), 
                    (0, 0, 1), 
                    blendType="easeInOut"),
                LerpPosInterval(
                    pivot[kk], 
                    2 - kk / 30, 
                    (0, 0, 1), 
                    (0, 0, -2), 
                    blendType="easeInOut")
            ).loop()

            self.charcoal[kk] = loader.load_model("models/smiley").copy_to(
                pivot[kk])
            self.charcoal[kk].set_texture(loader.load_texture(
                "models/plasma.png"), 
                1)
            self.charcoal[kk].set_color(flame_colors[0] * 0)
            self.charcoal[kk].set_x(self.radius)

            fire_trail[kk] = MotionTrail("fire trail", self.charcoal[kk])
            fire_trail[kk].register_motion_trail()
            fire_trail[kk].geom_node_path.reparent_to(render)
            fire_trail[kk].set_texture(loader.load_texture("models/plasma.png"))
            fire_trail[kk].time_window = 5 + 3 * kk 

            center = render.attach_new_node("center")
            around = center.attach_new_node("around")
            around.set_z(1)
            res = 8 # Amount of angles in "circle". Higher is smoother.
            for ii in range(res + 1):
                center.set_r((360 / res) * ii)
                vertex_pos = around.get_pos(render)
                fire_trail[kk].add_vertex(vertex_pos)

                start_color = (flame_colors[ii % len(flame_colors)] * 
                    (math.sin(kk) + 1.3))
                end_color = Vec4(1, kk / self.spheres, 1 - kk / self.spheres, 1)
                fire_trail[kk].set_vertex_color(ii, start_color, end_color)

            fire_trail[kk].update_vertices()

            LerpHprInterval(fire_trail[kk], 16, (0, 0, -360)).loop()
            LerpTexOffsetInterval(
                fire_trail[kk].geom_node_path, 
                60, 
                (1, 1), 
                (1, 0)).loop()
            Sequence(
                LerpScaleInterval(
                    fire_trail[kk], 
                    0.3, 
                    1.4, 
                    0.4, 
                    blendType="easeInOut"),
                LerpScaleInterval(
                    fire_trail[kk], 
                    0.2, 
                    0.5, 
                    1.4,
                    blendType="easeInOut")
            ).loop()

        self.run()

    def updateParameter(self, task):
        self.c += 0.01
        self.radius = 20 * (-math.cos(self.c) + 1)
        for k in range(self.spheres):
            self.h = (5 + k / 2) * math.sin(self.c)
            self.charcoal[k].set_x(self.radius)
            self.charcoal[k].set_z(self.h)
            if self.c > 12.56:
                self.h = self.c ** 2
            self.charcoal[k].set_z(self.h)
        return task.again

if "__main__" == __name__:
    ot = OscillatingTree()
    ot.run()
