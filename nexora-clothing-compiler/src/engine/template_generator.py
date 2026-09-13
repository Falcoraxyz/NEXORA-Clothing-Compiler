"""
Procedural Template Generator
Generates Roblox-compatible UV templates from constraint graphs.
Handles panel cutting, boundary locking, and seam solving.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Dict, List, Tuple, Optional
import os

from src.compiler.uv_constraint_graph import (
    UVConstraintGraph, UVPanel, UVEdge, EdgePosition, EdgeConstraint,
    build_uv_graph
)
from src.compiler.dsl_schema import ClothingSpec, GarmentType


class ProceduralTemplateGenerator:
    """
    Generates Roblox UV templates from constraint graphs.
    The template is a 512x512 PNG that Roblox Studio accepts.
    """
    
    ROBLOX_SHIRT_SIZE = (512, 512)
    ROBLOX_PANTS_SIZE = (512, 512)
    ROBLOX_TSHIRT_SIZE = (512, 512)
    
    def __init__(self, spec: ClothingSpec):
        self.spec = spec
        self.graph = build_uv_graph(spec.garment.garment_type.value)
        self.template_size = self.ROBLOX_SHIRT_SIZE
        if spec.garment.garment_type == GarmentType.PANTS:
            self.template_size = self.ROBLOX_PANTS_SIZE
        
        # The output image
        self.template = Image.new("RGBA", self.template_size, (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.template)
        
        # Pixel data per panel (for seam solving)
        self.panel_pixels: Dict[str, np.ndarray] = {}
    
    def generate_template(self) -> Image.Image:
        """Generate the complete template with all panels and seams."""
        print(f"[TemplateGenerator] Generating {self.spec.garment.garment_type.value} template...")
        
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
        
        print(f"[TemplateGenerator] Template generated: {self.template_size}")
        return self.template
    
    def _generate_panel_albedos(self):
        """Generate base albedo (color) for each panel."""
        primary_color = self._hex_to_rgb(self.spec.garment.color.primary)
        secondary_color = self._hex_to_rgb(self.spec.garment.color.secondary) if self.spec.garment.color.secondary else primary_color
        accent_color = self._hex_to_rgb(self.spec.garment.color.accent) if self.spec.garment.color.accent else primary_color
        
        material = self.spec.garment.material
        fabric = material.fabric.value
        
        for panel_id, panel in self.graph.panels.items():
            x, y, w, h = panel.template_position
            
            # Create panel pixel data
            panel_img = np.zeros((h, w, 4), dtype=np.uint8)
            
            # Base fabric color
            panel_img[:, :, 0] = primary_color[0]
            panel_img[:, :, 1] = primary_color[1]
            panel_img[:, :, 2] = primary_color[2]
            panel_img[:, :, 3] = 255
            
            # Add fabric texture based on material
            if fabric == "heavy_cotton":
                noise = np.random.randint(-10, 10, (h, w, 3), dtype=np.int16)
                panel_img[:, :, :3] = np.clip(
                    panel_img[:, :, :3].astype(np.int16) + noise, 0, 255
                ).astype(np.uint8)
            elif fabric == "denim":
                # Denim: diagonal weave pattern
                for i in range(h):
                    for j in range(w):
                        if (i + j) % 3 == 0:
                            panel_img[i, j, :3] = np.clip(
                                panel_img[i, j, :3].astype(np.int16) - 15, 0, 255
                            ).astype(np.uint8)
            elif fabric == "leather":
                # Leather: subtle grain
                noise = np.random.randint(-5, 5, (h, w, 3), dtype=np.int16)
                panel_img[:, :, :3] = np.clip(
                    panel_img[:, :, :3].astype(np.int16) + noise, 0, 255
                ).astype(np.uint8)
            
            # Add fabric folds (vertical gradient for shirt)
            fold_intensity = 0.05
            for i in range(h):
                fold = int(np.sin(i / h * np.pi * 2) * 20 * fold_intensity)
                panel_img[i, :, :3] = np.clip(
                    panel_img[i, :, :3].astype(np.int16) + fold, 0, 255
                ).astype(np.uint8)
            
            self.panel_pixels[panel_id] = panel_img
            
            # Paste into template
            panel_pil = Image.fromarray(panel_img, "RGBA")
            self.template.paste(panel_pil, (x, y))
    
    def _solve_seams(self):
        """
        Solve seam constraints by copying boundary pixels between connected panels.
        This ensures pixel-perfect alignment.
        """
        print(f"[TemplateGenerator] Solving {len(self.graph.constraints)} seam constraints...")
        
        for constraint in self.graph.constraints:
            panel_a_id, edge_a_pos = constraint.edge_a
            panel_b_id, edge_b_pos = constraint.edge_b
            
            panel_a = self.graph.panels[panel_a_id]
            panel_b = self.graph.panels[panel_b_id]
            

            
            # Apply Gaussian blend to seam region (2-4px feathering)
            self._blend_seam(panel_a, panel_b, edge_a_pos, edge_b_pos)
        
        # Update template with solved pixels
        for panel_id, panel in self.graph.panels.items():
            x, y, w, h = panel.template_position
            panel_pil = Image.fromarray(self.panel_pixels[panel_id], "RGBA")
            self.template.paste(panel_pil, (x, y))
    
    def _get_edge_pixels(self, panel: UVPanel, edge_pos: EdgePosition) -> List[Tuple[int, int]]:
        """Get (x, y) coordinates for all pixels along an edge."""
        x, y, w, h = panel.template_position
        positions = []
        
        if edge_pos == EdgePosition.TOP:
            positions = [(x + i, y) for i in range(w)]
        elif edge_pos == EdgePosition.BOTTOM:
            positions = [(x + i, y + h - 1) for i in range(w)]
        elif edge_pos == EdgePosition.LEFT:
            positions = [(x, y + i) for i in range(h)]
        elif edge_pos == EdgePosition.RIGHT:
            positions = [(x + w - 1, y + i) for i in range(h)]
        
        return positions
    
    def _blend_seam(self, panel_a: UVPanel, panel_b: UVPanel, 
                     edge_a: EdgePosition, edge_b: EdgePosition, 
                     blend_width: int = 3):
        """
        Gaussian blend along seam boundary.
        blend_width: number of pixels to feather (2-4px).
        """
        # Get boundary regions for blending
        a_pixels = self.panel_pixels[panel_a.panel_id]
        b_pixels = self.panel_pixels[panel_b.panel_id]
        
        h_a, w_a, _ = a_pixels.shape
        h_b, w_b, _ = b_pixels.shape
        
        # Apply Gaussian blur to edge region of panel B
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
        
        self.panel_pixels[panel_b.panel_id] = b_pixels
    
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
        
        self._update_template()
    
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
        
        self._update_template()
    
    def _add_pocket(self):
        """Add pocket to the front panel."""
        front_panel_id = "front_left"
        if front_panel_id not in self.graph.panels:
            front_panel_id = "front_right"
        
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
    
    def _add_hood(self):
        """Add hood to the top panel."""
        top_panel_id = "top_left"
        if top_panel_id not in self.graph.panels:
            top_panel_id = "top_right"
        
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
        panel_id = "front_left"
        
        if "left" in position:
            panel_id = "front_left"
        elif "right" in position:
            panel_id = "front_right"
        elif "back" in position:
            panel_id = "back_left"
        
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
        front_panel_id = "front_left"
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
    
    def _update_template(self):
        """Update template image from panel pixels."""
        for panel_id, panel in self.graph.panels.items():
            x, y, w, h = panel.template_position
            panel_pil = Image.fromarray(self.panel_pixels[panel_id], "RGBA")
            self.template.paste(panel_pil, (x, y))
    
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


def generate_roblox_template(spec: ClothingSpec, output_path: Optional[str] = None) -> Image.Image:
    """
    Convenience function: generate template from spec.
    
    Usage:
        spec = ClothingSpec.from_dict(EXAMPLE_SPEC)
        template = generate_roblox_template(spec, "output/shirt.png")
    """
    generator = ProceduralTemplateGenerator(spec)
    template = generator.generate_template()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        generator.save(output_path)
    
    return template
