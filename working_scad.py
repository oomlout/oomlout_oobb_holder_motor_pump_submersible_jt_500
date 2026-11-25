import copy
import oobb
import yaml
import os
import scad_help

def main(**kwargs):
    make_scad(**kwargs)

def make_scad(**kwargs):
    typ = scad_help.get_typ(**kwargs)
    oomp_mode = "project"
    #oomp_mode = "oobb"
    filt = ""
    build_variables = scad_help.get_build_variables(typ, filter=filt)
    if True:
        kwargs.setdefault("filter", build_variables["filter"])
        kwargs.setdefault("save_type", build_variables["save_type"])
        kwargs.setdefault("navigation", build_variables["navigation"])
        kwargs.setdefault("overwrite", build_variables["overwrite"])
        kwargs.setdefault("modes", build_variables["modes"])
        kwargs["oomp_mode"] = oomp_mode
        kwargs["oomp_run"] = build_variables["oomp_run"]
    parts = get_parts(kwargs, oomp_mode)
    
    kwargs["parts"] = parts

    scad_help.make_parts(**kwargs)

    if kwargs["navigation"]:
        oobb_style = False  
        sort = scad_help.get_navigation_sort(oobb_style=oobb_style)
        scad_help.generate_navigation(sort=sort)

    if any(part.get("documentation") for part in parts):
        import working_documentation
        working_documentation.write_readmes()

def get_parts(kwargs, oomp_mode):
    import working_cad
    parts = []    

    #load parts from parts/folder/working.yaml
    parts_directory = os.path.join(os.path.dirname(__file__), "parts")
    if not os.path.isdir(parts_directory):
        return parts

    for folder in os.listdir(parts_directory):
        folder_path = os.path.join(parts_directory, folder)
        if not os.path.isdir(folder_path):
            continue

        working_yaml_path = os.path.join(folder_path, "working.yaml")
        if not os.path.isfile(working_yaml_path):
            continue

        with open(working_yaml_path, "r", encoding="utf-8") as infile:
            loaded_part = yaml.safe_load(infile)

        if not isinstance(loaded_part, dict):
            continue

        oobb_details = loaded_part.get("oobb_details")
        if not isinstance(oobb_details, dict):
            continue

        if not working_cad.enabled(oobb_details, "scad"):
            continue
        part = loaded_part

        part_kwargs = copy.deepcopy(kwargs)
        part_kwargs.update(copy.deepcopy(loaded_part.get("kwargs", {})))
        part_kwargs.update(copy.deepcopy(oobb_details))
        for key in ("modes", "save_type", "overwrite", "filter", "navigation", "oomp_run"):
            if key in kwargs:
                part_kwargs[key] = copy.deepcopy(kwargs[key])
        part["kwargs"] = working_cad.geometry_parameters(part_kwargs)
        part["oobb_name"] = part.get("oobb_name", oobb_details.get("oobb_name", oobb_details.get("oobb_type", "default")))

        if oomp_mode == "oobb":
            part["kwargs"]["oomp_size"] = part["oobb_name"]

        parts.append(part)


    return parts

def get_base(thing, **kwargs):

    prepare_print = kwargs.get("prepare_print", False)
    width = kwargs.get("width", 1)
    height = kwargs.get("height", 1)
    depth = kwargs.get("depth", 6)                    
    rot = kwargs.get("rot", [0, 0, 0])
    pos = kwargs.get("pos", [0, 0, 0])
    extra = kwargs.get("extra", "")
    


    #add plate
    if True:
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "positive"
        p3["shape"] = f"oobb_plate"    
        p3["depth"] = depth
        #p3["holes"] = True         uncomment to include default holes
        #p3["m"] = "#"
        pos1 = copy.deepcopy(pos)         
        p3["pos"] = pos1
        oobb.append_full(thing,**p3)
    
    #add holes seperate
    if True:
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "p"
        p3["shape"] = f"oobb_holes"
        p3["both_holes"] = True  
        p3["depth"] = depth
        p3["holes"] = "perimeter"
        #p3["m"] = "#"
        pos1 = copy.deepcopy(pos)         
        p3["pos"] = pos1
        oobb.append_full(thing,**p3)

    #add a test screw_countersunk
    if True:
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "p"
        p3["shape"] = f"screw_countersunk"
        p3["depth"] = depth
        p3["radius_name"] = "m3"
        pos1 = copy.deepcopy(pos)         
        pos1[2] += depth
        p3["pos"] = pos1
        p3["m"] = "#"
        oobb.append_full(thing,**p3)

    if prepare_print:
        scad_help.prepare_base_for_print(thing, pos, **kwargs)

def get_hole_cover(thing, **kwargs):

    prepare_print = kwargs.get("prepare_print", False)
    width = kwargs.get("width", 1)
    height = kwargs.get("height", 1)
    depth = kwargs.get("depth", 6)                    
    rot = kwargs.get("rot", [0, 0, 0])
    pos = kwargs.get("pos", [0, 0, 0])
    extra = kwargs.get("extra", "")
    
    diameter = kwargs.get("diameter", 10)
    clearance = kwargs.get("clearance", 0.5)
    thickness_wall = 2
    depth_taper = 3
    depth_top = 2
    diameter_top_extra = 10
    radius_gap=6
    diameter_top_taper = 5

    #add cylinder
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "positive"
    p3["shape"] = f"oobb_cylinder"    
    dep = depth - depth_taper 
    p3["depth"] = dep
    p3["radius"] = (diameter-clearance)/2
    #p3["m"] = "#"
    pos1 = copy.deepcopy(pos)         
    pos1[2] += depth_taper + dep/2
    p3["pos"] = pos1
    oobb.append_full(thing,**p3)
    
    #add cylinder taper using radius_1 and radius_2
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "positive"
    p3["shape"] = f"oobb_cylinder"
    p3["depth"] = depth_taper
    p3["radius_2"] = (diameter-clearance)/2
    p3["radius_1"] = (diameter+clearance-thickness_wall)/2    
    #p3["m"] = "#"
    pos1 = copy.deepcopy(pos)
    pos1[2] += depth_taper/2
    p3["pos"] = pos1
    oobb.append_full(thing,**p3)

    #add top cylinder
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "positive"
    p3["shape"] = f"oobb_cylinder"
    p3["depth"] = depth_top
    dia = diameter+diameter_top_extra
    p3["radius_2"] = (dia-diameter_top_taper)/2
    p3["radius_1"] = (dia)/2
    #p3["m"] = "#"
    pos1 = copy.deepcopy(pos)
    pos1[2] += depth-depth_top/2
    p3["pos"] = pos1
    oobb.append_full(thing,**p3)

    

    #add hole
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "negative"
    p3["shape"] = f"oobb_cylinder"
    p3["depth"] = depth - depth_top/2
    p3["radius"] = (diameter+clearance-thickness_wall)/2    

    pos1 = copy.deepcopy(pos)
    pos1[2] += depth/2 - depth_top/2
    p3["pos"] = pos1
    #p3["m"] = "#"
    oobb.append_full(thing,**p3)

    
    #diameter_top 30
    #add hole_top
    diameter_top_hole = 30
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "negative"
    p3["shape"] = f"oobb_cylinder"
    p3["depth"] = depth_top
    p3["radius"] = (diameter_top_hole)/2
    pos1 = copy.deepcopy(pos)
    pos1[2] += depth - depth_top/2

    p3["pos"] = pos1
    p3["m"] = "#"
    oobb.append_full(thing,**p3)

    pos1 = copy.deepcopy(pos)
    pos1[1] += 100



    if prepare_print:
        scad_help.prepare_base_for_print(thing, pos, **kwargs)

    
def get_plate(thing, **kwargs):

    prepare_print = kwargs.get("prepare_print", False)
    width = kwargs.get("width", 1)
    height = kwargs.get("height", 1)
    depth = kwargs.get("depth", 6)
    rot = kwargs.get("rot", [0, 0, 0])
    pos = kwargs.get("pos", [0, 0, 0])
    extra = kwargs.get("extra", "")



    #add plate
    if True:
        if width == 1 and height == 1:
            p3 = copy.deepcopy(kwargs)
            p3["type"] = "positive"
            p3["shape"] = f"oobb_plate"
            p3["depth"] = depth
            #p3["holes"] = True         uncomment to include default holes
            #p3["m"] = "#"
            pos1 = copy.deepcopy(pos)
            p3["pos"] = pos1
            oobb.append_full(thing,**p3)
        else:
            p3 = copy.deepcopy(kwargs)
            p3["type"] = "positive"
            p3["shape"] = f"oobb_rounded_rectangle_rounded"
            wid = (width *15)-1
            hei = (height *15)-1
            dep = depth
            size = [wid, hei, dep]
            p3["radius_rounded"] = 1.5
            p3["size"] = size
            #p3["holes"] = True         uncomment to include default holes
            #p3["m"] = "#"
            pos1 = copy.deepcopy(pos)
            p3["pos"] = pos1
            oobb.append_full(thing,**p3)

    #add holes seperate
    if True:
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "p"
        p3["shape"] = f"oobb_holes"
        p3["both_holes"] = True
        p3["depth"] = depth
        p3["holes"] = "all"
        #p3["m"] = "#"
        pos1 = copy.deepcopy(pos)
        p3["pos"] = pos1
        oobb.append_full(thing,**p3)

    if prepare_print:
        scad_help.prepare_base_for_print(thing, pos, **kwargs)


def get_jt500_base_top(**kwargs):
    """Rear-face datum, independent of the pump's fixed fin projection."""
    depth = kwargs.get("depth", 6)
    base_foot_height = kwargs.get("base_foot_height", 2.7)

    if depth <= 0 or base_foot_height <= 0:
        raise ValueError("Base plate and corner feet must have positive thickness")
    return depth + base_foot_height


def get_jt500_print_offsets(**kwargs):
    """Separate the two print-oriented pieces by an editable edge-to-edge gap."""
    width = kwargs.get("width", 5)
    top_width = kwargs.get("top_width", 3)
    tab_outer_x = kwargs.get("tab_outer_x", 28.5)
    pump_body_length = kwargs.get("pump_body_length", 79)
    axial_clearance = kwargs.get("axial_clearance", 0)
    top_depth = kwargs.get("top_depth", 13)
    print_gap = kwargs.get("print_gap", 10)

    if print_gap <= 0:
        raise ValueError("Print layout requires a positive gap between pieces")
    return {
        "base": [-(width * 15 - 1) / 2 - print_gap / 2, 0, 0],
        "top": [max((top_width * 15 - 1) / 2, tab_outer_x) + print_gap / 2,
                (pump_body_length + axial_clearance + top_depth) / 2, 0],
        "lid": [max((top_width * 15 - 1) / 2, tab_outer_x) + print_gap / 2,
                -(pump_body_length + axial_clearance + top_depth) / 2 - print_gap - 22, 0],
    }


def get_holder_motor_pump_submersible_jt_500(thing, **kwargs):
    """Base, clamp and captive-nut lid; rear pump face down and ports up."""
    piece = kwargs.get("piece", "base")
    prepare_print = kwargs.get("prepare_print", True)
    pos = kwargs.get("pos", [0, 0, 0])
    rot = kwargs.get("rot", [0, 0, 0])
    depth = kwargs.get("depth", 6)
    top_depth = kwargs.get("top_depth", 13)
    pump_body_length = kwargs.get("pump_body_length", 79.0)
    base_top = get_jt500_base_top(**kwargs)
    axial_clearance = kwargs.get("axial_clearance", 0)
    pump_offset_y = kwargs.get("pump_offset_y", 15)

    if piece not in ("base", "top", "lid", "assembly", "all"):
        raise ValueError(f"Unknown JT-500 holder piece: {piece}")
    roof_z = pump_body_length + axial_clearance
    local = copy.deepcopy(kwargs)
    local["pos"] = [0, 0, 0]
    local["rot"] = [0, 0, 0]
    local["overhang"] = True
    components = []
    offsets = get_jt500_print_offsets(**kwargs) if piece == "all" and prepare_print else {"base": [0, 0, 0], "top": [0, 0, 0], "lid": [0, 0, 0]}
    if piece in ("base", "assembly", "all"):
        base = {"components": [], "components_objects": [], "components_string": []}
        get_jt500_base(base, **local)
        components.append({
            "type": "rotation",
            "typetype": "positive",
            "pos": [offsets["base"][0], offsets["base"][1], base_top] if prepare_print and piece in ("base", "all") else [0, 0, 0],
            "rot": [180, 0, 0] if prepare_print and piece in ("base", "all") else [0, 0, 0],
            "objects": base["components"],
        })
    if piece in ("top", "assembly", "all"):
        top = {"components": [], "components_objects": [], "components_string": []}
        get_jt500_top(top, **local)
        # Lay the open -Y side on the bed: only the two side walls remain.
        # The long pump axis now lies horizontally on the print bed.
        top_rot = [90, 0, 0] if prepare_print and piece in ("top", "all") else [0, 0, 0]
        top_z = (kwargs.get("top_height", 3) * 15 - 1) / 2 if prepare_print and piece in ("top", "all") else 0
        if piece == "assembly" or (piece == "all" and not prepare_print):
            top_z = base_top
        top_y = offsets["top"][1] + (pump_offset_y if piece == "assembly" or (piece == "all" and not prepare_print) else 0)
        components.append({
            "type": "rotation",
            "typetype": "positive",
            "pos": [offsets["top"][0], top_y, top_z],
            "rot": top_rot,
            "objects": top["components"],
        })
    if piece in ("lid", "assembly", "all"):
        lid = {"components": [], "components_objects": [], "components_string": []}
        get_jt500_lid(lid, **local)
        assembled = piece == "assembly" or (piece == "all" and not prepare_print)
        components.append({
            "type": "rotation", "typetype": "positive",
            "pos": [0, pump_offset_y, base_top + roof_z + top_depth] if assembled else offsets["lid"],
            "rot": [0, 0, 0], "objects": lid["components"],
        })
    thing["components"].append({
        "type": "rotation",
        "typetype": "positive",
        "pos": copy.deepcopy(pos),
        "rot": copy.deepcopy(rot),
        "objects": components,
    })


def get_jt500_grid(thing, **kwargs):
    """Complete M6 grid and interstitial M3 grid, with finite cutter depths.

    The library's `oobb_holes/all` currently drops depth on array expansion.
    Individual OOBB holes avoid cutting through unrelated supports or parts.
    An optional footprint omits bores covered by the clamp housing.
    """
    width = kwargs.get("width", 5)
    height = kwargs.get("height", 5)
    depth = kwargs.get("depth", 6)
    pos = kwargs.get("pos", [0, 0, 0])
    pitch = kwargs.get("pitch", 15)
    side_print_relief = kwargs.get("side_print_relief", False)
    grid_exclusion = kwargs.get("grid_exclusion", None)

    for ix in range(2 * width - 1):
        for iy in range(2 * height - 1):
            p3 = copy.deepcopy(kwargs)
            p3["type"] = "negative"
            p3["shape"] = "oobb_hole"
            p3["radius_name"] = "m6" if ix % 2 == 0 and iy % 2 == 0 else "m3"
            p3["depth"] = depth
            p3["pos"] = [
                pos[0] + (ix - width + 1) * pitch / 2,
                pos[1] + (iy - height + 1) * pitch / 2,
                pos[2],
            ]
            if grid_exclusion is not None:
                from shapely.geometry import Point
                radius = max(oobb.gv("hole_radius_" + p3["radius_name"], mode)
                             for mode in ["true", "3dpr", "laser"])
                if grid_exclusion.distance(Point(*p3["pos"][:2])) <= radius:
                    continue
            p3.pop("grid_exclusion", None)
            oobb.append_full(thing, **p3)
            if side_print_relief:
                get_jt500_hole_roof(thing, **p3)


def get_jt500_hole_roof(thing, **kwargs):
    """45-degree upper relief for a bore printed horizontally on the -Y side."""
    pos = kwargs.get("pos", [0, 0, 0])
    depth = kwargs.get("depth", 6)
    radius_name = kwargs.get("radius_name", "")
    radius = kwargs.get("radius", 3)

    import math
    for mode in ["true", "3dpr", "laser"]:
        r = oobb.gv("hole_radius_" + radius_name, mode) if radius_name else radius
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "negative"
        p3["shape"] = "polygon"
        p3["inclusion"] = mode
        p3["points"] = [[-r / math.sqrt(2), r / math.sqrt(2)],
                        [r / math.sqrt(2), r / math.sqrt(2)],
                        [0, r * math.sqrt(2)]]
        p3["height"] = depth
        p3["pos"] = list(pos)
        oobb.append_full(thing, **p3)


def get_jt500_outline(**kwargs):
    """Reference end profile with a true planar offset, not a scaled box."""
    pump_body_width = kwargs.get("pump_body_width", 33.43)
    pump_body_height = kwargs.get("pump_body_height", 38.33)
    outline_offset = kwargs.get("outline_offset", 3)
    outline_segments = kwargs.get("outline_segments", 32)
    pump_rotation_z = kwargs.get("pump_rotation_z", 0)

    import math
    from shapely.geometry import Polygon
    from shapely.affinity import rotate

    radius = pump_body_width / 2
    circle_y = pump_body_height / 2 - radius
    points = []
    for index in range(outline_segments + 1):
        angle = math.pi * index / outline_segments
        points.append([radius * math.cos(angle), circle_y + radius * math.sin(angle)])
    # Same nominal profile as the catalogue model; unlabelled curves are
    # approximated from the dimension drawing, not measured on a real pump.
    points.extend([
        [-radius, circle_y - 2],
        [-radius * 0.86, -pump_body_height * 0.35],
        [-radius * 0.72, -pump_body_height * 0.46],
        [-radius * 0.48, -pump_body_height / 2],
        [radius * 0.48, -pump_body_height / 2],
        [radius * 0.72, -pump_body_height * 0.46],
        [radius * 0.86, -pump_body_height * 0.35],
        [radius, circle_y - 2],
    ])
    profile = Polygon(points).buffer(outline_offset, quad_segs=16, join_style="round")
    # The same cavity and water windows must accept either end-for-end
    # orientation about the vertical pump axis.
    profile = profile.union(rotate(profile, 180, origin=(0, 0)))
    profile = rotate(profile, pump_rotation_z, origin=(0, 0))
    if profile.is_empty or profile.geom_type != "Polygon":
        raise ValueError("Pump outline offset must leave one nonempty profile")
    return [list(point) for point in list(profile.exterior.coords)[:-1]]


def get_jt500_tab_profile(**kwargs):
    """Shared outline for the nut tabs and their base-hole exclusion."""
    top_width = kwargs.get("top_width", 3)
    top_height = kwargs.get("top_height", 3)
    tab_outer_x = kwargs.get("tab_outer_x", 28.5)
    tab_inner_x = kwargs.get("tab_inner_x", 18)
    tab_corner_radius = kwargs.get("tab_corner_radius", 1)
    width = kwargs.get("width", 5)
    height = kwargs.get("height", 5)
    pump_offset_y = kwargs.get("pump_offset_y", 15)
    corner_clearance_diameter = kwargs.get("corner_clearance_diameter", 15)

    from math import cos, pi
    from shapely.geometry import Point, Polygon
    half_width = (top_width * 15 - 1) / 2
    half_height = (top_height * 15 - 1) / 2
    tab = Polygon([
        [tab_inner_x, -half_height],
        [half_width, -half_height],
        [tab_outer_x, -half_height + tab_outer_x - half_width],
        [tab_outer_x, half_height - 4],
        [tab_outer_x - 4, half_height],
        [tab_inner_x, half_height],
    ]).buffer(-tab_corner_radius).buffer(tab_corner_radius, quad_segs=12)
    # Model the right tab once. Its mirror supplies the left corner relief.
    corner = Point((width - 1) * 7.5, (height - 1) * 7.5 - pump_offset_y)
    # Circumscribe the clearance circle so even the polygon flats clear it.
    radius = corner_clearance_diameter / 2 / cos(pi / 256)
    return tab.difference(corner.buffer(radius, quad_segs=64))


def get_jt500_clamp_footprint(**kwargs):
    """Plan projection of the rounded 3x3 housing and both local nut tabs."""
    top_width = kwargs.get("top_width", 3)
    top_height = kwargs.get("top_height", 3)
    corner_radius = kwargs.get("clamp_corner_radius", 5)

    from shapely.geometry import box
    from shapely.affinity import scale
    half_width = (top_width * 15 - 1) / 2
    half_height = (top_height * 15 - 1) / 2
    column = box(-half_width + corner_radius, -half_height + corner_radius,
                 half_width - corner_radius, half_height - corner_radius).buffer(corner_radius)
    tab = get_jt500_tab_profile(**kwargs)
    return column.union(tab).union(scale(tab, xfact=-1, origin=(0, 0)))


def get_jt500_base(thing, **kwargs):
    """Rear-face retaining tongues, open water paths and four corner feet."""
    width = kwargs.get("width", 5)
    height = kwargs.get("height", 5)
    depth = kwargs.get("depth", 6)
    base_foot_height = kwargs.get("base_foot_height", 2.7)
    base_window_clearance = kwargs.get("base_window_clearance", 1)
    retainer_span = kwargs.get("retainer_span", 40)
    retainer_width = kwargs.get("retainer_width", 4)
    retainer_relief_diameter = kwargs.get("retainer_relief_diameter", 16)
    pump_body_width = kwargs.get("pump_body_width", 33.43)
    foot_pitch = kwargs.get("foot_pitch", 60)
    foot_size = kwargs.get("foot_size", 12)
    foot_radius = kwargs.get("foot_radius", 4)
    mount_x = kwargs.get("mount_x", 22.5)
    mount_y = kwargs.get("mount_y", 7.5)
    screw_radius_name = kwargs.get("screw_radius_name", "m3")
    screw_length = kwargs.get("screw_length", 16)
    omit_covered_base_holes = kwargs.get("omit_covered_base_holes", True)
    pump_offset_y = kwargs.get("pump_offset_y", 15)

    foot_height = base_foot_height
    base_top = get_jt500_base_top(**kwargs)
    if retainer_span <= pump_body_width or retainer_width <= 0:
        raise ValueError("Retaining tongues must join the base on both sides")
    if retainer_relief_diameter <= retainer_width:
        raise ValueError("Centre relief must separate the retaining tongues without a pinched web")
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "positive"
    p3["shape"] = "oobb_plate"
    p3["width"] = width
    p3["height"] = height
    p3["depth"] = depth
    p3["holes"] = False
    p3["pos"] = [0, 0, foot_height]
    oobb.append_full(thing, **p3)

    # The pump rests on the plate top. Independent feet keep water access
    # underneath when plate thickness exceeds the fixed fin projection.
    for x in [-foot_pitch / 2, foot_pitch / 2]:
        for y in [-foot_pitch / 2, foot_pitch / 2]:
            p3 = copy.deepcopy(kwargs)
            p3["type"] = "positive"
            p3["shape"] = "rounded_rectangle"
            p3["size"] = [foot_size, foot_size, foot_height + 0.1]
            p3["r"] = foot_radius
            p3["pos"] = [x, y, 0]
            oobb.append_full(thing, **p3)

    # Two opposing ledges reach under the solid strip between the intake
    # openings. Keep the central projection and either fin pattern clear.
    from shapely.geometry import Point, Polygon, box
    p3 = copy.deepcopy(kwargs)
    p3["outline_offset"] = base_window_clearance
    outline = Polygon(get_jt500_outline(**p3))
    band = box(-retainer_span / 2, -retainer_width / 2,
               retainer_span / 2, retainer_width / 2)
    relief = Point(0, 0).buffer(retainer_relief_diameter / 2, quad_segs=32)
    openings = outline.difference(band).union(relief)
    from shapely.affinity import translate
    openings = translate(openings, yoff=pump_offset_y)
    polygons = list(openings.geoms) if openings.geom_type == "MultiPolygon" else [openings]
    for opening in polygons:
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "negative"
        p3["shape"] = "polygon"
        p3["points"] = [list(point) for point in list(opening.exterior.coords)[:-1]]
        p3["height"] = base_top + 2
        p3["pos"] = [0, 0, -1]
        oobb.append_full(thing, **p3)

    p3 = copy.deepcopy(kwargs)
    p3["width"] = width
    p3["height"] = height
    p3["depth"] = base_top + 2
    p3["pos"] = [0, 0, -1]
    p3["side_print_relief"] = False
    if omit_covered_base_holes:
        p3["grid_exclusion"] = translate(get_jt500_clamp_footprint(**kwargs), yoff=pump_offset_y)
    get_jt500_grid(thing, **p3)

    for x in [-mount_x, mount_x]:
        for y in [-mount_y, mount_y]:
            p3 = copy.deepcopy(kwargs)
            p3["type"] = "negative"
            p3["shape"] = "oobb_screw_countersunk"
            p3["radius_name"] = screw_radius_name
            p3["depth"] = screw_length
            p3["zz"] = "top"
            p3["rot"] = [180, 0, 0]
            p3["pos"] = [x, y + pump_offset_y, foot_height]
            p3["nut_include"] = False
            p3["overhang"] = True
            oobb.append_full(thing, **p3)



def get_jt500_top(thing, **kwargs):
    """Subtract the pump from a 3x3 column, open two faces, add local nut tabs."""
    top_width = kwargs.get("top_width", 3)
    top_height = kwargs.get("top_height", 3)
    top_depth = kwargs.get("top_depth", 13)
    depth = kwargs.get("depth", 6)
    clamp_corner_radius = kwargs.get("clamp_corner_radius", 5)
    pump_body_length = kwargs.get("pump_body_length", 79)
    pump_outline_clearance = kwargs.get("pump_outline_clearance", 3)
    axial_clearance = kwargs.get("axial_clearance", 0)
    pump_outlet_xy = kwargs.get("pump_outlet_xy", [0, 9])
    pump_wire_xy = kwargs.get("pump_wire_xy", [0, -9])
    outlet_clearance_diameter = kwargs.get("outlet_clearance_diameter", 15.5)
    wire_clearance_diameter = kwargs.get("wire_clearance_diameter", 15.5)
    open_width = kwargs.get("open_width", 28)
    tab_height = kwargs.get("tab_height", 14)
    tab_outer_x = kwargs.get("tab_outer_x", 28.5)
    tab_inner_x = kwargs.get("tab_inner_x", 18)
    tab_corner_radius = kwargs.get("tab_corner_radius", 1)
    mount_x = kwargs.get("mount_x", 22.5)
    mount_y = kwargs.get("mount_y", 7.5)
    screw_radius_name = kwargs.get("screw_radius_name", "m3")
    screw_length = kwargs.get("screw_length", 16)
    nut_height_from_foot = kwargs.get("nut_height_from_foot", 6)
    screw_tip_clearance = kwargs.get("screw_tip_clearance", 2)
    side_print_relief = kwargs.get("side_print_relief", False)

    roof_z = pump_body_length + axial_clearance
    column_width = top_width * 15 - 1
    column_height = top_height * 15 - 1
    if not 0 < open_width < column_width:
        raise ValueError("Front/back openings must leave two side walls")
    if screw_length <= depth + nut_height_from_foot + oobb.gv("nut_depth_" + screw_radius_name, "3dpr"):
        raise ValueError("Screw must engage the complete nut")

    p3 = copy.deepcopy(kwargs)
    p3["type"] = "positive"
    p3["shape"] = "oobb_plate"
    p3["width"] = top_width
    p3["height"] = top_height
    p3["depth"] = roof_z + top_depth
    p3["r"] = clamp_corner_radius
    p3["holes"] = False
    p3["pos"] = [0, 0, 0]
    oobb.append_full(thing, **p3)


    # Two short mounting rails carry the nuts. Their bed-facing outer edges
    # grow at 45 degrees, supporting the local flare when printed on -Y.
    tab_profile = get_jt500_tab_profile(**kwargs)
    for sign in [-1, 1]:
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "positive"
        p3["shape"] = "polygon"
        p3["points"] = [[sign * x, y] for x, y in list(tab_profile.exterior.coords)[:-1]]
        p3["height"] = tab_height
        p3["pos"] = [0, 0, 0]
        oobb.append_full(thing, **p3)

    p3 = copy.deepcopy(kwargs)
    p3["type"] = "negative"
    p3["shape"] = "polygon"
    p3["outline_offset"] = pump_outline_clearance
    p3["points"] = get_jt500_outline(**p3)
    p3["height"] = roof_z + 1
    p3["pos"] = [0, 0, -1]
    oobb.append_full(thing, **p3)

    # Remove the front and back webs below the top plate. This also removes
    # the closed arch that would otherwise bridge across the pump when side-printed.
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "negative"
    p3["shape"] = "oobb_cube"
    p3["size"] = [open_width, column_height + 2, roof_z + 1]
    p3["pos"] = [0, 0, -1]
    oobb.append_full(thing, **p3)

    for x in [-mount_x, mount_x]:
        for y in [-mount_y, mount_y]:
            p3 = copy.deepcopy(kwargs)
            p3["type"] = "negative"
            p3["shape"] = "oobb_hole"
            p3["radius_name"] = screw_radius_name
            p3["depth"] = screw_length - depth + screw_tip_clearance + 1
            p3["pos"] = [x, y, -1]
            oobb.append_full(thing, **p3)

            # Separate modes ensure the nut's library print allowance is kept.
            # OOBB 'left' opens toward +X and 'right' toward -X.
            for mode in ["true", "3dpr", "laser"]:
                p3 = copy.deepcopy(kwargs)
                p3["type"] = "negative"
                p3["shape"] = "oobb_nut"
                p3["radius_name"] = screw_radius_name
                p3["depth"] = oobb.gv("nut_depth_" + screw_radius_name, mode)
                p3["mode"] = mode
                p3["zz"] = "bottom"
                p3["clearance"] = "left" if x > 0 else "right"
                p3["pos"] = [x, y, nut_height_from_foot]
                p3["overhang"] = True
                p3["hole"] = False
                oobb.append_full(thing, **p3)

    get_jt500_top_nut_pockets(thing, **kwargs)

    for xy, diameter in [
        (pump_outlet_xy, outlet_clearance_diameter),
        (pump_wire_xy, wire_clearance_diameter),
    ]:
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "negative"
        p3["shape"] = "oobb_hole"
        p3["radius_name"] = ""
        p3["radius"] = diameter / 2
        p3["depth"] = top_depth + 2
        p3["pos"] = [xy[0], xy[1], roof_z - 1]
        oobb.append_full(thing, **p3)
        if side_print_relief:
            get_jt500_hole_roof(thing, **p3)


def get_jt500_attachment_nuts(**kwargs):
    attachment_nuts = kwargs.get("attachment_nuts", [
        {"radius_name": "m6", "pos": [-15, -15]},
        {"radius_name": "m6", "pos": [-15, 0]},
        {"radius_name": "m6", "pos": [-15, 15]},
        {"radius_name": "m6", "pos": [15, -15]},
        {"radius_name": "m6", "pos": [15, 0]},
        {"radius_name": "m6", "pos": [15, 15]},
    ])
    return copy.deepcopy(attachment_nuts)


def get_jt500_top_nut_pockets(thing, **kwargs):
    pump_body_length = kwargs.get("pump_body_length", 79)
    axial_clearance = kwargs.get("axial_clearance", 0)
    top_depth = kwargs.get("top_depth", 13)
    lid_mount_positions = kwargs.get("lid_mount_positions", [[-16.5, 7.5], [16.5, -7.5]])
    lid_depth = kwargs.get("lid_depth", 3)
    lid_screw_length = kwargs.get("lid_screw_length", 16)
    lid_nut_bottom = kwargs.get("lid_nut_bottom", 2)

    roof_z = pump_body_length + axial_clearance
    entries = get_jt500_attachment_nuts(**kwargs)
    for entry in entries:
        size, xy = entry["radius_name"], entry["pos"]
        pocket_depth = oobb.gv("nut_depth_" + size, "3dpr")
        if top_depth - pocket_depth < 2:
            raise ValueError("Attachment nut pockets require at least 2 mm of supporting floor")
        for mode in ["true", "3dpr", "laser"]:
            p3 = copy.deepcopy(kwargs)
            p3.update(type="negative", shape="oobb_nut", radius_name=size,
                      pos=[*xy, roof_z + top_depth - pocket_depth],
                      depth=pocket_depth + .1, mode=mode, zz="bottom", clearance="",
                      overhang=True, hole=False)
            oobb.append_full(thing, **p3)
    # Fixing nuts sit BELOW a load-bearing shoulder, separately from the six
    # upward-loading M6 pockets. Side slots let them be loaded after the pump.
    fixing_depth = oobb.gv("nut_depth_m3", "3dpr")
    m6_floor = top_depth - oobb.gv("nut_depth_m6", "3dpr")
    if m6_floor - (lid_nut_bottom + fixing_depth) < 2:
        raise ValueError("Leave 2 mm between the lower fixing nuts and M6 pockets")
    screw_tip = top_depth + lid_depth - lid_screw_length
    if not 0 <= screw_tip <= lid_nut_bottom:
        raise ValueError("Cover screws must pass through the fixing nut without entering the pump")
    for xy in lid_mount_positions:
        for mode in ["true", "3dpr", "laser"]:
            p3 = copy.deepcopy(kwargs)
            p3.update(type="negative", shape="oobb_nut", radius_name="m3",
                      pos=[*xy, roof_z + lid_nut_bottom], depth=fixing_depth,
                      mode=mode, zz="bottom", clearance="right" if xy[0] < 0 else "left",
                      overhang=True, hole=False)
            oobb.append_full(thing, **p3)
    entries += [{"radius_name": "m3", "pos": xy} for xy in lid_mount_positions]
    for entry in entries:
        p3 = copy.deepcopy(kwargs)
        p3.update(type="negative", shape="oobb_hole", radius_name=entry["radius_name"],
                  pos=[*entry["pos"], roof_z - 1], depth=top_depth + 2)
        oobb.append_full(thing, **p3)


def get_jt500_lid(thing, **kwargs):
    top_width = kwargs.get("top_width", 3)
    top_height = kwargs.get("top_height", 3)
    lid_depth = kwargs.get("lid_depth", 3)
    lid_mount_positions = kwargs.get("lid_mount_positions", [[-16.5, 7.5], [16.5, -7.5]])
    lid_screw_length = kwargs.get("lid_screw_length", 16)
    pump_outlet_xy = kwargs.get("pump_outlet_xy", [0, 9])
    pump_wire_xy = kwargs.get("pump_wire_xy", [0, -9])
    outlet_clearance_diameter = kwargs.get("outlet_clearance_diameter", 15.5)
    wire_clearance_diameter = kwargs.get("wire_clearance_diameter", 15.5)

    p3 = copy.deepcopy(kwargs)
    p3.update(type="positive", shape="oobb_plate", width=top_width, height=top_height,
              depth=lid_depth, holes=False, pos=[0, 0, 0])
    oobb.append_full(thing, **p3)
    for entry in get_jt500_attachment_nuts(**kwargs):
        p3 = copy.deepcopy(kwargs)
        p3.update(type="negative", shape="oobb_hole", radius_name=entry["radius_name"],
                  pos=[*entry["pos"], -1], depth=lid_depth + 2)
        oobb.append_full(thing, **p3)
    for xy, diameter in [(pump_outlet_xy, outlet_clearance_diameter), (pump_wire_xy, wire_clearance_diameter)]:
        p3 = copy.deepcopy(kwargs)
        p3.update(type="negative", shape="oobb_hole", radius_name="", radius=diameter / 2,
                  pos=[*xy, -1], depth=lid_depth + 2)
        oobb.append_full(thing, **p3)
    for xy in lid_mount_positions:
        p3 = copy.deepcopy(kwargs)
        p3.update(type="negative", shape="oobb_screw_countersunk", radius_name="m3",
                  pos=[*xy, lid_depth], depth=lid_screw_length, zz="top",
                  nut_include=False, overhang=True)
        oobb.append_full(thing, **p3)


if __name__ == '__main__':
    main()
