"""
Procedural Template Generator v2
Generates Roblox-compatible UV templates using official template layout.
Template size: 585×559 (R15)
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import Dict, Tuple, Optional
import os

from src.compiler.dsl_schema import ClothingSpec, GarmentType
from src.compiler.uv_constraint_graph import (
    UVConstraintGraph, UVPanel, EdgePosition, EdgeConstraint,
    build_uv_graph
)
from src.compiler.constraint_solver import SolverResult


class ProceduralTemplateGeneratorV2:
    """
    Generates Roblox UV templates using official template layout.
    Template size: 585×559 pixels (R15)
    """
    
    def __init__(self, spec: ClothingSpec, solver_result: SolverResult):
        self.spec = spec
        self.solver = solver_result
        self.graph = build_uv_graph(spec.garment.garment_type.value)
        self.template_size = self.graph.template_size
        
        # The output image (RGBA)
        self.template = Image.new("RGBA", self.template_size, (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.template)
        
        # Pixel data per panel (numpy arrays)
        self.panel_pixels: Dict[str, np.ndarray] = {}
        
        # Panel positions from graph
        self.panel_positions: Dict[str, Tuple[int, int, int, int]] = {}
        for pid, panel in self.graph.panels.items():
            self.panel_positions[pid] = panel.template_position
    
    def generate_template(self) -> Image.Image:
        """Generate the complete template with all panels and seams."""
        print(f"[TemplateGenerator] Generating {self.spec.garment.garment_type.value} template...")
        print(f"  Template size: {self.template_size}")
        print(f"  Panels: {len(self.graph.panels)}")
        
        # Step 1: Generate base albedo for each panel
        self._generate_panel_albedos()
        
        # Step 2: Solve seams (lock boundaries)
        self._solve_seams()
        
        # Step 3: Add material properties (AO, normal, curvature)
        self._compose_materials()
        
        # Step 4: Add decorations (logo, pocket, zipper)
        self._add_decorations()
        
        # Step 5: Add stitches
        self._add_stitches()
        
        # Step 6: Paste panels into template
        self._paste_panels()
        
        print(f"[TemplateGenerator] Template generated: {self.template_size}")
        return self.template
    
    def _generate_panel_albedos(self):
        """Generate base albedo (color) for each panel with visible fabric texture."""
        primary = self._hex_to_rgb(self.spec.garment.color.primary)
        secondary = self._hex_to_rgb(self.spec.garment.color.secondary) if self.spec.garment.color.secondary else primary
        accent = self._hex_to_rgb(self.spec.garment.color.accent) if self.spec.garment.color.accent else primary
        
        material = self.spec.garment.material
        fabric = material.fabric.value
        fit = self.spec.garment.fit
        
        for panel_id, panel in self.graph.panels.items():
            x, y, w, h = panel.template_position
            
            # Create panel pixel data
            pixels = np.zeros((h, w, 4), dtype=np.uint8)
            
            # Base fabric color
            pixels[:, :, 0] = primary[0]
            pixels[:, :, 1] = primary[1]
            pixels[:, :, 2] = primary[2]
            pixels[:, :, 3] = 255
            
            # Add visible fabric texture based on material
            if fabric == "heavy_cotton":
                self._apply_cotton_texture(pixels, primary, secondary)
            elif fabric == "denim":
                self._apply_denim_texture(pixels, primary, secondary)
            elif fabric == "leather":
                self._apply_leather_texture(pixels, primary, secondary)
            elif fabric == "satin":
                self._apply_satin_texture(pixels, primary, accent)
            elif fabric == "nylon":
                self._apply_nylon_texture(pixels, primary, secondary)
            elif fabric == "wool":
                self._apply_wool_texture(pixels, primary, secondary)
            
            # Add panel border highlight
            self._apply_panel_border(pixels, accent)
            
            # Add fabric folds
            self._apply_folds(pixels, fit)
            
            self.panel_pixels[panel_id] = pixels
    
    def _apply_cotton_texture(self, pixels, primary, secondary):
        """Heavy cotton: subtle weave with color variation."""
        h, w, _ = pixels.shape
        for y in range(h):
            for x in range(w):
                # Diagonal weave pattern
                weave = int(np.sin((x + y) * 0.3) * 8)
                # Random fiber noise
                noise = np.random.randint(-5, 5)
                
                # Color variation
                r = np.clip(primary[0] + weave + noise, 0, 255)
                g = np.clip(primary[1] + weave + noise, 0, 255)
                b = np.clip(primary[2] + weave + noise, 0, 255)
                
                pixels[y, x, :3] = [r, g, b]
    
    def _apply_denim_texture(self, pixels, primary, secondary):
        """Denim: diagonal twill weave pattern."""
        h, w, _ = pixels.shape
        for y in range(h):
            for x in range(w):
                # Diagonal twill pattern
                twill = (x + y) % 4
                if twill == 0:
                    factor = 0.9
                elif twill == 1:
                    factor = 1.0
                elif twill == 2:
                    factor = 0.95
                else:
                    factor = 1.05
                
                noise = np.random.randint(-3, 3)
                r = np.clip(int(primary[0] * factor) + noise, 0, 255)
                g = np.clip(int(primary[1] * factor) + noise, 0, 255)
                b = np.clip(int(primary[2] * factor) + noise + 5, 0, 255)
                
                pixels[y, x, :3] = [r, g, b]
    
    def _apply_leather_texture(self, pixels, primary, secondary):
        """Leather: organic grain pattern."""
        h, w, _ = pixels.shape
        # Generate random grain spots
        grain = np.random.randint(-15, 15, (h, w))
        
        # Smooth the grain
        from scipy.ndimage import gaussian_filter
        if h > 10 and w > 10:
            grain = gaussian_filter(grain.astype(float), sigma=2).astype(int)
        
        for y in range(h):
            for x in range(w):
                g = grain[y, x]
                r = np.clip(primary[0] + g, 0, 255)
                g_val = np.clip(primary[1] + g - 5, 0, 255)
                b = np.clip(primary[2] + g - 10, 0, 255)
                
                pixels[y, x, :3] = [r, g_val, b]
    
    def _apply_satin_texture(self, pixels, primary, accent):
        """Satin: smooth with horizontal sheen."""
        h, w, _ = pixels.shape
        for y in range(h):
            # Horizontal sheen gradient
            sheen = int(np.sin(y / h * np.pi) * 20)
            for x in range(w):
                noise = np.random.randint(-3, 3)
                r = np.clip(primary[0] + sheen + noise, 0, 255)
                g = np.clip(primary[1] + sheen + noise, 0, 255)
                b = np.clip(primary[2] + sheen + noise, 0, 255)
                
                pixels[y, x, :3] = [r, g, b]
    
    def _apply_nylon_texture(self, pixels, primary, secondary):
        """Nylon: fine crosshatch pattern."""
        h, w, _ = pixels.shape
        for y in range(h):
            for x in range(w):
                # Fine crosshatch
                cross = int(np.sin(x * 0.5) * np.sin(y * 0.5) * 10)
                noise = np.random.randint(-3, 3)
                
                r = np.clip(primary[0] + cross + noise, 0, 255)
                g = np.clip(primary[1] + cross + noise, 0, 255)
                b = np.clip(primary[2] + cross + noise, 0, 255)
                
                pixels[y, x, :3] = [r, g, b]
    
    def _apply_wool_texture(self, pixels, primary, secondary):
        """Wool: knitted pattern with loops."""
        h, w, _ = pixels.shape
        for y in range(h):
            for x in range(w):
                # Knit pattern
                knit = int(np.sin(x * 0.4) * np.sin(y * 0.4) * 12)
                noise = np.random.randint(-8, 8)
                
                r = np.clip(primary[0] + knit + noise, 0, 255)
                g = np.clip(primary[1] + knit + noise, 0, 255)
                b = np.clip(primary[2] + knit + noise, 0, 255)
                
                pixels[y, x, :3] = [r, g, b]
    
    def _apply_panel_border(self, pixels, accent):
        """Add visible panel border."""
        h, w, _ = pixels.shape
        border = 2
        
        # Top border
        pixels[:border, :, :3] = accent
        # Bottom border
        pixels[-border:, :, :3] = accent
        # Left border
        pixels[:, :border, :3] = accent
        # Right border
        pixels[:, -border:, :3] = accent
    
    def _apply_folds(self, pixels, fit):
        """Add fabric fold shadows."""
        h, w, _ = pixels.shape
        
        if fit == "oversized":
            fold_intensity = 15
            fold_freq = 2
        elif fit == "slim":
            fold_intensity = 5
            fold_freq = 1
        else:
            fold_intensity = 10
            fold_freq = 2
        
        for y in range(h):
            fold = int(np.sin(y / h * np.pi * fold_freq) * fold_intensity)
            pixels[y, :, :3] = np.clip(pixels[y, :, :3].astype(np.int16) + fold, 0, 255).astype(np.uint8)
    
    def _solve_seams(self):
        """
        Solve seam constraints.
        For Roblox template, panels are not adjacent in 2D space.
        Seam consistency is achieved by using same generation params for connected panels.
        """
        print(f"[TemplateGenerator] Processing {len(self.graph.constraints)} seam constraints...")
        print("  (Roblox UV mapping handles edge wrapping - panels generated independently)")
        
        # For Roblox template, we don't copy pixels between panels
        # because they're laid out with gaps in the template image.
        # Instead, we ensure consistency by using the same generation
        # parameters for connected panels (same color, same fabric, etc.)
        pass
    
    def _get_edge_pixel_data(self, pixels: np.ndarray, edge_pos: EdgePosition) -> Optional[np.ndarray]:
        """Get pixel data along an edge (returns a copy)."""
        h, w, c = pixels.shape
        if edge_pos == EdgePosition.TOP:
            return pixels[0, :, :].copy()
        elif edge_pos == EdgePosition.BOTTOM:
            return pixels[h - 1, :, :].copy()
        elif edge_pos == EdgePosition.LEFT:
            return pixels[:, 0, :].copy()
        elif edge_pos == EdgePosition.RIGHT:
            return pixels[:, w - 1, :].copy()
        return None
    
    def _set_edge_pixel_data(self, pixels: np.ndarray, edge_pos: EdgePosition, data: np.ndarray):
        """Set pixel data along an edge."""
        h, w, c = pixels.shape
        if edge_pos == EdgePosition.TOP:
            pixels[0, :, :] = data
        elif edge_pos == EdgePosition.BOTTOM:
            pixels[h - 1, :, :] = data
        elif edge_pos == EdgePosition.LEFT:
            pixels[:, 0, :] = data
        elif edge_pos == EdgePosition.RIGHT:
            pixels[:, w - 1, :] = data
    
    def _blend_seam_numpy(self, a_pixels: np.ndarray, b_pixels: np.ndarray,
                           edge_a: EdgePosition, edge_b: EdgePosition,
                           blend_width: int = 3):
        """
        Gaussian blend along seam boundary using numpy.
        """
        h_a, w_a, _ = a_pixels.shape
        h_b, w_b, _ = b_pixels.shape
        
        for i in range(blend_width):
            alpha = (i + 1) / (blend_width + 1)
            
            if edge_b == EdgePosition.LEFT:
                col = i
                if col < w_b:
                    b_pixels[:, col, :3] = (
                        b_pixels[:, col, :3].astype(np.float32) * (1 - alpha) +
                        a_pixels[:, w_a - 1, :3].astype(np.float32) * alpha * 0.5
                    ).astype(np.uint8)
            elif edge_b == EdgePosition.RIGHT:
                col = w_b - 1 - i
                if col >= 0:
                    b_pixels[:, col, :3] = (
                        b_pixels[:, col, :3].astype(np.float32) * (1 - alpha) +
                        a_pixels[:, 0, :3].astype(np.float32) * alpha * 0.5
                    ).astype(np.uint8)
            elif edge_b == EdgePosition.TOP:
                row = i
                if row < h_b:
                    b_pixels[row, :, :3] = (
                        b_pixels[row, :, :3].astype(np.float32) * (1 - alpha) +
                        a_pixels[h_a - 1, :, :3].astype(np.float32) * alpha * 0.5
                    ).astype(np.uint8)
            elif edge_b == EdgePosition.BOTTOM:
                row = h_b - 1 - i
                if row >= 0:
                    b_pixels[row, :, :3] = (
                        b_pixels[row, :, :3].astype(np.float32) * (1 - alpha) +
                        a_pixels[0, :, :3].astype(np.float32) * alpha * 0.5
                    ).astype(np.uint8)
    
    def _compose_materials(self):
        """Compose material properties: AO, normal, curvature."""
        print("[TemplateGenerator] Composing materials (AO, normal, curvature)...")
        
        # Ambient Occlusion (AO) - darken edges and folds
        ao_intensity = self.spec.garment.material.roughness * 0.3
        
        for panel_id, panel in self.graph.panels.items():
            pixels = self.panel_pixels[panel_id]
            h, w, _ = pixels.shape
            
            # Edge darkening (AO)
            ao = np.ones((h, w), dtype=np.float32)
            for i in range(h):
                for j in range(w):
                    # Distance to nearest edge
                    dist = min(i, j, h - 1 - i, w - 1 - j)
                    if dist < 8:
                        ao[i, j] = 1.0 - (8 - dist) / 8 * ao_intensity
            
            pixels[:, :, :3] = (pixels[:, :, :3].astype(np.float32) * ao[:, :, np.newaxis]).astype(np.uint8)
            self.panel_pixels[panel_id] = pixels
    
    def _add_decorations(self):
        """Add decorations: pocket, logo, hood, etc."""
        print("[TemplateGenerator] Adding decorations...")
        
        # Add pocket
        if self.spec.garment.pocket.style.value != "none":
            self._add_pocket()
        
        # Add hood
        if self.spec.garment.hood:
            self._add_hood()
        
        # Add logo
        if self.spec.garment.logo:
            self._add_logo()
        
        # Add extras (chain, belt, etc.)
        for extra in self.spec.garment.extras:
            if extra == "chain":
                self._add_chain()
            elif extra == "belt":
                self._add_belt()
    
    def _add_pocket(self):
        """Add pocket to the front panel."""
        front_panel_id = "front"
        if front_panel_id not in self.graph.panels:
            return
        
        panel = self.graph.panels[front_panel_id]
        x, y, w, h = panel.template_position
        pixels = self.panel_pixels[front_panel_id]
        
        pocket_style = self.spec.garment.pocket.style.value
        
        if pocket_style == "kangaroo":
            # Kangaroo pocket: centered, large
            pocket_x = x + w // 4
            pocket_y = y + h // 3
            pocket_w = w // 2
            pocket_h = h // 3
            
            # Draw pocket shape
            self.draw.rectangle(
                [pocket_x, pocket_y, pocket_x + pocket_w, pocket_y + pocket_h],
                fill=(0, 0, 0, 0),
                outline=self._hex_to_rgb(self.spec.garment.color.secondary or "#222222"),
                width=2
            )
            
            # Pocket opening line
            self.draw.line(
                [(pocket_x, pocket_y + 10), (pocket_x + pocket_w, pocket_y + 10)],
                fill=self._hex_to_rgb(self.spec.garment.color.secondary or "#222222"),
                width=2
            )
        elif pocket_style == "chest":
            # Chest pocket: smaller, upper area
            pocket_x = x + 10
            pocket_y = y + 15
            pocket_w = 30
            pocket_h = 25
            
            self.draw.rectangle(
                [pocket_x, pocket_y, pocket_x + pocket_w, pocket_y + pocket_h],
                fill=(0, 0, 0, 0),
                outline=self._hex_to_rgb(self.spec.garment.color.secondary or "#222222"),
                width=2
            )
        elif pocket_style == "cargo":
            # Cargo pocket: large, with flap
            pocket_x = x + 15
            pocket_y = y + h // 3
            pocket_w = w - 30
            pocket_h = h // 3
            
            # Pocket body
            self.draw.rectangle(
                [pocket_x, pocket_y, pocket_x + pocket_w, pocket_y + pocket_h],
                fill=(0, 0, 0, 60),
                outline=self._hex_to_rgb(self.spec.garment.color.secondary or "#222222"),
                width=2
            )
            # Pocket flap
            self.draw.polygon([
                (pocket_x, pocket_y),
                (pocket_x + pocket_w, pocket_y),
                (pocket_x + pocket_w - 5, pocket_y - 10),
                (pocket_x + 5, pocket_y - 10),
            ], fill=None, outline=self._hex_to_rgb(self.spec.garment.color.secondary or "#222222"), width=2)
            # Button
            self.draw.ellipse(
                [pocket_x + pocket_w // 2 - 3, pocket_y - 5, pocket_x + pocket_w // 2 + 3, pocket_y + 1],
                fill=self._hex_to_rgb(self.spec.garment.color.accent or "#FFFFFF")
            )
    
    def _add_hood(self):
        """Add hood to the top panel."""
        top_panel_id = "top"
        if top_panel_id not in self.graph.panels:
            return
        
        panel = self.graph.panels[top_panel_id]
        x, y, w, h = panel.template_position
        
        # Draw hood outline (curved shape)
        hood_points = [
            (x + w // 4, y),
            (x + w // 4, y + h // 2),
            (x + w * 3 // 4, y + h // 2),
            (x + w * 3 // 4, y),
        ]
        
        # Hood shape (trapezoid with curve)
        self.draw.polygon(
            hood_points,
            fill=None,
            outline=self._hex_to_rgb(self.spec.garment.color.secondary or "#222222"),
            width=2
        )
    
    def _add_logo(self):
        """Add logo to specified position."""
        logo = self.spec.garment.logo
        if not logo:
            return
        
        # Determine panel based on position
        position = logo.position
        panel_id = "front"
        
        if "left" in position:
            panel_id = "front"
        elif "right" in position:
            panel_id = "front"
        elif "back" in position:
            panel_id = "back"
        
        if panel_id not in self.graph.panels:
            return
        
        panel = self.graph.panels[panel_id]
        x, y, w, h = panel.template_position
        
        # Logo position within panel
        if "chest" in position:
            logo_x = x + w // 4
            logo_y = y + h // 4
        elif "sleeve" in position:
            logo_x = x + w // 3
            logo_y = y + h // 3
        else:
            logo_x = x + w // 3
            logo_y = y + h // 3
        
        logo_size = int(min(w, h) * logo.scale)
        
        # Draw logo (simplified as text or shape)
        motif = logo.motif
        logo_color = self._hex_to_rgb(self.spec.garment.color.accent or "#FFFFFF")
        
        if motif == "skull":
            # Simple skull shape
            self.draw.ellipse(
                [logo_x, logo_y, logo_x + logo_size, logo_y + logo_size],
                fill=None,
                outline=logo_color,
                width=2
            )
            # Eyes
            eye_size = logo_size // 5
            self.draw.ellipse(
                [logo_x + logo_size // 4, logo_y + logo_size // 3,
                 logo_x + logo_size // 4 + eye_size, logo_y + logo_size // 3 + eye_size],
                fill=logo_color
            )
            self.draw.ellipse(
                [logo_x + logo_size * 3 // 4 - eye_size, logo_y + logo_size // 3,
                 logo_x + logo_size * 3 // 4, logo_y + logo_size // 3 + eye_size],
                fill=logo_color
            )
        else:
            # Default: circle logo
            self.draw.ellipse(
                [logo_x, logo_y, logo_x + logo_size, logo_y + logo_size],
                fill=None,
                outline=logo_color,
                width=2
            )
    
    def _add_chain(self):
        """Add chain accessory."""
        front_panel_id = "front"
        if front_panel_id not in self.graph.panels:
            return
        
        panel = self.graph.panels[front_panel_id]
        x, y, w, h = panel.template_position
        
        # Chain: silver line from hood to pocket
        chain_color = self._hex_to_rgb("#C0C0C0")
        
        # Start from neck area
        start_x = x + w // 2
        start_y = y + 5
        
        # End at chest
        end_x = x + w // 2
        end_y = y + h // 2
        
        # Draw chain as dotted line
        for i in range(20):
            t = i / 20
            cx = int(start_x + (end_x - start_x) * t)
            cy = int(start_y + (end_y - start_y) * t)
            self.draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=chain_color)
    
    def _add_belt(self):
        """Add belt accessory around waist (bottom panel for pants)."""
        # For pants, belt goes around the waist (top panel)
        waist_panel_id = "top"
        if waist_panel_id not in self.graph.panels:
            waist_panel_id = "bottom"
        
        if waist_panel_id not in self.graph.panels:
            return
        
        panel = self.graph.panels[waist_panel_id]
        x, y, w, h = panel.template_position
        
        belt_color = self._hex_to_rgb("#8B7355")
        
        # Belt: horizontal line with buckle
        belt_y = y + h // 2
        
        # Belt line
        self.draw.line([(x + 10, belt_y), (x + w - 10, belt_y)], fill=belt_color, width=3)
        
        # Belt buckle
        buckle_x = x + w // 2
        self.draw.rectangle([buckle_x - 8, belt_y - 5, buckle_x + 8, belt_y + 5], fill=self._hex_to_rgb("#C0C0C0"))
        self.draw.ellipse([buckle_x - 3, belt_y - 3, buckle_x + 3, belt_y + 3], fill=belt_color)
    
    def _add_stitches(self):
        """Add procedural stitches along panel edges."""
        print("[TemplateGenerator] Adding procedural stitches...")
        
        stitch = self.spec.garment.stitch
        if stitch.type.value == "none":
            return
        
        stitch_color = self._hex_to_rgb(stitch.color)
        
        # Stitch along panel boundaries
        for panel_id, panel in self.graph.panels.items():
            x, y, w, h = panel.template_position
            
            # Stitch from edge
            dist = int(stitch.distance_from_edge / 10 * min(w, h))
            
            # Draw stitch pattern along all edges
            self.draw.line([(x + dist, y + dist), (x + w - dist, y + dist)],
                          fill=stitch_color, width=1)
            self.draw.line([(x + dist, y + h - dist), (x + w - dist, y + h - dist)],
                          fill=stitch_color, width=1)
            self.draw.line([(x + dist, y + dist), (x + dist, y + h - dist)],
                          fill=stitch_color, width=1)
            self.draw.line([(x + w - dist, y + dist), (x + w - dist, y + h - dist)],
                          fill=stitch_color, width=1)
            
            # Add stitch marks (dashed line effect)
            if stitch.type.value == "double":
                inner_dist = dist + 3
                self.draw.line([(x + inner_dist, y + inner_dist), (x + w - inner_dist, y + inner_dist)],
                              fill=stitch_color, width=1)
                self.draw.line([(x + inner_dist, y + h - inner_dist), (x + w - inner_dist, y + h - inner_dist)],
                              fill=stitch_color, width=1)
                self.draw.line([(x + inner_dist, y + inner_dist), (x + inner_dist, y + h - inner_dist)],
                              fill=stitch_color, width=1)
                self.draw.line([(x + w - inner_dist, y + inner_dist), (x + w - inner_dist, y + h - inner_dist)],
                              fill=stitch_color, width=1)
    
    def _paste_panels(self):
        """Paste all panel pixels into the template."""
        for panel_id, panel in self.graph.panels.items():
            x, y, w, h = panel.template_position
            pixels = self.panel_pixels.get(panel_id)
            if pixels is not None:
                panel_img = Image.fromarray(pixels, "RGBA")
                self.template.paste(panel_img, (x, y))
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def save(self, output_path: str):
        """Save template to file."""
        self.template.save(output_path)
        print(f"[TemplateGenerator] Saved template to: {output_path}")
    
    def get_template(self) -> Image.Image:
        """Get the generated template image."""
        return self.template


def generate_roblox_template_v2(spec: ClothingSpec, solver_result: SolverResult,
                                 output_path: Optional[str] = None) -> Image.Image:
    """
    Convenience function: generate template from spec.
    
    Usage:
        spec = ClothingSpec.from_dict(EXAMPLE_SPEC)
        solver_result = solve_constraints(spec)
        template = generate_roblox_template_v2(spec, solver_result, "output/shirt.png")
    """
    generator = ProceduralTemplateGeneratorV2(spec, solver_result)
    template = generator.generate_template()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        generator.save(output_path)
    
    return template
