
import copy
import itertools

from requests import options

from oomp_populate_helper import build_oomp_id, write_extras


def main(**kwargs):
    
    options = []
    
    

    # Millimetres except width/height, which count 15 mm OOBB grid units.
    # Keep the complete editable design here; OOMP carries it into working_scad.
    holder = {
        "oobb_type": "holder_motor_pump_submersible_jt_500",
        "oobb_name": "holder_motor_pump_submersible_jt_500",
        "width": 5,
        "height": 5,
        "depth": 6,
        "base_foot_height": 2.7,
        "top_width": 3,
        "top_height": 3,
        "top_depth": 13,
        "pump_offset_y": 15,
        "pump_rotation_z": 0,
        "lid_depth": 3,
        "lid_mount_positions": [
            [-16.5, 7.5],
            [16.5, -7.5],
        ],
        "lid_screw_length": 16,
        "lid_nut_bottom": 2,
        "attachment_nuts": [
            {"radius_name": "m6", "pos": [-15, -15]},
            {"radius_name": "m6", "pos": [-15, 0]},
            {"radius_name": "m6", "pos": [-15, 15]},
            {"radius_name": "m6", "pos": [15, -15]},
            {"radius_name": "m6", "pos": [15, 0]},
            {"radius_name": "m6", "pos": [15, 15]},
        ],
        "clamp_corner_radius": 5,
        "pump_body_width": 33.43,
        "pump_body_height": 38.33,
        "pump_body_length": 79.0,
        "pump_fin_projection": 5.7,
        "pump_outlet_diameter": 11.9,
        "pump_outlet_projection": 21.2,
        "pump_outlet_xy": [0, 9],
        "pump_wire_xy": [0, -9],
        "outlet_clearance_diameter": 15.5,
        "wire_clearance_diameter": 15.5,
        "axial_clearance": 0,
        "pump_outline_clearance": 3,
        "base_window_clearance": 1,
        "omit_covered_base_holes": True,
        "corner_clearance_diameter": 15,
        "retainer_span": 40,
        "retainer_width": 4,
        "retainer_relief_diameter": 16,
        "foot_pitch": 60,
        "foot_size": 12,
        "foot_radius": 4,
        "mount_x": 22.5,
        "mount_y": 7.5,
        "open_width": 28,
        "tab_height": 14,
        "tab_outer_x": 28.5,
        "tab_inner_x": 18,
        "tab_corner_radius": 1,
        "side_print_relief": False,
        "screw_radius_name": "m3",
        "screw_length": 16,
        "nut_height_from_foot": 6,
        "screw_tip_clearance": 2,
        "overhang": True,
        "prepare_print": True,
        "print_gap": 10,
        "run_scad": True,
        "run_solidcraft": "working_scad",
        "dimension_source": "source_file/pump_dimension_reference.png",
        "dimension_note": "Main envelope and 5.7 mm rear projection are dimensioned. Port centres, fin footprints and body profile are approximate; physically check fit before final printing.",
    }
    option = copy.deepcopy(holder)
    option["piece"] = "all"
    option["name"] = "JT-500 two-wall holder - complete print set"
    option["documentation"] = define_documentation()
    options.append(option)

    #load from working_manual.yaml
    if False:
        with open("working_manual.yaml", 'r', encoding='utf-8') as file:
            import yaml
            data = yaml.safe_load(file)
            options_yaml = data.get("options", [])
            for option_yaml in options_yaml:
                options.append(option_yaml)

    
    ###### populate taxonomy details and oobb details
    if True:
        for option in options:       
            option["taxonomy_1"] = "oobb"
            option["taxonomy_2"] = "holder_motor_pump_submersible_jt_500"
            option["taxonomy_3"] = ""
            # oobb_type selects get_<type> independently in each backend.
            if option.get("oobb_type"):
                geometry_details = copy.deepcopy(option)
                geometry_details.pop("documentation", None)
                option["oobb_details"] = {
                    "oobb_type": option["oobb_type"],
                    "oobb_name": option.get("oobb_name", option["oobb_type"]),
                    "width": option.get("width", 1),
                    "height": option.get("height", 1),
                    "depth": option.get("depth", 3),
                    "run_scad": option.get("run_scad", True),
                    # True: native recipe; False: off; "working_scad": shared source.
                    "run_solidcraft": option.get("run_solidcraft", "working_scad"),
                }
                option["oobb_details"].update(geometry_details)
            #svg details
            if False:
                pass
                svg_details = {}
                svg_details["svg_name"] = option_type
                svg_details["svg_width"] = option.get("width", None)            
                svg_details["svg_height"] = option.get("height", None)
                option["svg_details"] = svg_details

    #load the options into full list
    extras = []
    for option in options:
        extra = {}
        extra.update(option)
        extras.append(extra)

    
    ######### add notes from an id string
    import working_oomp_populate_extra_detail
    working_oomp_populate_extra_detail.main(extras=extras)


    write_extras(extras)



def define_documentation(**kwargs):
    """Editable project text, inventory and assembly sequence, carried by OOMP."""
    project_url = kwargs.get("project_url", "https://github.com/oomlout/oomlout_oobb_holder_motor_pump_submersible_jt_500")
    viewer_url = kwargs.get("viewer_url", "")

    return {
        "title": "JT-500 pump holder",
        "configuration_title": "M3 x 16 mm / JT-500",
        "description": "Mount a JT-500 submersible pump upright on a 5 × 5 OOBB base with the outlet facing either way. Two ledges support the pump between its rear inlet openings, leaving a water path underneath. The base, clamp and top cover print together as three separate pieces.",
        "credit": "Documentation follows Oomlout's wave-drive assembly book and OOBB presentation conventions; the pump fit follows the supplied JT-500 dimension drawing.",
        "credit_url": "https://github.com/oomlout/oomlout_oobb_part_motor_gearbox_wave_drive_version_5",
        "creator_name": "Oomlout",
        "creator_url": "https://github.com/oomlout",
        "ai_message": "This is an entirely AI-generated coding project. The source code is largely unreadable by humans, but usable generated files are included. It is published so others can use their own AI tools to understand, modify and regenerate the design.",
        "notice": "AI-generated CAD images and instructions. Errors possible.",
        "physical_status": "Physical pump fit, printed strength and slicing have not been verified.",
        "version_description": "The 6 mm base accepts the pump in either orientation. The cover captures six M6 attachment nuts.",
        "preparation": [
            "Print the single 3dpr.stl once: it contains the base, clamp and top cover, separated by 10 mm on the bed. Keep all three pieces separate. The assembly.scad file shows their fitted positions.",
            "Keep the supplied STL orientations: base plate face on the bed with feet upward; clamp on its open side with the pump axis horizontal. Inspect the slicer preview before printing.",
            "Clear the nut slots, screw bores and water openings. Test that each M3 nut slides fully into its pocket.",
            "Use four M3 x 16 mm countersunk screws for the base and two M3 x 16 mm countersunk screws for the cover. Both lengths include the head; the linked hex-socket screws use a 2 mm hex key.",
            "Leave the hose disconnected. Route the free cable end through both clamp and cover before fitting them; check that any fitted connector clears the circular openings. Use either roof opening for the outlet and the other for the cable.",
        ],
        "installation": [
            "Check that the pump rear face rests on both retaining tongues and that the fins pass into the water openings.",
            "Confirm that the top plate captures the pump, all nuts are seated, and the cable and outlet are free of pinching.",
            "Use the exposed OOBB holes to attach the base to your structure. Choose those attachment fasteners for the mating structure; they are not included in the holder hardware count.",
            "Keep the underside water openings clear when mounting the holder.",
            "The cover presents six accessible M6 captive attachment nuts. Keep M6 screw projection below the cover face to at most 8 mm; the holes pass through the roof, so check that projecting bolts clear the pump. Attachment screws are not included in the inventory.",
        ],
        "part_notes": {
            "base": "Print one black base, plate face down and four feet up. The two inward tongues support the rear housing. The centre relief and upper/lower windows clear the rear projections and admit water. OOBB holes beneath the clamp and nut tabs are omitted. The two M6 corner holes at the flush edge pass through the plate and feet. Curved notches in the clamp give each hole 15 mm diameter clearance. Four countersinks on the underside take the M3 x 16 mm clamp screws.",
            "top": "Print one teal clamp on the open side in the supplied orientation. The two walls connect the top plate to the local nut tabs. Slide four M3 nuts in from the outside edges. Route the outlet and cable through the two 15.5 mm openings before seating the clamp on the base.",
            "lid": "Print the black nut cover flat, with countersinks upward. It traps six M6 attachment nuts in the upper roof pockets. Two M3 fixing nuts slide into lower side slots beneath solid shoulders. Two M3 x 16 mm countersunk screws secure it between the M6 rows within the plate. All top openings are circular.",
        },
        "parts": {
            "base": {
                "name": "Retaining base",
                "id": "oobb_holder_motor_pump_submersible_jt_500__base",
                "printed": True,
                "quantity": 1,
            },
            "top": {
                "name": "Two-wall clamp",
                "id": "oobb_holder_motor_pump_submersible_jt_500__top",
                "printed": True,
                "quantity": 1,
            },
            "lid": {
                "name": "Captive nut cover",
                "id": "oobb_holder_motor_pump_submersible_jt_500__lid",
                "printed": True,
                "quantity": 1,
            },
            "m3nut": {
                "name": "M3 hex nut",
                "id": "hardware_nut_m3",
                "catalogue_url": "https://github.com/oomlout/oomlout_oomp_version_1_messy/tree/main/parts/hardware_nut_m3",
                "printed": False,
                "quantity": 2,
                "detail": "Cover-fixing nuts in the lower roof side slots.",
            },
            "m6nut": {
                "name": "M6 hex nut",
                "id": "hardware_nut_m6",
                "catalogue_url": "https://github.com/oomlout/oomlout_oomp_version_1_messy/tree/main/parts/hardware_nut_m6",
                "printed": False,
                "quantity": 6,
                "detail": "Six accessible top attachment nuts on the 15 mm grid.",
            },
            "capscrew": {
                "name": "M3 x 16 mm countersunk",
                "id": "hardware_screw_countersunk_hex_head_black_m3_diameter_16_mm_length",
                "catalogue_url": "https://github.com/oomlout/oomp_hardware_screw_version_5/tree/main/parts/hardware_screw_countersunk_hex_head_black_m3_diameter_16_mm_length",
                "printed": False,
                "quantity": 2,
                "detail": "Cover fixings; 16 mm including head, driven downward.",
            },
            "pump": {
                "name": "JT-500 pump",
                "id": "motor_pump_submersible_jt_500",
                "catalogue_url": "https://github.com/oomlout/oomp_motor_version_5/tree/main/parts/motor_pump_submersible_jt_500",
                "printed": False,
                "quantity": 1,
                "detail": "Nominal reference envelope; check your pump against the drawing.",
            },
            "nut": {
                "name": "M3 hex nut",
                "id": "hardware_nut_m3",
                "catalogue_url": "https://github.com/oomlout/oomlout_oomp_version_1_messy/tree/main/parts/hardware_nut_m3",
                "printed": False,
                "quantity": 4,
                "detail": "Ordinary hex nut, not a nylon-insert locknut.",
            },
            "screw": {
                "name": "M3 x 16 mm countersunk",
                "id": "hardware_screw_countersunk_hex_head_black_m3_diameter_16_mm_length",
                "catalogue_url": "https://github.com/oomlout/oomp_hardware_screw_version_5/tree/main/parts/hardware_screw_countersunk_hex_head_black_m3_diameter_16_mm_length",
                "printed": False,
                "quantity": 4,
                "detail": "Hex socket; 16 mm overall including the countersunk head. The catalogue black finish is an identity reference, not a corrosion rating.",
            },
        },
        "steps": [
            {
                "key": "step_01",
                "title": "Place the base",
                "action": "Place the base on its four feet, retaining tongues facing upward and the four screw countersinks facing downward.",
                "add": ["base"],
                "move": {},
            },
            {
                "key": "step_02",
                "title": "Seat the pump",
                "action": "Choose which side you want the outlet on. Lower the pump onto the two ledges with its outlet and cable up. Check from underneath that the fins enter the windows and all three inlet openings are clear.",
                "add": ["pump"],
                "move": {"pump": [0, 0, 16]},
            },
            {
                "key": "step_03",
                "title": "Load the nuts and fit the clamp",
                "action": "Slide two M3 nuts into each side of the clamp. Pass the cable through its top opening and lower the clamp over the pump, guiding the outlet through the other opening. Seat both nut tabs against the base.",
                "add": ["top", "nut_1", "nut_2", "nut_3", "nut_4"],
                "move": {
                    "top": [0, 0, 28],
                    "nut_1": [-12, 0, 28],
                    "nut_2": [-12, 0, 28],
                    "nut_3": [12, 0, 28],
                    "nut_4": [12, 0, 28],
                },
            },
            {
                "key": "step_04",
                "title": "Fasten from underneath",
                "action": "Hold the pump and clamp seated while accessing the underside. Insert all four M3 x 16 mm countersunk screws upward into the captive nuts. Start each screw before tightening them evenly until the heads seat; stop when the pump is captured without distorting the printed parts.",
                "add": ["screw_1", "screw_2", "screw_3", "screw_4"],
                "move": {
                    "screw_1": [0, 0, -22],
                    "screw_2": [0, 0, -22],
                    "screw_3": [0, 0, -22],
                    "screw_4": [0, 0, -22],
                },
                "eye": [1.2, -1.6, -1.3],
            },
            {
                "key": "step_05",
                "title": "Load the top nuts",
                "action": "Drop six M6 nuts into the upper roof pockets. Slide one M3 nut into each lower side slot beneath the roof shoulders. Seat every nut flat; keep all six M6 bores clear.",
                "add": ["m6nut_1", "m6nut_2", "m6nut_3", "m6nut_4", "m6nut_5", "m6nut_6", "m3nut_1", "m3nut_2"],
                "move": {
                    "m6nut_1": [0, 0, 10],
                    "m6nut_2": [0, 0, 10],
                    "m6nut_3": [0, 0, 10],
                    "m6nut_4": [0, 0, 10],
                    "m6nut_5": [0, 0, 10],
                    "m6nut_6": [0, 0, 10],
                    "m3nut_1": [-12, 0, 0],
                    "m3nut_2": [12, 0, 0],
                },
                "eye": [1.2, -1.6, 2],
            },
            {
                "key": "step_06",
                "title": "Encapsulate the nuts",
                "action": "Pass the cable through the cover and lower it over the outlet, with the countersinks upward. Insert two M3 x 16 mm countersunk screws downward through the plate into the lower side-loaded M3 nuts and tighten evenly until the cover seats. Keep all six M6 attachment holes clear.",
                "add": ["lid", "capscrew_1", "capscrew_2"],
                "move": {
                    "lid": [0, 0, 18],
                    "capscrew_1": [0, 0, 28],
                    "capscrew_2": [0, 0, 28],
                },
                "eye": [1.2, -1.6, 2],
            },
        ],
        "style": {
            "page_mm": [297, 210],
            "columns": 2,
            "rows": 2,
            "margin_mm": 6,
            "gutter_mm": 4,
            "border_radius_mm": 3,
            "border_width_pt": 3,
            "component_border_width_pt": 1.1,
            "thumbnail_height_mm": 8.5,
            "quantity_shift_mm": 1,
            "border": "000000",
            "font_body_pt": 7,
            "font_code_pt": 6.4,
            "font_url_prefix_pt": 4.8,
            "quantity_pt": 5.8,
            "explosion_scale": 1.35,
            "eye": [1.2, -1.6, 1.1],
        },
        "book": {
            "cover_title": "JT-500 pump holder",
            "cover_subtitle": "5 x 5 OOBB base / M3 x 16 mm screws",
            "project_name": "oomlout_oobb_holder_motor_pump_submersible_jt_500",
            "project_url": project_url,
            "viewer_url": viewer_url,
            "viewer_enabled": True,
            "viewer_start": "page-03",
            "viewer_layout": "a4-landscape-four-step",
            "logo_svg": "source_file/oomlout_logo_unshaded_original.svg",
            "logo_symbol_subpaths": 3,
            "details_title": "Project details",
            "details": [
                "Base: 5 x 5 OOBB units, 74 x 74 mm; 6 mm plate and 2.7 mm corner feet; 3 mm clearance below the fin tips.",
                "Clamp: 3 x 3 OOBB units, 44 x 44 mm above the local nut tabs.",
                "Pump reference body: 33.43 x 38.33 x 79 mm; rear projections 5.7 mm.",
                "Rear retaining tongues and the top plate capture the pump axially.",
                "Fasteners: four M3 x 16 mm countersunk screws driven upward; four side-loaded M3 nuts.",
                "Top cover: two M3 x 16 mm countersunk screws; six M6 attachment nuts plus two M3 fixing nuts.",
                "Top openings: 15.5 mm for the outlet and cable; route the free cable end before lowering the clamp.",
                "One print file: base face down, clamp on its open side, cover flat with countersinks upward.",
                "Either pump orientation fits. Two 4 mm wide tongues support the rear housing between the inlet openings.",
                "Regenerate CAD, renders and instructions: python action_make_holder.py",
                "See Assembly in the part README for the numbered steps and fit checks.",
                "AI-generated CAD images and instructions. Errors possible. Physical fit and slicing unverified.",
            ],
            "summary_title": "Printed parts",
            "hardware_title": "Hardware",
            "summary_step": True,
            "summary_view": "book_cover",
            "summary_description": "Completed edge-aligned JT-500 holder with its captive-nut cover.",
            "signature_pages": 4,
        },
    }


# Call main automatically
if __name__ == "__main__":
    main()
