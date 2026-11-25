"""Tests of rendered solids, not mocks of component requests.

Build current artifacts with python working_verify.py before running this suite.
"""
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np
import trimesh
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[1]


class PumpGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import working_verify
        cls.records = working_verify.discover(root=ROOT)
        cls.base_record = cls.records[0]
        cls.datum = cls.base_record['details']['depth'] + cls.base_record['details']['base_foot_height']
        cls.layout = trimesh.load_mesh(cls.base_record['folder'] / '3dpr.stl')
        cls.holders = [dict(cls.base_record, details=dict(cls.base_record['details'], piece='top'))]
        cls.base = trimesh.load_mesh(cls.base_record['folder'] / 'render/mesh_cache/base.stl')
        cls.lid = trimesh.load_mesh(cls.base_record['folder'] / 'render/mesh_cache/lid.stl')
        cls.pump = trimesh.load_mesh(ROOT / 'source_file/pump_reference.stl')
        cls.pump.apply_transform(trimesh.transformations.rotation_matrix(np.radians(cls.base_record["details"]["pump_rotation_z"]), [0, 0, 1]))
        cls.pump.apply_translation([0, 0, cls.datum])
        cls.base_assembled = cls.base.copy()
        transform = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
        transform[:3, 3] = [0, 0, cls.datum]
        cls.base_assembled.apply_transform(transform)
        cls.base_world = cls.base_assembled.copy()
        cls.base_assembled.apply_translation([0, -cls.base_record['details']['pump_offset_y'], 0])
        cls.lid_assembled = cls.lid.copy()
        cls.lid_assembled.apply_translation([0, 0, cls.datum + 79 + cls.base_record['details']['top_depth']])
        cls.report = {}
        for record in cls.holders:
            d = record['details']
            record['print_mesh'] = trimesh.load_mesh(record['folder'] / 'render/mesh_cache/top.stl')
            transform = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])
            # Inverse of print rotation/translation, then raise to rear-face datum.
            transform[:3, 3] = [0, -22, cls.datum]
            record['assembly_mesh'] = record['print_mesh'].copy()
            record['assembly_mesh'].apply_transform(transform)
            cls.report[d['piece']] = {
                'open_width_mm': d['open_width'], 'tab_height_mm': d['tab_height'],
                'volume_mm3': float(record['print_mesh'].volume),
                'print_bounds_mm': record['print_mesh'].bounds.tolist(),
            }

    @classmethod
    def tearDownClass(cls):
        (ROOT / 'verification.json').write_text(json.dumps(cls.report, indent=2) + '\n')

    def test_artifacts_match_current_sources(self):
        manifest = json.loads((ROOT / 'build_manifest.json').read_text())
        for path, digest in manifest['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest, path)
        for part in manifest['parts']:
            path = ROOT / part['folder'] / '3dpr.stl'
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), part['sha256'])

    def test_only_m3_16_holder_is_populated(self):
        self.assertEqual(len(self.records), 1)
        self.assertEqual(self.records[0]['details']['piece'], 'all')
        self.assertEqual(len(list((ROOT / 'parts_source').glob('*/working.yaml'))), 1)
        self.assertEqual(len(list((ROOT / 'parts').rglob('3dpr.stl'))), 1)
        self.assertEqual(len(self.holders), 1)
        for record in self.records:
            self.assertEqual(record['details']['screw_length'], 16)
            self.assertEqual(record['details']['screw_radius_name'], 'm3')
            self.assertEqual(record['details']['open_width'], 28)
            self.assertEqual(record['details']['tab_height'], 14)
            self.assertNotIn('variant', record['details'])

    def test_combined_print_has_three_separate_bed_level_pieces(self):
        pieces = sorted(self.layout.split(), key=lambda mesh: mesh.extents[2])
        self.assertEqual(len(pieces), 3)
        for mesh in pieces:
            self.assertTrue(mesh.is_watertight)
            self.assertAlmostEqual(mesh.bounds[0, 2], 0, places=3)
        self.assertAlmostEqual(pieces[2].bounds[0, 0] - pieces[1].bounds[1, 0], 10, delta=.02)
        self.assertAlmostEqual(pieces[2].bounds[0, 1] - pieces[0].bounds[1, 1], 10, delta=.02)
        self.assertAlmostEqual(pieces[0].extents[2], 3, places=3)
        self.assertAlmostEqual(pieces[1].extents[2], self.datum, places=3)
        self.assertAlmostEqual(pieces[2].extents[2], 44, places=3)
        self.assertAlmostEqual(self.layout.volume, self.base.volume + self.lid.volume + self.holders[0]['print_mesh'].volume, places=1)

    def test_watertight_single_solids(self):
        for name, mesh in [('base', self.base), ('lid', self.lid)] + [(r['details']['piece'], r['print_mesh']) for r in self.holders]:
            with self.subTest(part=name):
                self.assertTrue(mesh.is_watertight and mesh.is_winding_consistent)
                self.assertEqual(len(mesh.split()), 1)
                self.assertGreater(mesh.volume, 0)

    def test_six_mm_base_and_pump_flat_facing_base_centre(self):
        d = self.base_record['details']
        self.assertEqual(d['depth'], 6)
        # In pump-local coordinates the plate centre is at negative Y.
        ring = self.pump.section([0, 0, 1], [0, 0, self.datum + 42]).vertices
        inward = ring[np.isclose(ring[:, 1], ring[:, 1].min(), atol=.05)]
        outward = ring[np.isclose(ring[:, 1], ring[:, 1].max(), atol=.05)]
        self.assertGreater(np.ptp(inward[:, 0]), 15)
        self.assertLess(np.ptp(outward[:, 0]), 2)
        hits, _, _ = self.base_assembled.ray.intersects_location([[34, -15, -1]], [[0, 0, 1]])
        self.assertEqual(len(hits), 2)
        self.assertAlmostEqual(np.ptp(hits[:, 2]), 6, places=3)
        # The pump rotates inside the clamp; base mountings stay in place.
        centres = [[x, y + d['pump_offset_y'], -1]
                   for x in [-d['mount_x'], d['mount_x']]
                   for y in [-d['mount_y'], d['mount_y']]]
        self.assertFalse(self.base_world.ray.intersects_any(centres, [[0, 0, 1]] * 4).any())
        self.assertEqual(-(d['pump_offset_y'] + 22), -37)

    def test_side_print_orientation_and_flat_contact(self):
        for record in self.holders:
            mesh = record['print_mesh']
            with self.subTest(part=record['details']['piece']):
                self.assertAlmostEqual(mesh.bounds[0, 2], 0, places=3)
                self.assertAlmostEqual(mesh.extents[2], 44, places=3)
                d = record['details']
                self.assertAlmostEqual(mesh.extents[1], d['pump_body_length'] + d['axial_clearance'] + d['top_depth'], places=3)
                # Measure the middle of a 0.2 mm first layer. The faceted
                # rounded OOBB outline starts 0.01 mm above the exact Y extremum.
                section = mesh.section([0, 0, 1], [0, 0, 0.1])
                planar, _ = section.to_2D()
                area = float(sum(p.area for p in planar.polygons_full))
                self.assertGreater(area, 500)
                self.report[record['details']['piece']]['bed_contact_mm2'] = area

    def test_body_stays_within_three_by_three_above_tabs(self):
        for record in self.holders:
            mesh, d = record['assembly_mesh'], record['details']
            vertices = mesh.vertices[(mesh.vertices[:, 2] > self.datum + d['tab_height'] + 0.1) & (mesh.vertices[:, 2] < self.datum + 79)]
            self.assertLessEqual(np.abs(vertices[:, :2]).max(), 22.001)

    def test_exactly_two_walls_in_middle_section(self):
        for record in self.holders:
            section = record['assembly_mesh'].section([0, 0, 1], [0, 0, 45])
            planar, _ = section.to_2D()
            self.assertEqual(len(planar.polygons_full), 2, record['details']['piece'])

    def test_front_and_back_remain_open(self):
        for record in self.holders:
            mesh = record['assembly_mesh']
            origins = [[0, -40, z] for z in np.linspace(6, 84.5, 20)]
            self.assertFalse(mesh.ray.intersects_any(origins, [[0, 1, 0]] * len(origins)).any())

    def test_three_mm_motor_clearance_at_multiple_sections(self):
        import working_scad
        for record in self.holders:
            outline = working_scad.get_jt500_outline(outline_offset=2.98)
            samples = [[x, y, z] for z in [6, 12, 25, 45, 70, 84.5] for x, y in outline]
            self.assertFalse(record['assembly_mesh'].contains(samples).any(), record['details']['piece'])

    def test_exposed_grid_bores_are_open_at_nominal_diameter(self):
        import oobb
        import working_scad
        from shapely.geometry import Point
        footprint = working_scad.get_jt500_clamp_footprint(**self.base_record['details'])
        items = [('base', self.base_assembled, 5, 5)]
        for name, mesh, width, height in items:
            origins = []
            for ix in range(2 * width - 1):
                for iy in range(2 * height - 1):
                    x, y = (ix - width + 1) * 7.5, (iy - height + 1) * 7.5
                    y -= self.base_record['details']['pump_offset_y']
                    size = 'm6' if ix % 2 == iy % 2 == 0 else 'm3'
                    if name == 'base' and footprint.distance(Point(x, y)) <= max(
                            oobb.gv('hole_radius_' + size, mode) for mode in ['true', '3dpr', 'laser']):
                        continue
                    radius = oobb.gv('hole_radius_' + size, '3dpr') * 0.95
                    origins.append([x, y, -1])
                    origins.extend([[x + radius * np.cos(a), y + radius * np.sin(a), -1]
                                    for a in np.linspace(0, 2 * np.pi, 8, endpoint=False)])
            self.assertFalse(mesh.ray.intersects_any(origins, [[0, 0, 1]] * len(origins)).any(), name)

    def test_covered_base_holes_are_filled_and_mounting_bores_stay_open(self):
        # Former grid centres under the housing/rails and bores overlapping
        # the outer tab edges must now be solid through the plate.
        points = [[x, y, z] for x, y in [(-22.5, 0), (22.5, 0),
                  (-22.5, 15), (22.5, 15), (-15, 0), (15, 0)] for z in [2.8, 4, 5.6]]
        self.assertTrue(self.base_assembled.contains(points).all())
        origins = [[x, y, -1] for x in [-22.5, 22.5] for y in [-7.5, 7.5]]
        self.assertFalse(self.base_assembled.ray.intersects_any(origins, [[0, 0, 1]] * 4).any())

    def test_upper_base_corners_accept_m6_with_15_mm_holder_clearance(self):
        import oobb
        # Base-local coordinates in the assembled mesh are relative to the pump.
        y = 30 - self.base_record['details']['pump_offset_y']
        bore_radius = oobb.gv('hole_radius_m6', '3dpr')
        for x in [-30, 30]:
            angles = np.arange(48) * 2 * np.pi / 48
            origins = [[x + (bore_radius - .05) * np.cos(a),
                        y + (bore_radius - .05) * np.sin(a), -1] for a in angles]
            self.assertFalse(self.base_assembled.ray.intersects_any(origins, [[0, 0, 1]] * len(origins)).any())
            # A ring of plate around the bore distinguishes an M6 hole from a 15 mm cutout.
            self.assertTrue(self.base_assembled.contains([
                [x + (bore_radius + .2) * np.cos(a), y + (bore_radius + .2) * np.sin(a), 5] for a in angles
            ]).all())
            gauge = trimesh.creation.cylinder(radius=7.5, height=120, sections=256)
            gauge.apply_translation([x, y, self.datum + 60])
            for mesh in [self.holders[0]['assembly_mesh'], self.lid_assembled]:
                overlap = trimesh.boolean.intersection([gauge, mesh], engine='manifold')
                self.assertTrue(overlap.is_empty or abs(overlap.volume) < .00001)

    def test_nominal_pump_and_parts_have_no_collisions(self):
        for record in self.holders:
            for name, mesh in [('pump', self.pump), ('base', self.base_assembled)]:
                overlap = trimesh.boolean.intersection([record['assembly_mesh'], mesh], engine='manifold')
                volume = 0 if overlap.is_empty else abs(float(overlap.volume))
                self.assertLess(volume, 0.001, (record['details']['piece'], name))

    def test_base_supports_body_and_fin_tips_clear_foot_plane(self):
        self.assertAlmostEqual(self.base_assembled.bounds[0, 2], 0, places=3)
        self.assertAlmostEqual(self.pump.bounds[0, 2], 3, places=3)
        self.assertAlmostEqual(self.base_assembled.bounds[1, 2], self.datum, places=3)
        overlap = trimesh.boolean.intersection([self.pump, self.base_assembled], engine='manifold')
        self.assertTrue(overlap.is_empty or abs(overlap.volume) < 0.001)
        lower = self.pump.copy()
        lower.apply_translation([0, 0, -0.05])
        self.assertGreater(trimesh.boolean.intersection([lower, self.base_assembled], engine='manifold').volume, 0.1)

    def test_water_access_and_four_corner_feet(self):
        self.assertFalse(self.base_assembled.ray.intersects_any([[0, 0, -1]], [[0, 0, 1]])[0])
        section = self.base_assembled.section([0, 0, 1], [0, 0, 1])
        planar, _ = section.to_2D()
        self.assertEqual(len(planar.polygons_full), 4)

    def test_retaining_tongues_extend_under_solid_rear_face(self):
        points = [[x, y, self.datum - .1] for x in [-12, -9, 9, 12] for y in [-1.75, 1.75]]
        self.assertTrue(self.base_assembled.contains(points).all())
        self.assertTrue(self.pump.contains([[x, y, self.datum + .1] for x, y, _ in points]).all())
        # The centre projection, both fins and both water windows remain open.
        origins = [[0, y, -1] for y in [-13, -8, 0, 8, 13.5]]
        self.assertFalse(self.base_assembled.ray.intersects_any(origins, [[0, 0, 1]] * len(origins)).any())

    def test_inlet_clearance_and_retention_in_both_orientations(self):
        from shapely.affinity import translate
        from shapely.geometry import box
        from shapely.ops import unary_union

        def cross_section(mesh, z):
            return [Polygon(loop[:, :2]) for loop in mesh.section([0, 0, 1], [0, 0, z]).discrete]

        # Intersect the actual exported plate with the rear face of the reference
        # pump. The three interior loops are its two diagonal slots and curved inlet.
        plate_loops = sorted(cross_section(self.base_assembled, self.datum - .1),
                             key=lambda polygon: polygon.area, reverse=True)
        plate = plate_loops[0].difference(unary_union(plate_loops[1:]))
        min_contact = float('inf')
        for degrees in [0, 180]:
            pump = self.pump.copy()
            pump.apply_transform(trimesh.transformations.rotation_matrix(np.radians(degrees), [0, 0, 1]))
            for mesh in [self.base_assembled, self.holders[0]['assembly_mesh'], self.lid_assembled]:
                overlap = trimesh.boolean.intersection([mesh, pump], engine='manifold')
                self.assertTrue(overlap.is_empty or abs(overlap.volume) < .001)
            boundary, *inlets = sorted(cross_section(pump, self.datum + .1),
                                       key=lambda polygon: polygon.area, reverse=True)
            self.assertEqual(len(inlets), 3)
            rear_face = boundary.difference(unary_union(inlets))
            for inlet in inlets:
                # Convex hull of the four shifted outlines contains its full sweep.
                sweep = unary_union([translate(inlet, x, y) for x in [-3, 3] for y in [-3, 3]]).convex_hull
                self.assertTrue(plate.disjoint(sweep), (degrees, inlet.bounds))
            for x in [-3, 0, 3]:
                for y in [-3, 0, 3]:
                    seated = translate(rear_face, x, y).intersection(plate)
                    for side in [-1, 1]:
                        tongue = box(
                            min(0, side * 20), -2, max(0, side * 20), 2)
                        area = seated.intersection(tongue).area
                        self.assertGreater(area, 12, (degrees, x, y, side))
                        min_contact = min(min_contact, area)
        self.report['top']['minimum_contact_per_tongue_mm2'] = min_contact

    def test_top_and_base_capture_pump_without_nominal_axial_slack(self):
        raised = self.pump.copy()
        raised.apply_translation([0, 0, 0.25])
        for record in self.holders:
            self.assertEqual(record['details']['axial_clearance'], 0)
            overlap = trimesh.boolean.intersection([raised, record['assembly_mesh']], engine='manifold')
            self.assertFalse(overlap.is_empty)
            self.assertGreater(overlap.volume, 5)
            self.report[record['details']['piece']]['retention_upward_overlap_mm3'] = float(overlap.volume)

    def test_nut_slots_load_outwards(self):
        for record in self.holders:
            for x in [-22.5, 22.5]:
                for y in [-7.5, 7.5]:
                    points = [[np.sign(x) * xx, y + dy, self.datum + 7.5 + dz]
                              for xx in np.linspace(abs(x), 30, 15)
                              for dy in [-2.7, 0, 2.7] for dz in [-1, 0, 1]]
                    self.assertFalse(record['assembly_mesh'].contains(points).any())

    def test_countersinks_face_down_and_screws_reach_nuts(self):
        for x in [-22.5, 22.5]:
            for y in [-7.5, 7.5]:
                self.assertFalse(self.base_assembled.contains([[x + 2.8, y, 2.75]])[0])
                self.assertTrue(self.base_assembled.contains([[x + 2.8, y, 5.6]])[0])
        for record in self.holders:
            d = record['details']
            self.assertGreater(d['screw_length'] - d['depth'], d['nut_height_from_foot'] + 3)
            self.assertGreater(d['tab_height'], d['screw_length'] - d['depth'])

    def test_port_holes_are_circular_without_triangle_relief(self):
        for record in self.holders:
            self.assertFalse(record['details']['side_print_relief'])
            for mesh, z in [(record['assembly_mesh'], self.datum + 83), (self.lid_assembled, self.lid_assembled.bounds[0, 2] + 1.5)]:
                # Above the outlet circle must be solid, not a teardrop apex.
                self.assertTrue(mesh.contains([[0, 19.5, z]])[0])
                for y in [-9, 9]:
                    angles = np.linspace(0, 2 * np.pi, 20, endpoint=False)
                    points = [[7.65 * np.cos(a), y + 7.65 * np.sin(a), z] for a in angles]
                    self.assertFalse(mesh.contains(points).any())

    def test_clamp_flush_edge_and_outlet_outboard(self):
        d = self.base_record['details']
        self.assertEqual(d['pump_offset_y'] + (d['top_height'] * 15 - 1) / 2, (d['height'] * 15 - 1) / 2)
        self.assertGreater(d['pump_outlet_xy'][1], d['pump_wire_xy'][1])

    def test_top_nuts_fit_have_through_bores_and_are_trapped(self):
        import working_scad
        import oobb
        d = self.base_record['details']
        entries = working_scad.get_jt500_attachment_nuts(**d)
        self.assertEqual([e['radius_name'] for e in entries].count('m6'), 6)
        self.assertEqual([e['radius_name'] for e in entries].count('m3'), 0)
        top = self.holders[0]['assembly_mesh']
        for entry in entries:
            x, y = entry['pos']
            size = entry['radius_name']
            floor_z = self.datum + 79 + d['top_depth'] - oobb.gv('nut_depth_' + size, '3dpr')
            radius = oobb.gv('nut_radius_' + size, 'true')
            vertices = [[x + .99 * radius * np.cos(a), y + .99 * radius * np.sin(a), floor_z + .2]
                        for a in np.arange(6) * np.pi / 3]
            self.assertFalse(top.contains(vertices).any())
            self.assertFalse(top.contains([[x, y, self.datum + 79.3]])[0])
            bore_radius = .95 * oobb.gv('hole_radius_' + size, '3dpr')
            origins = [[x + bore_radius * np.cos(a), y + bore_radius * np.sin(a), self.datum + 79.1]
                       for a in np.linspace(0, 2 * np.pi, 12, endpoint=False)]
            for mesh in [top, self.lid_assembled]:
                self.assertFalse(mesh.ray.intersects_any(origins, [[0, 0, 1]] * len(origins)).any())
            # Nut shoulder is covered; bolt centre is open through the lid.
            shoulder = oobb.gv('hole_radius_' + size, '3dpr') + .5
            self.assertTrue(self.lid_assembled.contains([[x + shoulder, y, self.lid_assembled.bounds[0, 2] + 1.5]])[0])
            self.assertFalse(self.lid_assembled.contains([[x, y, self.lid_assembled.bounds[0, 2] + 1.5]])[0])
        for mesh in [top, self.pump]:
            overlap = trimesh.boolean.intersection([mesh, self.lid_assembled], engine='manifold')
            self.assertTrue(overlap.is_empty or abs(overlap.volume) < .001)

    def test_lid_countersinks_face_up_and_screws_reach_nuts(self):
        for x, y in self.base_record['details']['lid_mount_positions']:
            self.assertFalse(self.lid.contains([[x + 2.8, y, 2.95]])[0])
            self.assertTrue(self.lid.contains([[x + 2.8, y, .1]])[0])
        d = self.base_record['details']
        for x, y in d['lid_mount_positions']:
            self.assertLess(abs(x) + 3.3, 22)
            self.assertLess(abs(y) + 3.3, 22)
        self.assertGreater(d['lid_screw_length'], d['lid_depth'] + 3)
        self.assertLessEqual(d['lid_screw_length'], d['top_depth'] + d['lid_depth'])

    def test_invalid_dimensions_fail_early(self):
        import working_scad
        for params in [{'open_width': 44}, {'open_width': -1}, {'screw_length': 10}]:
            with self.assertRaises(ValueError):
                working_scad.get_jt500_top({}, **params)
        with self.assertRaises(ValueError):
            working_scad.get_jt500_base({}, depth=0)

    def test_cover_fixing_nuts_have_shoulders_side_access_and_full_engagement(self):
        d = self.base_record['details']
        top = self.holders[0]['assembly_mesh']
        roof = self.datum + d['pump_body_length'] + d['axial_clearance']
        pocket = roof + d['lid_nut_bottom']
        screw_tip = roof + d['top_depth'] + d['lid_depth'] - d['lid_screw_length']
        self.assertGreaterEqual(screw_tip, roof)
        self.assertLessEqual(screw_tip, pocket + .5)
        for x, y in d['lid_mount_positions']:
            sign = np.sign(x)
            # Load a full nominal M3 hex from outside; the pocket keeps it
            # below a solid shoulder, so pulling upward clamps the lid down.
            for travel in np.linspace(0, 12, 7):
                nut = trimesh.creation.cylinder(radius=5.5 / np.sqrt(3), height=2.5, sections=6)
                nut.apply_translation([x + sign * travel, y, pocket + 1.75])
                overlap = trimesh.boolean.intersection([nut, top], engine='manifold')
                self.assertTrue(overlap.is_empty or overlap.volume < .001)
            self.assertTrue(top.contains([[x, y + 2.5, pocket + 4]])[0])
            # Shaft passes the full roof and cover, stopping at the pump face.
            origins = [[x + 1.65 * np.cos(a), y + 1.65 * np.sin(a), roof - .1]
                       for a in np.linspace(0, 2 * np.pi, 12, endpoint=False)]
            for mesh in [top, self.lid_assembled]:
                self.assertFalse(mesh.ray.intersects_any(origins, [[0, 0, 1]] * len(origins)).any())

    def test_six_m6_nuts_can_load_from_above_without_collisions(self):
        d = self.base_record['details']
        top = self.holders[0]['assembly_mesh']
        floor = self.lid_assembled.bounds[0, 2] - 5.5
        for entry in d['attachment_nuts']:
            for lift in [0, 3, 8]:
                nut = trimesh.creation.cylinder(radius=5.77, height=5, sections=6)
                nut.apply_translation([*entry['pos'], floor + 2.5 + lift])
                overlap = trimesh.boolean.intersection([nut, top], engine='manifold')
                self.assertTrue(overlap.is_empty or overlap.volume < .001)


if __name__ == '__main__':
    unittest.main()
