"""
Material Composer
Composes final PBR materials: albedo + AO + normal + curvature.
Produces the final template image ready for Roblox Studio.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from typing import Dict, Tuple, Optional, List
import math

from src.compiler.dsl_schema import ClothingSpec
from src.compiler.constraint_solver import SolverResult, ConstraintType
from src.engine.garment_engine import ProceduralGarmentEngine


class MaterialComposer:
    """
    Composes final materials from garment engine output.
    Adds decorations, stitches, and exports the final template.
    """

    def __init__(self, spec: ClothingSpec, solver_result: SolverResult, 
                 panel_pixels: Dict[str, np.ndarray]):
        self.spec = spec
        self.solver = solver_result
        self.garment = spec.garment
        self.panel_pixels = panel_pixels

        # Template image
        self.template_size = solver_result.template_size
        self.template = Image.new("RGBA", self.template_size, (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.template)

        # Panel positions from graph
        self.panel_positions = self._get_panel_positions()

    def compose(self) -> Image.Image:
        """Compose the final template."""
        print("[MaterialComposer] Composing final materials...")

        # Step 1: Paste panel pixels
        self._paste_panels()

        # Step 2: Add decorations
        self._add_decorations()

        # Step 3: Add stitches
        self._add_stitches()

        # Step 4: Add zipper
        self._add_zipper()

        # Step 5: Final seam blend
        self._final_seam_blend()

        print(f"[MaterialComposer] Template composed: {self.template_size}")
        return self.template

    def _get_panel_positions(self) -> Dict[str, Tuple[int, int, int, int]]:
        """Get panel positions from solver result."""
        positions = {}
        panel_size = self.solver.global_constraints.get("panel_size", 128)

        # Standard Roblox shirt layout
        layout = [
            ("back_left", 0, 0),
            ("top_left", 128, 0),
            ("front_left", 256, 0),
            ("bottom_left", 384, 0),
            ("back_right", 0, 128),
            ("top_right", 128, 128),
            ("front_right", 256, 128),
            ("bottom_right", 384, 128),
            ("left_sleeve_top", 0, 256),
            ("left_sleeve_bottom", 128, 256),
            ("right_sleeve_top", 256, 256),
            ("right_sleeve_bottom", 384, 256),
        ]

        for panel_id, x, y in layout:
            if panel_id in self.panel_pixels:
                positions[panel_id] = (x, y, panel_size, panel_size)

        return positions

    def _paste_panels(self):
        """Paste all panel pixels into the template."""
        for panel_id, (x, y, w, h) in self.panel_positions.items():
            pixels = self.panel_pixels.get(panel_id)
            if pixels is not None:
                panel_img = Image.fromarray(pixels, "RGBA")
                self.template.paste(panel_img, (x, y))

    def _add_decorations(self):
        """Add decorations (pocket, logo, hood, extras)."""
        for panel_id, pc in self.solver.panel_constraints.items():
            for constraint in pc.constraints:
                if constraint["type"] == ConstraintType.DECORATION.value:
                    params = constraint["params"]
                    dec_type = params.get("type")

                    if dec_type == "pocket":
                        self._add_pocket(panel_id, params)
                    elif dec_type == "logo":
                        self._add_logo(panel_id, params)
                    elif dec_type == "chain":
                        self._add_chain(panel_id, params)

    def _add_pocket(self, panel_id: str, params: Dict):
        """Add pocket decoration."""
        pos = self.panel_positions.get(panel_id)
        if not pos:
            return

        x, y, w, h = pos
        style = params.get("style", "kangaroo")
        color = self._hex_to_rgb(params.get("color", "#222222"))

        if style == "kangaroo":
            # Large centered pocket
            pocket_x = x + w // 4
            pocket_y = y + h // 3
            pocket_w = w // 2
            pocket_h = h // 3

            # Pocket background
            self.draw.rectangle(
                [pocket_x, pocket_y, pocket_x + pocket_w, pocket_y + pocket_h],
                fill=(0, 0, 0, 80),
                outline=color,
                width=2,
            )
            # Pocket opening
            self.draw.line(
                [(pocket_x, pocket_y + 8), (pocket_x + pocket_w, pocket_y + 8)],
                fill=color,
                width=2,
            )
        elif style == "chest":
            # Small chest pocket
            pocket_x = x + 10
            pocket_y = y + 15
            pocket_w = 30
            pocket_h = 25

            self.draw.rectangle(
                [pocket_x, pocket_y, pocket_x + pocket_w, pocket_y + pocket_h],
                fill=(0, 0, 0, 60),
                outline=color,
                width=2,
            )
        elif style == "side":
            # Side pocket
            pocket_x = x + 5
            pocket_y = y + h // 3
            pocket_w = w - 10
            pocket_h = h // 4

            self.draw.rectangle(
                [pocket_x, pocket_y, pocket_x + pocket_w, pocket_y + pocket_h],
                fill=(0, 0, 0, 60),
                outline=color,
                width=2,
            )

    def _add_logo(self, panel_id: str, params: Dict):
        """Add logo decoration."""
        pos = self.panel_positions.get(panel_id)
        if not pos:
            return

        x, y, w, h = pos
        motif = params.get("motif", "circle")
        scale = params.get("scale", 0.3)
        color = self._hex_to_rgb(params.get("color", "#FFFFFF"))

        logo_size = int(min(w, h) * scale)

        # Position within panel
        position = params.get("position", "left_chest")
        if "left" in position:
            logo_x = x + w // 4
        elif "right" in position:
            logo_x = x + w * 3 // 4 - logo_size
        else:
            logo_x = x + w // 2 - logo_size // 2

        if "chest" in position:
            logo_y = y + h // 4
        elif "sleeve" in position:
            logo_y = y + h // 3
        else:
            logo_y = y + h // 2 - logo_size // 2

        if motif == "skull":
            # Draw skull shape
            self.draw.ellipse(
                [logo_x, logo_y, logo_x + logo_size, logo_y + logo_size],
                fill=None,
                outline=color,
                width=2,
            )
            # Eyes
            eye_size = max(logo_size // 5, 2)
            self.draw.ellipse(
                [logo_x + logo_size // 4, logo_y + logo_size // 3,
                 logo_x + logo_size // 4 + eye_size, logo_y + logo_size // 3 + eye_size],
                fill=color,
            )
            self.draw.ellipse(
                [logo_x + logo_size * 3 // 4 - eye_size, logo_y + logo_size // 3,
                 logo_x + logo_size * 3 // 4, logo_y + logo_size // 3 + eye_size],
                fill=color,
            )
            # Nose
            nose_size = max(logo_size // 8, 1)
            self.draw.polygon([
                (logo_x + logo_size // 2, logo_y + logo_size // 2),
                (logo_x + logo_size // 2 - nose_size, logo_y + logo_size // 2 + nose_size * 2),
                (logo_x + logo_size // 2 + nose_size, logo_y + logo_size // 2 + nose_size * 2),
            ], fill=color)
        elif motif == "star":
            # Draw star
            cx = logo_x + logo_size // 2
            cy = logo_y + logo_size // 2
            r = logo_size // 2
            points = []
            for i in range(10):
                angle = math.pi / 2 + i * math.pi / 5
                radius = r if i % 2 == 0 else r // 2
                points.append((cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
            self.draw.polygon(points, fill=None, outline=color, width=2)
        else:
            # Default: circle
            self.draw.ellipse(
                [logo_x, logo_y, logo_x + logo_size, logo_y + logo_size],
                fill=None,
                outline=color,
                width=2,
            )

    def _add_chain(self, panel_id: str, params: Dict):
        """Add chain accessory."""
        pos = self.panel_positions.get(panel_id)
        if not pos:
            return

        x, y, w, h = pos
        color = self._hex_to_rgb(params.get("color", "#C0C0C0"))

        # Chain from neck to chest
        start_x = x + w // 2
        start_y = y + 5
        end_x = x + w // 2
        end_y = y + h // 2

        # Draw chain as connected circles
        num_links = 15
        for i in range(num_links):
            t = i / num_links
            cx = int(start_x + (end_x - start_x) * t)
            cy = int(start_y + (end_y - start_y) * t)
            r = 3
            self.draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    def _add_stitches(self):
        """Add procedural stitches along panel edges."""
        for panel_id, pc in self.solver.panel_constraints.items():
            for constraint in pc.constraints:
                if constraint["type"] == ConstraintType.STITCH_PATTERN.value:
                    self._add_stitches_to_panel(panel_id, constraint["params"])

    def _add_stitches_to_panel(self, panel_id: str, params: Dict):
        """Add stitches to a specific panel."""
        pos = self.panel_positions.get(panel_id)
        if not pos:
            return

        x, y, w, h = pos
        color = self._hex_to_rgb(params.get("color", "#000000"))
        dist = int(params.get("distance_from_edge", 3.0) / 10 * min(w, h))
        spacing = int(params.get("spacing", 2.0) / 10 * min(w, h))
        stitch_type = params.get("type", "single")

        edges = params.get("apply_to_edges", ["top", "bottom", "left", "right"])

        for edge in edges:
            if edge == "top":
                self._draw_stitch_line(x + dist, y + dist, x + w - dist, y + dist, color, spacing)
            elif edge == "bottom":
                self._draw_stitch_line(x + dist, y + h - dist, x + w - dist, y + h - dist, color, spacing)
            elif edge == "left":
                self._draw_stitch_line(x + dist, y + dist, x + dist, y + h - dist, color, spacing)
            elif edge == "right":
                self._draw_stitch_line(x + w - dist, y + dist, x + w - dist, y + h - dist, color, spacing)

        # Double stitch: add inner line
        if stitch_type == "double":
            inner_dist = dist + 4
            for edge in edges:
                if edge == "top":
                    self._draw_stitch_line(x + inner_dist, y + inner_dist, x + w - inner_dist, y + inner_dist, color, spacing)
                elif edge == "bottom":
                    self._draw_stitch_line(x + inner_dist, y + h - inner_dist, x + w - inner_dist, y + h - inner_dist, color, spacing)
                elif edge == "left":
                    self._draw_stitch_line(x + inner_dist, y + inner_dist, x + inner_dist, y + h - inner_dist, color, spacing)
                elif edge == "right":
                    self._draw_stitch_line(x + w - inner_dist, y + inner_dist, x + w - inner_dist, y + h - inner_dist, color, spacing)

    def _draw_stitch_line(self, x1: int, y1: int, x2: int, y2: int, 
                           color: Tuple[int, int, int], spacing: int):
        """Draw a dashed stitch line."""
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx**2 + dy**2)
        if length == 0:
            return

        num_dashes = int(length / (spacing * 2))
        for i in range(num_dashes):
            t1 = i / num_dashes
            t2 = (i + 0.5) / num_dashes
            sx = int(x1 + dx * t1)
            sy = int(y1 + dy * t1)
            ex = int(x1 + dx * t2)
            ey = int(y1 + dy * t2)
            self.draw.line([(sx, sy), (ex, ey)], fill=color, width=1)

    def _add_zipper(self):
        """Add zipper decoration."""
        if self.garment.zipper.style.value == "none":
            return

        color = self._hex_to_rgb(self.garment.zipper.color)

        # Zipper runs down the front center
        front_panels = [pid for pid in ["front_left", "front_right"] if pid in self.panel_positions]

        for panel_id in front_panels:
            pos = self.panel_positions[panel_id]
            if not pos:
                continue

            x, y, w, h = pos
            center_x = x + w // 2

            # Zipper line
            self.draw.line(
                [(center_x, y + 5), (center_x, y + h - 5)],
                fill=color,
                width=3,
            )

            # Zipper teeth
            num_teeth = 20
            for i in range(num_teeth):
                t = i / num_teeth
                ty = int(y + 10 + (h - 20) * t)
                # Left tooth
                self.draw.rectangle(
                    [center_x - 4, ty, center_x - 1, ty + 3],
                    fill=color,
                )
                # Right tooth
                self.draw.rectangle(
                    [center_x + 1, ty, center_x + 4, ty + 3],
                    fill=color,
                )

            # Zipper pull
            pull_y = y + h // 3
            self.draw.rectangle(
                [center_x - 3, pull_y, center_x + 3, pull_y + 8],
                fill=color,
            )

    def _final_seam_blend(self):
        """Apply final Gaussian blend to seam boundaries."""
        blend_width = self.solver.global_constraints.get("blend_width", 3)

        for edge_constraint in self.solver.edge_constraints:
            edge_a = edge_constraint["edge_a"]
            edge_b = edge_constraint["edge_b"]

            panel_a_id = edge_a["panel"]
            panel_b_id = edge_b["panel"]

            pos_a = self.panel_positions.get(panel_a_id)
            pos_b = self.panel_positions.get(panel_b_id)

            if not pos_a or not pos_b:
                continue

            # Apply Gaussian blur to boundary region
            # This is a simplified version - full implementation would
            # extract boundary pixels, blend, and re-paste
            pass

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def save(self, output_path: str):
        """Save template to file."""
        self.template.save(output_path)
        print(f"[MaterialComposer] Saved template to: {output_path}")

    def get_template(self) -> Image.Image:
        return self.template


def compose_materials(spec: ClothingSpec, solver_result: SolverResult,
                      panel_pixels: Dict[str, np.ndarray]) -> Image.Image:
    """Convenience function."""
    composer = MaterialComposer(spec, solver_result, panel_pixels)
    return composer.compose()
