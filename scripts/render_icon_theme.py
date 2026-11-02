"""Antu system icon scenes. Blender 5.2 / Cycles, original CC-BY-SA-4.0 artwork.

Imports the APPROVED renderer's geometry/light helpers without invoking its export.
Writes only brand/masters/icon-theme; never touches any approved app, logo or wallpaper.
  blender -b --python-exit-code 1 -P scripts/render_icon_theme.py -- --proof
  blender -b --python-exit-code 1 -P scripts/render_icon_theme.py --
"""
import argparse
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_art as A
from antu_icon_catalog import ALIASES, CATALOG, MIME_ACCENTS, SIZES

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT/"brand/masters/icon-theme"
PALETTE = {
    "lava": A.LAVA, "neutral": (0.44, 0.47, 0.51, 1),
    "sage": (0.16, 0.34, 0.26, 1), "steel": (0.17, 0.29, 0.40, 1),
    "brick": (0.56, 0.12, 0.08, 1), "copper": (0.56, 0.28, 0.12, 1),
    "amber": (0.54, 0.38, 0.13, 1),
}
M = {}
TARGET = 256


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def plate(name, x0, y0, x1, y1, z, depth, mat, bevel=0.04):
    return A.solid(name, rect(x0, y0, x1, y1), z, depth, M[mat] if isinstance(mat, str) else mat, bevel)


def disk(name, x, y, z, radius, mat="silver", flatten=0.25):
    return A.sphere(name, (x, y, z), radius, M[mat] if isinstance(mat, str) else mat, (1, 1, flatten))


def stroke(name, points, z, width, mat="silver", closed=False):
    return A.curve(name, [(x, y, z) for x, y in points], width,
                   M[mat] if isinstance(mat, str) else mat, closed)


def ring(name, x, y, z, radius, width, mat="silver", a0=0, a1=2*math.pi):
    pts = [(x+radius*math.cos(a0+(a1-a0)*i/96), y+radius*math.sin(a0+(a1-a0)*i/96)) for i in range(97)]
    return stroke(name, pts, z, width, mat, a1-a0 >= 2*math.pi)


def transformed(builder, scale=1, x=0, y=0, z=0):
    before = set(bpy.data.objects)
    builder()
    transform = Matrix.Translation((x, y, z)) @ Matrix.Scale(scale, 4)
    for o in set(bpy.data.objects)-before:
        o.matrix_world = transform @ o.matrix_world


def glyph(kind, x=0, y=0, z=0.45, scale=1, accent="lava"):
    """Original flush inlays. Small-size recipes replace details, not just scale them."""
    micro = TARGET <= 24
    small = TARGET <= 32
    # Hand-tuned widths resolve to approximately one lit pixel in a list view.
    w = {16:0.140,22:0.115,24:0.108,32:0.090}.get(TARGET,0.055)
    silver = M["silver"]
    color = M[accent]
    def build():
        def line(pts, width=None, mat=silver):
            return stroke("Machined inlay", pts, 0.035, width or w, mat)
        def fill(pts, mat=silver):
            return A.solid("Inlay face", pts, 0, 0.035, mat, 0.012)
        def dot(px, py, r, mat=silver):
            return disk("Enamel rivet", px, py, 0.045, r, mat, 0.22)
        if kind == "home":
            line([(-0.82, 0.07), (0, 0.79), (0.82, 0.07)])
            line([(-0.59, 0.19), (-0.59, -0.65), (-0.14, -0.65), (-0.14, -0.12),
                  (0.20, -0.12), (0.20, -0.65), (0.59, -0.65), (0.59, 0.19)])
        elif kind in ("display", "terminal"):
            line([(-0.85, -0.27), (-0.85, 0.68), (0.85, 0.68), (0.85, -0.27), (-0.85, -0.27)])
            if kind == "terminal":
                line([(-0.51, 0.44), (-0.19, 0.19), (-0.51, -0.03)], w*1.1)
                line([(0.12, -0.03), (0.56, -0.03)], w*1.1, color)
            else:
                line([(0, -0.3), (0, -0.62)]); line([(-0.46, -0.67), (0.46, -0.67)])
        elif kind in ("text", "document"):
            if kind == "document":
                line([(-0.62, 0.58), (0.57, 0.58)], w*1.4, color)
            else:
                line([(-0.62, 0.58), (0.31, 0.58)])
            for yy, end in [(0.15, 0.62), (-0.26, 0.62), (-0.65, 0.20)]:
                if not micro or yy != -0.26:
                    line([(-0.62, yy), (end, yy)])
        elif kind == "download":
            fill([(-0.15, 0.80), (0.15, 0.80), (0.15, -0.03), (0.62, -0.03),
                  (0, -0.64), (-0.62, -0.03), (-0.15, -0.03)])
            if not micro:
                line([(-0.77, -0.46), (-0.77, -0.79), (0.77, -0.79), (0.77, -0.46)])
        elif kind == "music":
            line([(-0.35, -0.43), (-0.35, 0.58), (0.55, 0.77), (0.55, -0.24)], w*1.2)
            dot(-0.59, -0.49, 0.27); dot(0.31, -0.30, 0.27)
        elif kind == "picture":
            line([(-0.83, -0.69), (-0.83, 0.68), (0.83, 0.68), (0.83, -0.69), (-0.83, -0.69)])
            line([(-0.68, -0.44), (-0.14, 0.12), (0.24, -0.29), (0.52, -0.04), (0.73, -0.36)])
            dot(0.39, 0.36, 0.14 if not micro else 0.19, color)
        elif kind == "video":
            fill([(-0.39, -0.60), (-0.39, 0.65), (0.68, 0.02)], color if not small else silver)
            if not small:
                for xx in (-0.85, 0.85):
                    for yy in (-0.55, 0, 0.55):
                        fill(rect(xx-0.08, yy-0.12, xx+0.08, yy+0.12))
        elif kind == "template":
            for xx in (-0.42, 0.42):
                for yy in (-0.42, 0.42):
                    line([(xx-0.25, yy-0.25), (xx-0.25, yy+0.25),
                          (xx+0.25, yy+0.25), (xx+0.25, yy-0.25), (xx-0.25, yy-0.25)], w*0.9)
        elif kind in ("share", "network"):
            line([(-0.57, -0.48), (0, 0.46), (0.57, -0.48)])
            if kind == "network" and not small:
                line([(-0.57, -0.48), (0.57, -0.48)])
            for xx, yy in [(-0.62, -0.52), (0, 0.57), (0.62, -0.52)]:
                dot(xx, yy, 0.24 if small else 0.20)
        elif kind == "remote":
            pts = [(-0.72, -0.12), (-0.72, 0.25), (-0.46, 0.39), (-0.29, 0.73),
                   (0.12, 0.80), (0.46, 0.46), (0.74, 0.40), (0.84, 0.05), (0.70, -0.12)]
            line(pts)
            line([(0, -0.75), (0, 0.20)]); line([(-0.29, -0.43), (0, -0.75), (0.29, -0.43)])
        elif kind == "gamepad":
            pts = [(-0.95, -0.52), (-0.79, 0.47), (-0.48, 0.62), (0.48, 0.62),
                   (0.79, 0.47), (0.95, -0.52), (0.60, -0.61), (0.29, -0.22),
                   (-0.29, -0.22), (-0.60, -0.61)]
            line(pts+[pts[0]], w*1.2)
            line([(-0.65, 0.17), (-0.19, 0.17)], w*1.1); line([(-0.42, -0.06), (-0.42, 0.40)], w*1.1)
            dot(0.50, 0.24, 0.145, M["lava"])
            if not micro:
                dot(0.27, 0.04, 0.10)
        elif kind == "sealed-document":
            line([(-0.65, -0.36), (-0.65, 0.70), (0.51, 0.70), (0.51, 0.17)])
            line([(-0.36, 0.34), (0.22, 0.34)])
            dot(0.19, -0.36, 0.42, color)
            if not small:
                line([(-0.02, -0.61), (-0.12, -0.94), (0.17, -0.76), (0.45, -0.91), (0.43, -0.56)], w*0.7, color)
        elif kind == "archive":
            fill(rect(-0.22, -0.75, 0.22, 0.75), color)
            if not micro:
                for i in range(5):
                    yy = -0.55+i*0.29
                    fill(rect(-0.48 if i%2 else 0.05, yy, -0.05 if i%2 else 0.48, yy+0.15))
            else:
                line([(-0.58, 0.45), (0.58, 0.45)], w*1.3)
        elif kind in ("settings", "executable"):
            teeth = 8 if small else 12
            pts = []
            for i in range(teeth*4):
                a = i*math.pi*2/(teeth*4)
                rr = 0.88 if i%4 in (1, 2) else 0.69
                pts.append((rr*math.cos(a), rr*math.sin(a)))
            fill(pts)
            dot(0, 0, 0.37, M["dark"])
            dot(0, 0, 0.19, color)
        elif kind == "optical":
            ring("Optical media inlay", 0, 0, 0.04, 0.71, 0.13 if small else 0.105, silver)
            dot(0, 0, 0.15, M["dark"])
            if not small:
                ring("Optical track", 0, 0, 0.045, 0.45, 0.025, color)
        elif kind == "package":
            line([(0, 0.82), (0.72, 0.39), (0.72, -0.44), (0, -0.85), (-0.72, -0.44), (-0.72, 0.39), (0, 0.82)])
            line([(-0.72, 0.39), (0, 0), (0.72, 0.39)]);line([(0, 0), (0, -0.85)], mat=color)
        elif kind == "spreadsheet":
            line([(-0.80, -0.72), (-0.80, 0.72), (0.80, 0.72), (0.80, -0.72), (-0.80, -0.72)])
            line([(-0.80, 0.21), (0.80, 0.21)], mat=color)
            line([(-0.23, -0.72), (-0.23, 0.72)])
            if not micro:
                line([(0.29, -0.72), (0.29, 0.72)]);line([(-0.80, -0.25), (0.80, -0.25)])
        elif kind == "presentation":
            line([(-0.78, -0.64), (-0.78, 0.68), (0.78, 0.68), (0.78, -0.64)])
            for xx, hh in [(-0.47, 0.18), (0, 0.51), (0.47, 0.84)]:
                fill(rect(xx-0.13, -0.52, xx+0.13, hh-0.52), color if xx==0.47 else silver)
        elif kind in ("script", "terminal-code"):
            line([(-0.29, 0.55), (-0.83, 0), (-0.29, -0.55)])
            line([(0.29, 0.55), (0.83, 0), (0.29, -0.55)])
            if not micro:
                line([(0.14, 0.69), (-0.14, -0.69)], mat=color)
        elif kind == "files":
            fill([(-0.93, -0.67), (-0.93, 0.63), (-0.24, 0.63), (-0.02, 0.36),
                  (0.93, 0.36), (0.93, -0.67)])
            fill(rect(-0.70, -0.44, 0.70, 0.02), M["dark"])
            line([(-0.54, -0.21), (0.54, -0.21)], mat=color)
        elif kind == "discover":
            line([(-0.70, -0.75), (-0.70, 0.38), (0.70, 0.38), (0.70, -0.75), (-0.70, -0.75)])
            pts=[(0.36*math.cos(a), 0.40+0.39*math.sin(a)) for a in [math.pi*i/48 for i in range(49)]]
            line(pts)
            dot(0, -0.20, 0.25, color)
        elif kind == "editor":
            line([(-0.67, -0.72), (-0.67, 0.72), (0.45, 0.72), (0.45, -0.23)])
            line([(-0.30, 0.30), (0.10, 0.30)])
            line([(-0.10, -0.61), (0.72, 0.33)], w*2.2)
            fill([(-0.20, -0.78), (-0.10, -0.41), (0.09, -0.59)], color)
        elif kind == "capture":
            for sx in (-1, 1):
                for sy in (-1, 1):
                    line([(sx*0.38, sy*0.79), (sx*0.79, sy*0.79), (sx*0.79, sy*0.38)], w*1.4)
            ring("Focus lens", 0, 0, 0.04, 0.33, w*1.1, color)
        elif kind == "calculator":
            line([(-0.68, -0.85), (-0.68, 0.85), (0.68, 0.85), (0.68, -0.85), (-0.68, -0.85)])
            fill(rect(-0.44, 0.27, 0.44, 0.60), color)
            for xx in (-0.31, 0.31):
                for yy in ((-0.17, -0.59) if small else (-0.12, -0.43, -0.73)):
                    dot(xx, yy, 0.14 if small else 0.10)
        elif kind == "globe":
            ring("Network meridian", 0, 0, 0.04, 0.80, w, silver)
            line([(-0.80, 0), (0.80, 0)])
            pts=[(0.32*math.cos(a), 0.77*math.sin(a)) for a in [i*math.pi*2/96 for i in range(97)]]
            line(pts)
            if not small:
                for yy in (-0.38, 0.38):line([(-0.68, yy), (0.68, yy)], w*0.7)
            dot(0.55, -0.55, 0.19, color)
        elif kind == "sound":
            fill([(-0.88, -0.25), (-0.48, -0.25), (0.06, -0.76),
                  (0.06, 0.76), (-0.48, 0.25), (-0.88, 0.25)])
            for rr in ([0.73] if micro else [0.48, 0.84]):
                ring("Sound wave inlay", 0.05, 0, 0.04, rr, w, color if rr>0.7 else silver, -0.8, 0.8)
        else:
            raise ValueError("Unknown original glyph: "+kind)
    transformed(build, scale, x, y, z)


def folder(kind):
    micro = TARGET <= 32
    back = [(-1.83, -1.28), (1.83, -1.28), (1.83, 1.05), (-0.23, 1.05),
            (-0.58, 1.48), (-1.83, 1.48)]
    A.solid("Anodised folder spine", back, -0.11, 0.22, M["edge"], 0.075)
    A.solid("Obsidian folder back", [(x*0.975,y*0.975) for x,y in back], 0.08, 0.08, M["folder"], 0.045)
    if kind == "open":
        for i in range(1 if micro else 2):
            plate("Visible silver filing", -1.47+i*0.06, -0.83, 1.48, 1.13-i*0.15, 0.17+i*0.025, 0.045, "paper", 0.035)
    front = [(-1.73, -1.30), (1.73, -1.30), (1.96, 0.78 if kind != "open" else 0.26),
             (-1.96, 0.78 if kind != "open" else 0.26)]
    A.solid("Folded obsidian front", front, 0.16 if kind != "open" else 0.45, 0.17, M["folder"], 0.085)
    z = 0.345 if kind != "open" else 0.63
    stroke("Folder lip / silver reveal", [(-1.82, 0.78), (1.82, 0.78)] if kind != "open" else [(-1.81, 0.26), (1.81, 0.26)],
           z, 0.025 if micro else 0.012, "edge")
    if kind not in ("folder", "open"):
        glyph(kind, y=-0.25, z=z+0.012, scale=0.78 if micro else 0.69,
              accent="lava" if kind=="gamepad" else "silver")
    if kind == "gamepad":
        plate("Lava games tab", -1.61, 1.19, -0.79, 1.30, 0.19, 0.03, "lava", 0.025)


def paper(kind):
    micro = TARGET <= 32
    pts = [(-1.28, -1.62), (1.28, -1.62), (1.28, 0.83), (0.48, 1.64), (-1.28, 1.64)]
    A.solid("Anodised folio edge", pts, -0.12, 0.25, M["edge"], 0.055)
    A.solid("Obsidian folio", [(x*0.962,y*0.974) for x,y in pts], 0.10, 0.11, M["folder"], 0.035)
    # A real raised triangular folded corner, with a soft cast shadow.
    A.solid("Folded silver corner", [(0.45, 1.56), (0.45, 0.83), (1.19, 0.83)], 0.23, 0.05, M["paper"], 0.025)
    accent = MIME_ACCENTS[kind]
    glyph(kind, y=-0.13, z=0.235, scale=0.90 if micro else 0.86, accent=accent)
    plate("Type material signature", -0.78, -1.31, 0.78, -1.17 if micro else -1.25, 0.235, 0.025, accent, 0.018)


def tile():
    A.solid("Approved app unibody", A.squircle(1.8, 4.3), -0.23, 0.44, M["edge"], 0.09)
    A.solid("Approved obsidian face", A.squircle(1.755, 4.3), 0.13, 0.12, M["body"], 0.055)
    if TARGET > 32:
        A.curve("Rim catchlight", [(x,y,0.257) for x,y in A.squircle(1.715,4.3)], 0.009, M["edge"], True)


def trash(full=False):
    micro = TARGET <= 32
    if full:
        for i in range(1 if micro else 3):
            p=plate("Discarded paper", -0.63+i*0.24, 0.23, 0.30+i*0.24, 1.22+(i%2)*0.20, 0.08, 0.07, "paper", 0.04)
            p.rotation_euler.z = [-0.17,0.2,0.06][i]
    body=[(-0.95,-1.44),(0.95,-1.44),(1.18,0.79),(-1.18,0.79)]
    A.solid("Obsidian recycling vessel",body,0.12,0.38,M["folder"],0.10)
    if not micro:
        for xx in (-0.56,0,0.56):stroke("Vertical bin machining",[(xx,-1.15),(xx,0.52)],0.515,0.025,"edge")
    plate("Silver lid",-1.29,0.78,1.29,0.99,0.50,0.13,"silver",0.06)
    if not full:
        stroke("Lid handle",[(-0.37,1.01),(-0.37,1.27),(0.37,1.27),(0.37,1.01)],0.53,0.08,"silver")
    else:
        disk("Full-bin lava marker",0,-0.25,0.53,0.17,"lava")


def device(kind):
    small=TARGET<=32
    if kind in ("display","laptop","phone"):
        if kind=="phone":
            plate("Anodised phone rim",-0.81,-1.62,0.81,1.62,0,0.28,"silver",0.12)
            plate("Phone obsidian glass",-0.72,-1.51,0.72,1.51,0.25,0.05,"dark",0.10)
            stroke("Phone horizon",[(-0.51,-0.76),(-0.20,-0.39),(0.21,-0.64),(0.51,-0.12)],0.32,0.065 if small else 0.03,"lava")
            if not small:disk("Front optics",0,1.26,0.32,0.055,"edge")
            return
        plate("Display silver chassis",-1.65,-0.48,1.65,1.47,0,0.25,"silver",0.09)
        plate("Optically black display",-1.53,-0.36,1.53,1.35,0.23,0.06,"dark",0.045)
        stroke("Lava horizon on glass",[(-1.24,-0.02),(-0.45,0.34),(0.23,0.05),(1.24,0.69)],0.31,0.075 if small else 0.035,"lava")
        if kind=="laptop":
            A.solid("Laptop deck",[(-1.66,-0.52),(1.66,-0.52),(1.97,-1.31),(-1.97,-1.31)],0.20,0.12,M["silver"],0.065)
            if not small:
                plate("Keyboard well",-1.25,-0.91,1.25,-0.60,0.34,0.035,"dark",0.03)
                plate("Trackpad",-0.40,-1.18,0.40,-0.98,0.34,0.015,"edge",0.02)
        else:
            plate("Display stem",-0.17,-1.14,0.17,-0.43,0,0.19,"silver",0.04)
            plate("Display foot",-0.77,-1.34,0.77,-1.13,0.02,0.15,"edge",0.06)
    elif kind in ("harddisk","ssd"):
        plate("Drive anodised shell",-1.23,-1.59,1.23,1.59,0,0.36,"silver",0.12)
        plate("Drive obsidian enclosure",-1.13,-1.48,1.13,1.48,0.31,0.08,"body",0.08)
        if kind=="harddisk":
            disk("Magnetic platter",0,0.29,0.46,0.82,"silver")
            disk("Spindle",0,0.29,0.69,0.20,"dark")
            stroke("Read arm",[(0.74,-0.86),(0.49,-0.28),(0.04,0.22)],0.73,0.10 if small else 0.065,"edge")
        else:
            for xx in (-0.52,0.52):
                for yy in (-0.42,0.55):plate("Solid-state ceramic module",xx-0.31,yy-0.30,xx+0.31,yy+0.30,0.42,0.08,"edge",0.035)
            plate("Lava controller",-0.42,-1.17,0.42,-0.94,0.43,0.06,"lava",0.025)
        if not small:
            for xx in (-0.93,0.93):
                for yy in (-1.29,1.29):disk("Case fastener",xx,yy,0.43,0.055,"edge")
    elif kind=="usb":
        plate("USB connector",-0.60,0.54,0.60,1.62,0,0.23,"silver",0.05)
        for xx in (-0.29,0.29):plate("USB connector aperture",xx-0.13,0.95,xx+0.13,1.26,0.24,0.015,"dark",0.018)
        plate("USB obsidian body",-0.79,-1.54,0.79,0.65,0.04,0.38,"body",0.15)
        plate("USB lava seam",-0.53,-0.96,0.53,-0.83,0.44,0.03,"lava",0.025)
    elif kind=="optical":
        disk("Optical disc body",0,0,0,1.52,"silver",0.045)
        disk("Obsidian optical coating",0,0,0.09,1.37,"body",0.018)
        disk("Translucent hub",0,0,0.15,0.42,"silver",0.045)
        disk("Optical spindle aperture",0,0,0.18,0.19,"dark",0.02)
        if not small:
            for rr in (0.64,1.17,1.26):ring("Concentric media machining",0,0,0.13,rr,0.012,"edge")
        ring("Lava optical sector",0,0,0.145,1.25,0.07 if small else 0.025,"lava",0.18,1.05)
    elif kind=="gamepad":
        pts=[(-1.74,-0.79),(-1.48,0.86),(-0.91,1.09),(0.91,1.09),(1.48,0.86),(1.74,-0.79),
             (1.09,-1.03),(0.51,-0.43),(-0.51,-0.43),(-1.09,-1.03)]
        A.solid("Ergonomic obsidian controller",pts,0,0.47,M["body"],0.19)
        plate("Horizontal D pad",-1.24,0.18,-0.47,0.40,0.49,0.08,"silver",0.03)
        plate("Vertical D pad",-0.97,-0.09,-0.74,0.67,0.50,0.08,"silver",0.03)
        for xx,yy in [(0.99,0.59),(1.28,0.28),(0.70,0.28),(0.99,-0.02)]:
            disk("Unbranded controller key",xx,yy,0.53,0.14 if small else 0.115,"lava" if xx==0.99 else "silver")
        if not small:
            for xx in (-0.45,0.45):disk("Controller thumbstick",xx,-0.34,0.54,0.21,"edge")
    elif kind=="keyboard":
        plate("Keyboard unibody",-1.88,-1.01,1.88,1.01,0,0.28,"edge",0.13)
        cols=5 if small else 9
        for row in range(3):
            for col in range(cols):
                xx=-1.53+3.06*col/(cols-1);yy=0.64-row*0.50
                half=0.23 if small else 0.125
                plate("Individual tactile key",xx-half,yy-0.17,xx+half,yy+0.17,0.30,0.09,"body",0.035)
        plate("Lava space bar",-0.70,-0.84,0.70,-0.63,0.30,0.09,"lava",0.035)
    elif kind=="mouse":
        A.solid("Mouse anodised edge",[(x*0.65,y) for x,y in A.squircle(1.44,2.7)],0,0.38,M["silver"],0.15)
        A.solid("Ergonomic obsidian mouse",[(x*0.64,y*0.97) for x,y in A.squircle(1.42,2.7)],0.25,0.34,M["body"],0.16)
        stroke("Split mouse buttons",[(0,1.20),(0,0.25)],0.61,0.025 if not small else 0.045,"edge")
        plate("Lava scroll wheel",-0.11,0.45,0.11,0.96,0.61,0.08,"lava",0.055)
    elif kind=="headphones":
        pts=[(1.13*math.cos(math.pi*i/96),-0.02+1.42*math.sin(math.pi*i/96)) for i in range(97)]
        stroke("Anodised headband",pts,0.08,0.19,"silver")
        for xx in (-1.13,1.13):
            plate("Obsidian ear cup",xx-0.36,-1.18,xx+0.36,0.30,0.18,0.40,"body",0.17)
            plate("Soft ear cushion",xx-0.20,-1.03,xx+0.20,0.13,0.59,0.12,"dark",0.12)
        plate("Lava left-channel detail",-1.50,-0.72,-1.37,-0.14,0.60,0.03,"lava",0.035)
    elif kind=="speakers":
        for xx in (-0.91,0.91):
            plate("Speaker cabinet",xx-0.64,-1.47,xx+0.64,1.47,0,0.37,"body",0.11)
            disk("Silver woofer rim",xx,-0.43,0.42,0.47,"silver")
            disk("Obsidian woofer",xx,-0.43,0.53,0.34,"dark")
            disk("Tweeter",xx,0.74,0.43,0.23,"edge")
        disk("Speaker lava indicator",0.91,-1.15,0.44,0.075 if not small else 0.12,"lava")
    elif kind=="printer":
        plate("Printer paper input",-0.96,0.58,0.96,1.56,0,0.08,"paper",0.03)
        plate("Printer obsidian housing",-1.58,-0.69,1.58,0.93,0.10,0.43,"body",0.13)
        plate("Paper exit shadow",-1.17,-0.48,1.17,-0.13,0.55,0.03,"dark",0.035)
        plate("Printed page",-0.94,-1.49,0.94,-0.32,0.60,0.035,"paper",0.03)
        if not small:
            for yy in (-0.69,-0.94):stroke("Printed abstract rules",[(-0.62,yy),(0.46,yy)],0.65,0.025,"edge")
        disk("Printer indicator",1.12,0.55,0.56,0.10,"lava")
    else:
        raise ValueError(kind)


def scene(context,name,target,proof=False):
    global TARGET,M
    TARGET=target
    n=1024 if target==256 else max(128,target*4)
    A.reset(n,n,48 if target>=64 else 32,True)
    A.world((0.13,0.14,0.16),0.45)
    M={
        "body":A.material("Approved polished obsidian",(0.026,0.027,0.033,1),0.58,0.21,coat=0.65),
        "folder":A.material("Folder obsidian / brighter edges",(0.047,0.050,0.059,1),0.46,0.26,coat=0.45),
        "edge":A.material("Approved anodised edge",(0.080,0.083,0.093,1),0.78,0.24),
        "silver":A.material("Approved bead-blasted silver",A.SILVER,0.82 if target>32 else 0.5,0.23),
        "paper":A.material("Satin folded silver",(0.59,0.62,0.66,1),0.35,0.32),
        "dark":A.material("Optically black ceramic",(0.009,0.010,0.014,1),0.45,0.22,coat=0.4),
    }
    for key,color in PALETTE.items():M[key]=A.material(key+" enamel",color,0.28,0.2,0.12 if key=="lava" else 0,0.6)
    kind=CATALOG[context][name]
    if context=="places":
        if kind=="network":glyph("network",scale=1.62,z=0.25)
        elif kind.startswith("trash"):trash(kind=="trash-full")
        else:folder(kind)
    elif context=="devices":device(kind)
    elif context=="mimetypes":paper(kind)
    elif context=="apps":
        tile()
        k={16:1.31,22:1.27,24:1.24,32:1.20,48:1.17,64:1.14,128:1.12,256:1.10}[target]
        glyph(kind,z=0.35,scale=k)
    A.camera((0,-0.48,12),(0,0,0),ortho=4.24 if context!="mimetypes" else 4.0)
    A.area("Key / approved softbox northwest",(-3.5,4.8,6),(0,0,0),520,4,(0.93,0.96,1),5)
    A.area("Approved narrow silver rim",(4,1.5,4),(0,0,0),250,1.4,(1,0.94,0.88),5)
    A.area("Approved gentle fill",(0,-4,6),(0,0,0),70,5)


def main():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--proof",action="store_true")
    p.add_argument("--only",default="")
    p.add_argument("--sizes",default="")
    p.add_argument("--force",action="store_true")
    a=p.parse_args(argv)
    only=set(a.only.split(",")) if a.only else None
    sizes=tuple(int(s) for s in a.sizes.split(",")) if a.sizes else SIZES
    if any(s not in SIZES for s in sizes):p.error("Unsupported optical size")
    proof_names={"folder","folder-games","user-trash-full","text-plain","application-pdf",
                 "image-x-generic","input-gaming","computer-laptop","systemsettings","org.kde.dolphin"}
    for context,icons in CATALOG.items():
        for name in icons:
            if name in ALIASES or name=="start-here" or only and name not in only:continue
            if a.proof and name not in proof_names:continue
            for size in ((256,16) if a.proof else sizes):
                path=OUTPUT/context/name/f"{size}.png"
                if path.exists() and not a.force:continue
                print(f"ANTU_THEME {context}/{name} {size}",flush=True)
                scene(context,name,size,a.proof)
                A.save(path)


if __name__=="__main__":main()
