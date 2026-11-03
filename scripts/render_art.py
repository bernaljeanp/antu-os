"""Original Antu app icons: native 4096 px ray-traced material, CC-BY-SA-4.0.

Run with Blender 5.x:
  blender -b --python-exit-code 1 -P scripts/render_art.py -- icons
  blender -b --python-exit-code 1 -P scripts/render_art.py -- icons --preview
Small variants use separate size-specific geometry and detail, not master shrinking.
"""
import argparse
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
MASTERS = ROOT / "brand/masters"
PREVIEWS = ROOT / "brand/previews"
LAVA = (1.0, 0.102, 0.014, 1)
SILVER = (0.72, 0.74, 0.77, 1)
ICON_NAMES = ("antu", "antu-inicio", "antu-instalador", "antu-eclipse", "antu-ia",
              "antu-biblioteca", "antu-observatorio")


def reset(width, height, samples=64, transparent=False):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.worlds):
        for item in list(collection):
            if item.users == 0:
                collection.remove(item)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.samples = samples
    s.cycles.use_denoising = True
    s.cycles.adaptive_threshold = 0.025
    s.cycles.max_bounces = 8
    s.cycles.transparent_max_bounces = 8
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "OPTIX"
        s.cycles.device = "GPU"
    except Exception as exc:
        print("Cycles CPU fallback:", exc, flush=True)
        s.cycles.device = "CPU"
    s.render.resolution_x = width
    s.render.resolution_y = height
    s.render.resolution_percentage = 100
    s.render.film_transparent = transparent
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    s.render.image_settings.color_depth = "8"
    s.render.image_settings.compression = 30
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = 0
    s.render.threads_mode = "FIXED"
    s.render.threads = 8
    return s


def material(name, color, metal=0, rough=0.3, emission=0, coat=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = color
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = color
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Coat Roughness"].default_value = 0.15
    if emission:
        p.inputs["Emission Color"].default_value = color
        p.inputs["Emission Strength"].default_value = emission
    return m


def mesh(name, verts, faces, mat=None, smooth=True, bevel=0):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    o = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(o)
    if mat:
        data.materials.append(mat)
    if smooth:
        for p in data.polygons:
            p.use_smooth = True
    if bevel:
        b = o.modifiers.new("Machined radii", "BEVEL")
        b.width = bevel
        b.segments = 5
        n = o.modifiers.new("Surface normals", "WEIGHTED_NORMAL")
        n.keep_sharp = True
    return o


def solid(name, outline, z, depth, mat, bevel=0.04):
    n = len(outline)
    v = [(x, y, z) for x, y in outline] + [(x, y, z + depth) for x, y in outline]
    f = [tuple(reversed(range(n))), tuple(range(n, n * 2))]
    f += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return mesh(name, v, f, mat, True, bevel)


def squircle(radius, power=4, count=128):
    pts = []
    for i in range(count):
        a = 2 * math.pi * i / count
        c, s = math.cos(a), math.sin(a)
        pts.append((radius * math.copysign(abs(c) ** (2 / power), c),
                    radius * math.copysign(abs(s) ** (2 / power), s)))
    return pts


def curve(name, pts, radius, mat, cyclic=False):
    c = bpy.data.curves.new(name, "CURVE")
    c.dimensions = "3D"
    c.resolution_u = 2
    c.bevel_depth = radius
    c.bevel_resolution = 4
    p = c.splines.new("POLY")
    p.points.add(len(pts) - 1)
    for v, xyz in zip(p.points, pts):
        v.co = (*xyz, 1)
    p.use_cyclic_u = cyclic
    o = bpy.data.objects.new(name, c)
    bpy.context.collection.objects.link(o)
    c.materials.append(mat)
    return o


def sphere(name, pos, radius, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=radius, location=pos)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def cylinder(name, pos, radius, depth, mat, vertices=96):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=pos)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    bevel = o.modifiers.new("Edge polish", "BEVEL")
    bevel.width = min(radius * 0.06, depth * 0.2)
    bevel.segments = 4
    o.modifiers.new("Normals", "WEIGHTED_NORMAL")
    return o


def aim(o, target):
    o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()


def camera(pos, target, ortho=None, lens=40):
    bpy.ops.object.camera_add(location=pos)
    o = bpy.context.object
    aim(o, target)
    if ortho:
        o.data.type = "ORTHO"
        o.data.ortho_scale = ortho
    else:
        o.data.lens = lens
        o.data.clip_end = 1000
    bpy.context.scene.camera = o
    return o


def area(name, pos, target, power, size, color=(1, 1, 1), size_y=None):
    d = bpy.data.lights.new(name, "AREA")
    d.energy, d.color = power, color
    d.shape = "RECTANGLE"
    d.size = size
    d.size_y = size_y if size_y else size
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = pos
    aim(o, target)
    return o


def world(color, strength=1):
    w = bpy.data.worlds.new("Atacama environment")
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    bpy.context.scene.world = w
    return w


def save(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print("ANTU_RENDER", path, flush=True)


def icon_scene(name, target=4096, preview=False):
    # Each small size changes the scene itself: thicker silhouettes, fewer parts,
    # broader highlights and a larger optical glyph. No blind master shrinking.
    micro = target <= 32
    compact = target <= 64
    n = 768 if preview else max(target, 256)
    reset(n, n, 48 if target < 1024 or preview else 96, True)
    world((0.13, 0.14, 0.16), 0.45)
    body = material("Polished obsidian glass", (0.026, 0.027, 0.033, 1), 0.58, 0.21, coat=0.65)
    edge = material("Anodised edge", (0.080, 0.083, 0.093, 1), 0.78, 0.24)
    silver = material("Bead-blasted silver", SILVER, 0.82, 0.23)
    orange = material("Lava enamel", LAVA, 0.28, 0.2, 0.12, 0.6)
    dark = material("Eclipse ceramic", (0.009, 0.01, 0.014, 1), 0.45, 0.22, coat=0.4)
    solid("Unibody", squircle(1.8, 4.3), -0.23, 0.44, edge, 0.09)
    solid("Obsidian face", squircle(1.755, 4.3), 0.13, 0.12, body, 0.055)
    if not micro:
        curve("Rim catchlight", [(x, y, 0.257) for x, y in squircle(1.715, 4.3)], 0.009, edge, True)
    k = {16: 1.16, 24: 1.14, 32: 1.12, 48: 1.075, 64: 1.05, 128: 1.02, 256: 1.01, 512: 1.005}.get(target, 1)
    if name == "antu":
        pts = [(-1.08, -0.96), (-0.14, 1.01), (-0.09, 1.09), (0, 1.13),
               (0.09, 1.09), (0.14, 1.01), (1.08, -0.96), (0.72, -0.96),
               (0, 0.58), (-0.72, -0.96)]
        solid("Solar summit", [(x * k, y * k) for x, y in pts], 0.31, 0.22, silver, 0.045)
        sphere("Solar core", (0, -0.53 * k, 0.48), 0.265 * k, orange, (1, 1, 0.48))
    elif name == "antu-inicio":
        # An architectural threshold with first light inside.
        r = 0.85 * k
        pts = [(-r, -0.99, 0.46), (-r, 0.28, 0.46)]
        pts += [(r * math.cos(math.pi - i * math.pi / 64),
                 0.28 + r * math.sin(math.pi - i * math.pi / 64), 0.46) for i in range(65)]
        pts += [(r, -0.99, 0.46)]
        curve("Silver threshold", pts, (0.17 if micro else 0.135) * k, silver)
        sphere("First light", (0, -0.19, 0.42), 0.43 * k, orange, (1, 1, 0.42))
        solid("Threshold step", [(-0.96, -1.04), (0.96, -1.04), (0.96, -0.81), (-0.96, -0.81)],
              0.32, 0.18, silver, 0.035)
        if not compact:
            solid("Step inset", [(-0.74, -0.93), (0.74, -0.93), (0.74, -0.88), (-0.74, -0.88)],
                  0.505, 0.01, dark, 0.007)
    elif name == "antu-instalador":
        width = 0.24 if micro else 0.20
        pts = [(-width, 1.12), (width, 1.12), (width, 0.13), (0.69, 0.13),
               (0, -0.59), (-0.69, 0.13), (-width, 0.13)]
        solid("Installation monolith", [(x * k, y * k) for x, y in pts], 0.38, 0.23, silver, 0.045)
        solid("Obsidian installation bay", [(-1.04, -1.02), (1.04, -1.02), (1.04, -0.64), (-1.04, -0.64)],
              0.30, 0.23, edge, 0.085)
        curve("Lava landing", [(-0.78, -0.79, 0.555), (0.78, -0.79, 0.555)],
              0.075 if micro else 0.045, orange)
    elif name == "antu-eclipse":
        sphere("Lava photosphere", (0.10, 0.04, 0.51), 1.0 * k, orange, (1, 1, 0.24))
        sphere("Obsidian occultation", (-0.17 * k, 0.15 * k, 0.66), 0.91 * k, dark, (1, 1, 0.32))
        if not compact:
            pts = [(-0.17 + 0.90 * math.cos(a), 0.15 + 0.90 * math.sin(a), 0.69)
                   for a in np.linspace(0.3, 2.4, 80)]
            curve("Hairline silver limb", pts, 0.008, silver)
    elif name == "antu-ia":
        # A local optical core, not the stock microchip/circuit-board motif.
        sphere("Local lava core", (0, 0, 0.56), (0.48 if micro else 0.37) * k, orange, (1, 1, 0.65))
        for a in ([0, 2.094, 4.189] if micro else [0.28, 2.374, 4.468]):
            x, y = 0.89 * math.sin(a) * k, 0.89 * math.cos(a) * k
            sphere("Silver optical node", (x, y, 0.49), (0.25 if micro else 0.20) * k, silver, (1, 1, 0.65))
        if not micro:
            pts = [(math.cos(a) * 0.90 * k, math.sin(a) * 0.90 * k, 0.40)
                   for a in np.linspace(0, 2 * math.pi, 160, endpoint=False)]
            curve("Machined optical orbit", pts, 0.055 if compact else 0.035, silver, True)
    elif name == "antu-biblioteca":
        # Three original cartridges; the selected one is physically pulled forward.
        cartridge = material("Optical cartridge case", (0.24, 0.25, 0.27, 1), 0.3, 0.38) if micro else edge
        for index, y in enumerate((-0.72, -0.04, 0.64)):
            selected = index == 1
            x, z = (0.18, 0.64) if selected else (-0.12, 0.34)
            w, h = 0.91, 0.275
            notch = 0 if micro else 0.12
            outline = [(-w, -h), (w, -h), (w, h-notch),
                       (w-notch, h), (-w+notch, h), (-w, h-notch)]
            solid("Selected cartridge" if selected else "Stored cartridge",
                  [((px+x)*k, (py+y)*k) for px, py in outline], z, 0.22, cartridge, 0.035)
            label_w = 0.64 if selected else 0.59
            label_h = 0.17 if micro else 0.15
            if selected or not micro:
                solid("Lava review label" if selected else "Blank cartridge label",
                      [((x+px)*k, (y+py)*k) for px, py in
                       [(-label_w, -label_h), (label_w, -label_h),
                        (label_w, label_h), (-label_w, label_h)]],
                      z+0.222, 0.028, orange if selected else body, 0.018)
            if not compact:
                # Connector recess and grip cuts disappear in the optical variants.
                solid("Connector recess", [((x+px)*k, (y+py)*k) for px, py in
                      [(-0.37, -0.278), (0.37, -0.278), (0.37, -0.22), (-0.37, -0.22)]],
                      z+0.205, 0.025, dark, 0.008)
                for side in (-1, 1):
                    curve("Cartridge grip", [((x+side*0.77)*k, (y-0.11)*k, z+0.224),
                                             ((x+side*0.77)*k, (y+0.10)*k, z+0.224)],
                          0.012, silver)
    elif name == "antu-observatorio":
        # Architectural dome seen front-on: two thick shells leave a real open slit.
        # The hemisphere is built around Y so the shared family camera stays fixed.
        radius, gap, cy, cz = 1.03, (0.18 if micro else 0.13), -0.27, 0.43
        dome_mat = material("Obsidian dome shell", (0.10, 0.105, 0.12, 1), 0.3, 0.36)
        for side in (-1, 1):
            verts, faces = [], []
            rows, cols = 48, 48
            for i in range(rows+1):
                a = math.asin(gap/radius) + (math.pi/2-math.asin(gap/radius))*i/rows
                x, r = side*radius*math.sin(a), radius*math.cos(a)
                for j in range(cols+1):
                    b = math.pi*j/(2*cols)
                    verts.append((x*k, (cy+r*math.cos(b))*k, cz+r*math.sin(b)))
            for i in range(rows):
                for j in range(cols):
                    q = i*(cols+1)+j
                    face = (q, q+1, q+cols+2, q+cols+1)
                    faces.append(face if side == -1 else tuple(reversed(face)))
            shell = mesh("Open dome shutter", verts, faces, dome_mat)
            wall = shell.modifiers.new("Obsidian shell thickness", "SOLIDIFY")
            wall.thickness = 0.075
            # Narrow cut faces reveal thickness without a chrome outline.
            r = math.sqrt(radius*radius-gap*gap)
            lip = [(side*gap*k, (cy+r*math.cos(b))*k, cz+r*math.sin(b))
                   for b in np.linspace(0, math.pi/2, 64)]
            curve("Slit cut edge", lip, 0.018 if micro else 0.012, edge)
        # Low cylindrical drum, with the rotation joint omitted at small sizes.
        drum = cylinder("Observatory drum", (0, -0.63*k, 0.46), 1.025*k, 0.68*k, dome_mat if micro else edge)
        drum.rotation_euler.x = math.pi/2
        drum.scale.y = 0.38
        if not compact:
            joint = cylinder("Dome rotation joint", (0, -0.285*k, 0.46), 1.055*k, 0.065, body)
            joint.rotation_euler.x = math.pi/2
            joint.scale.y = 0.38
        # A single lava beam, emerging from the dark opening into the sky.
        beam = material("Lava guide light", LAVA, 0.05, 0.4, 0.65)
        curve("Lava beam to the sky", [(0, 0.06*k, 1.48), (0.42*k, 1.40*k, 0.64)],
              (0.075 if target == 16 else 0.060 if micro else 0.025)*k, beam)
    camera((0, -0.48, 12), (0, 0, 0), ortho=4.25 if compact else 4.35)
    area("Key / softbox northwest", (-3.5, 4.8, 6), (0, 0, 0), 520, 4, (0.93, 0.96, 1), 5)
    area("Narrow silver rim", (4, 1.5, 4), (0, 0, 0), 250, 1.4, (1, 0.94, 0.88), 5)
    area("Gentle front fill", (0, -4, 6), (0, 0, 0), 70, 5)
    return n


def render_icons(preview=False, only=None, sizes=None):
    targets = sizes or ([4096] if preview else [4096, 1024, 512, 256, 128, 64, 48, 32, 24, 16])
    for name in ([only] if only else ICON_NAMES):
        for size in targets:
            icon_scene(name, size, preview)
            path = PREVIEWS / "drafts" / f"{name}.png" if preview else MASTERS / "icons" / name / f"{size}.png"
            save(path)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("job", choices=("icons",))
    p.add_argument("--preview", action="store_true")
    p.add_argument("--only", choices=ICON_NAMES)
    p.add_argument("--sizes", default="")
    a = p.parse_args(argv)
    sizes = [int(x) for x in a.sizes.split(",")] if a.sizes else None
    if sizes and any(x not in (16, 24, 32, 48, 64, 128, 256, 512, 1024, 4096) for x in sizes):
        p.error("Unsupported optical size")
    render_icons(a.preview, a.only, sizes)
