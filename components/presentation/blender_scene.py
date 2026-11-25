"""Run through working_render.py; all scene geometry comes from current STLs."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector, Vector


def material(**kwargs):
    name = kwargs.get("name", "PLA")
    swatch = kwargs.get("swatch", "00B1B7")
    roughness = kwargs.get("roughness", 0.4)
    emission = kwargs.get("emission", False)

    rgb = [int(swatch[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*linear, 1)
    shader.inputs["Roughness"].default_value = roughness
    if emission:
        shader.inputs["Emission Color"].default_value = (*linear, 1)
        shader.inputs["Emission Strength"].default_value = 1
    return mat


def load_mesh(**kwargs):
    path = kwargs["path"]
    mat = kwargs["mat"]
    name = kwargs.get("name", Path(path).stem)

    bpy.ops.wm.stl_import(filepath=str(path))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    obj.data.set_sharp_from_angle(angle=math.radians(35))
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    return data


def make_scene(**kwargs):
    name = kwargs["name"]
    items = kwargs["items"]
    output = Path(kwargs["output"])
    job = kwargs["job"]
    heading = kwargs.get("heading", "JT-500 holder")
    direction = Vector(kwargs.get("direction", [1, -1, 0.85])).normalized()
    target_override = kwargs.get("target_override", None)
    scale_override = kwargs.get("scale_override", None)
    save_scene = kwargs.get("save_scene", True)
    captions = kwargs.get("captions", True)
    show_floor = kwargs.get("show_floor", True)

    scene = bpy.data.scenes.new(name)
    bpy.context.window.scene = scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = job["samples"]
    scene.cycles.use_denoising = True
    scene.cycles.device = job["device"]
    scene.cycles.seed = 19
    scene.render.resolution_x = job["resolution"]
    scene.render.resolution_y = job["resolution"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = not show_floor
    scene.render.image_settings.color_mode = "RGBA" if not show_floor else "RGB"
    scene.render.filepath = str(output)
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.1  # 1 Blender unit = 100 mm.
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world = bpy.data.worlds.new(name + " warm studio")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.85, 0.87, 0.9, 1)
    background.inputs["Strength"].default_value = 0.45
    objects, points = [], []
    for label, mesh, transform in items:
        obj = bpy.data.objects.new(label, mesh)
        scene.collection.objects.link(obj)
        obj.matrix_world = Matrix.Scale(0.01, 4) @ transform
        objects.append(obj)
        points.extend([obj.matrix_world @ v.co for v in mesh.vertices])
    minimum = Vector([min(p[i] for p in points) for i in range(3)])
    maximum = Vector([max(p[i] for p in points) for i in range(3)])
    target = (minimum + maximum) / 2
    rotation = (-direction).to_track_quat("-Z", "Y")
    right, up = rotation @ Vector((1, 0, 0)), rotation @ Vector((0, 1, 0))
    us, vs = [p.dot(right) for p in points], [p.dot(up) for p in points]
    target += right * ((max(us) + min(us)) / 2 - target.dot(right))
    target += up * ((max(vs) + min(vs)) / 2 - target.dot(up))
    scale = max(max(us) - min(us), max(vs) - min(vs)) * 1.28
    if target_override is not None:
        target = Vector(target_override) * 0.01
    if scale_override is not None:
        scale = scale_override * 0.01
    cam = bpy.data.objects.new(name + " orthographic camera", bpy.data.cameras.new(name + " lens"))
    scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = scale
    cam.data.clip_start, cam.data.clip_end = 0.001, 100
    cam.location = target + direction * 7
    cam.rotation_euler = rotation.to_euler()
    scene.camera = cam

    # CAD meshes remain unchanged: no cosmetic bevel that hides thin walls.
    floor_mesh = bpy.data.meshes.new(name + " floor")
    floor_mesh.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 200, 0), (-200, 200, 0)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new(name + " floor", floor_mesh)
    scene.collection.objects.link(floor)
    floor.location.z = minimum.z - 0.003
    floor.hide_render = not show_floor
    floor.data.materials.append(bpy.data.materials["Warm white background"])
    for index, (offset, energy, size) in enumerate([
        ((-3, -4, 6), 650, 4), ((4, 1, 4), 470, 3), ((-1, 4, 3), 550, 3),
    ]):
        light = bpy.data.objects.new(name + f" softbox {index}", bpy.data.lights.new(name + str(index), "AREA"))
        scene.collection.objects.link(light)
        light.location = target + Vector(offset)
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
        light.data.energy, light.data.shape, light.data.size = energy, "DISK", size
    for body, y, size in ([
        (heading, 0.465, 0.025),
        ("AI-generated CAD illustration. Errors possible.", -0.475, 0.018),
    ] if captions else []):
        curve = bpy.data.curves.new(name + body, "FONT")
        curve.body, curve.size, curve.align_x = body, scale * size, "CENTER"
        text = bpy.data.objects.new(name + body, curve)
        scene.collection.objects.link(text)
        text.rotation_euler = rotation.to_euler()
        text.location = cam.location + rotation @ Vector((0, scale * y, -1))
        text.data.materials.append(bpy.data.materials["Caption ink"])
    scene["source_sha256"] = json.dumps(job["source_hashes"])
    scene["physical_validation"] = "Nominal CAD only; no print or real-pump fit claimed"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)
    return {"scene": name, "output": str(output), "objects": [o.name for o in objects],
            "instances": [item[0] for item in items], "camera_scale": scale}


def main(**kwargs):
    job_path = Path(kwargs["job_path"])

    job = json.loads(job_path.read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    prefs = bpy.context.preferences.addons["cycles"].preferences
    job["device"] = "CPU"
    for backend in ["OPTIX", "CUDA", "HIP"]:
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            if any(d.type == backend for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == backend
                job["device"] = "GPU"
                break
        except (TypeError, RuntimeError):
            continue
    teal = material(name="OOBB Turquoise PLA 10605", swatch="00B1B7")
    black = material(name="OOBB Black PLA 10101", swatch="121212")
    grey = material(name="Pump grey moulding", swatch="707A7E", roughness=0.48)
    material(name="Warm white background", swatch="F7F6F2", roughness=0.75)
    material(name="Caption ink", swatch="172E34", emission=True)
    base = load_mesh(path=job["base"], mat=black, name="Common 5x5 base")
    pump = load_mesh(path=job["pump"], mat=grey, name="Nominal JT-500 reference")
    lid = load_mesh(path=job["lid"], mat=black, name="Captive nut lid")
    results = []
    for holder in job["holders"]:
        d = holder["details"]
        shift = d["pump_offset_y"]
        base_top = d["depth"] + d["base_foot_height"]
        base_transform = Matrix.Translation((0, 0, base_top)) @ Matrix.Rotation(math.pi, 4, "X")
        pump_transform = Matrix.Translation((0, shift, base_top))
        top_transform = Matrix.Translation((0, shift - 22, base_top)) @ Matrix.Rotation(-math.pi / 2, 4, "X")
        lid_transform = Matrix.Translation((0, shift, base_top + d["pump_body_length"] + d["top_depth"]))
        orientation = Matrix.Rotation(math.radians(d["pump_rotation_z"]), 4, "Z")
        pump_transform = pump_transform @ orientation
        name = "holder"
        top = load_mesh(path=holder["mesh"], mat=teal, name=name + " two-wall holder")
        items = [("Base", base, base_transform), ("Two-wall holder", top, top_transform), ("Nut cover", lid, lid_transform)]
        heading = "JT-500 holder - M3 x 16 mm countersunk screws"
        results.append(make_scene(name=name + "_assembled", items=items, job=job,
                                  output=Path(holder["assembly_folder"]) / "render_studio.png", heading=heading))
        results.append(make_scene(name="holder_base_retainer", items=[("Base retaining tongues", base, base_transform)], job=job,
                                  direction=[0.5, -0.6, 1.4], output=Path(job["base_folder"]) / "render_retainer.png",
                                  heading="Base retaining tongues - inlet and fin openings remain clear"))
        results.append(make_scene(name="holder_with_pump", items=items + [("Pump", pump, pump_transform)], job=job,
                                  output=Path(holder["assembly_folder"]) / "render_with_pump.png", heading="JT-500 in the two-wall holder"))
        results.append(make_scene(name="holder_side_print", items=[("Top - print position", top, Matrix.Identity(4))], job=job,
                                  direction=[1, -1, 1.4], output=Path(holder["top_folder"]) / "render_side_print.png",
                                  heading="Side-print position - long pump axis horizontal"))
        exploded = [("Base", base, base_transform),
                    ("Pump", pump, Matrix.Translation((0, 0, 30)) @ pump_transform),
                    ("Two-wall holder", top, Matrix.Translation((0, 0, 160)) @ top_transform),
                    ("Nut cover", lid, Matrix.Translation((0, 0, 220)) @ lid_transform)]
        results.append(make_scene(name="holder_exploded", items=exploded, job=job,
                                  output=Path(holder["assembly_folder"]) / "render_exploded.png", heading="Printed parts and pump - exploded along assembly axis"))
        results.append(make_scene(name="holder_nut_detail", items=items, job=job, direction=[1, -0.45, 0.55],
                                  target_override=[24, shift, base_top + 8], scale_override=55,
                                  output=Path(holder["top_folder"]) / "render_nut_detail.png", heading="Local nut tabs - screws enter from below"))
    bpy.context.window.scene = bpy.data.scenes["holder_with_pump"]
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=job["scene_file"])
    result = {"blender_version": bpy.app.version_string, "device": job["device"],
              "source_hashes": job["source_hashes"], "renders": results, "scene_file": job["scene_file"]}
    (job_path.parent / "qa/render_manifest.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main(job_path=sys.argv[sys.argv.index("--") + 1])
