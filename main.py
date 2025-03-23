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
import os
from panda3d.core import PNMImage, Filename
import subprocess
import shutil
import uuid

class Lights(ShowBase):
    spheres = 15
    radius = 0
    h = 0
    c = 0

    def __init__(self):
        ShowBase.__init__(self)

        self.set_background_color(0.0, 0.0, 0.0, 1)
        self.cam.set_pos(0, -120, 0)

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

        for sphere in range(self.spheres):
            pivot[sphere] = render.attach_new_node("pivot")
            pivot[sphere].hprInterval(6 + sphere, (360, 0, 0)).loop()
            Sequence( 
                LerpPosInterval(
                    pivot[sphere], 
                    2 - sphere / 30, 
                    (0, 0,-2), 
                    (0, 0, 1), 
                    blendType="easeInOut"),
                LerpPosInterval(
                    pivot[sphere], 
                    2 - sphere / 30, 
                    (0, 0, 1), 
                    (0, 0, -2), 
                    blendType="easeInOut")
            ).loop()

            self.charcoal[sphere] = loader.load_model("models/smiley").copy_to(
                pivot[sphere]
            )
            self.charcoal[sphere].set_texture(
                loader.load_texture(
                    "static/plasma.png"
                ), 
                1
            )
            self.charcoal[sphere].set_color(flame_colors[0] * 0)
            self.charcoal[sphere].set_x(self.radius)

            fire_trail[sphere] = MotionTrail("fire trail", self.charcoal[sphere])
            fire_trail[sphere].register_motion_trail()
            fire_trail[sphere].geom_node_path.reparent_to(render)
            fire_trail[sphere].set_texture(loader.load_texture("static/plasma.png"))
            fire_trail[sphere].time_window = 5 + 3 * sphere 

            center = render.attach_new_node("center")
            around = center.attach_new_node("around")
            around.set_z(1)
            res = 8
            for ii in range(res + 1):
                center.set_r((360 / res) * ii)
                vertex_pos = around.get_pos(render)
                fire_trail[sphere].add_vertex(vertex_pos)

                start_color = (flame_colors[ii % len(flame_colors)] * 
                    (math.sin(sphere) + 1.3))
                end_color = Vec4(
                    1, 
                    sphere / self.spheres, 
                    1 - sphere / self.spheres, 
                    1
                )
                fire_trail[sphere].set_vertex_color(ii, start_color, end_color)

            fire_trail[sphere].update_vertices()

            LerpHprInterval(fire_trail[sphere], 16, (0, 0, -360)).loop()
            LerpTexOffsetInterval(
                fire_trail[sphere].geom_node_path, 
                60, 
                (1, 1), 
                (1, 0)
            ).loop()
            Sequence(
                LerpScaleInterval(
                    fire_trail[sphere], 
                    0.3, 
                    1.4, 
                    0.4, 
                    blendType="easeInOut"
                ),
                LerpScaleInterval(
                    fire_trail[sphere], 
                    0.2, 
                    0.5, 
                    1.4,
                    blendType="easeInOut"
                )
            ).loop()

        self.frame_count = 0
        self.output_dir = "frames"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.taskMgr.add(self.captureFrame, "CaptureFrame")

        self.run()

    def captureFrame(self, task):
        """Erfasst jeden Frame und speichert ihn als Bild"""
        filename = os.path.join(self.output_dir, f"frame_{self.frame_count:04d}.png")
        self.win.saveScreenshot(Filename(filename))
        self.frame_count += 1
        
        # Prüfe die Frame-Anzahl und erstelle Video, wenn genug Frames vorhanden sind
        if self.frame_count >= 100:  # Passe diese Zahl nach Bedarf an
            print(f"Erstelle Video...")
            self.taskMgr.doMethodLater(1.0, self.createVideoTask, "CreateVideoTask")
            # Deaktiviere weiteres Aufnehmen von Frames
            return task.done
        
        return task.cont

    def createVideoTask(self, task):
        """Task-Wrapper für die Videoerstellung"""
        self.createVideo()
        return task.done

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
            
        # Entferne die Frame-Überprüfung hier, da sie bereits in captureFrame geschieht
        return task.again

    def createVideo(self):
        """Erstellt ein Video aus den gespeicherten Frames"""
        print(f"Erstelle Video aus {self.frame_count} Frames...")
        # Zähle tatsächlich vorhandene PNG-Dateien im Verzeichnis
        png_files = [f for f in os.listdir(self.output_dir) if f.endswith('.png')]
        print(f"Gefundene PNG-Dateien: {len(png_files)}")
        
        cmd = [
            'ffmpeg',
            '-framerate', '30',
            '-i', f'{self.output_dir}/frame_%04d.png',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            'output_video.mp4'
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print("Video wurde erfolgreich erstellt: output_video.mp4")
            videos_dir = "videos"
            if not os.path.exists(videos_dir):
                os.makedirs(videos_dir)

            unique_video_name = f"video_{uuid.uuid4().hex}.mp4"
            shutil.move("output_video.mp4", os.path.join(videos_dir, unique_video_name))
            print(f"Video copied as {os.path.join(videos_dir, unique_video_name)}")
            # Optional: Beende die Anwendung nach Videoerstellung
            # self.userExit()
        except subprocess.CalledProcessError as e:
            print(f"Fehler bei der Videoerstellung: {e}")

if "__main__" == __name__:
    ot = Lights()
    ot.run()
