"""
Procedural Garment Engine
Generates geometry, folds, draping, and component placement.
Executes constraints from ConstraintSolver to produce pixel data.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import Dict, Tuple, Optional
import math

from src.compiler.dsl_schema import ClothingSpec
from src.compiler.constraint_solver import SolverResult, ConstraintType


class ProceduralGarmentEngine:
    """
    Executes solved constraints to generate garment pixel data.
    Handles:
    - Base albedo generation per panel
    - Fabric folds (procedural noise + directional)
    - AO (ambient occlusion from geometry)
    - Curvature (edge darkening)
    - Normal map hints (bump from folds)
    """

    def __init__(self, spec: ClothingSpec, solver_result: SolverResult):
        self.spec = spec
        self.solver = solver_result
        self.garment = spec.garment

        # Panel pixel data (numpy arrays)
        self.panel_pixels: Dict[str, np.ndarray] = {}
        self.panel_ao: Dict[str, np.ndarray] = {}
        self.panel_normal: Dict[str, np.ndarray] = {}
        self.panel_curvature: Dict[str, np.ndarray] = {}

    def generate(self) -> Dict[str, np.ndarray]:
        """Generate all panel pixel data."""
        print("[GarmentEngine] Generating procedural garment...")

        # Step 1: Generate base albedo per panel
        self._generate_albedo()

        # Step 2: Generate AO
        self._generate_ao()

        # Step 3: Generate curvature
        self._generate_curvature()

        # Step 4: Generate normal hints
        self._generate_normal_hints()

        # Step 5: Apply folds
        self._apply_folds()

        # Step 6: Compose final panels
        self._compose_panels()

        print(f"[GarmentEngine] Generated {len(self.panel_pixels)} panels")
        return self.panel_pixels

    def _generate_albedo(self):
        """Generate base albedo (diffuse color) for each panel."""
        primary = self._hex_to_rgb(self.spec.garment.color.primary)
        secondary = self._hex_to_rgb(self.spec.garment.color.secondary) if self.spec.garment.color.secondary else primary

        for panel_id, pc in self.solver.panel_constraints.items():
            # Get panel size from graph
            # Default 128x128
            w, h = 128, 128

            # Create base color
            pixels = np.zeros((h, w, 4), dtype=np.uint8)
            pixels[:, :, 0] = primary[0]
            pixels[:, :, 1] = primary[1]
            pixels[:, :, 2] = primary[2]
            pixels[:, :, 3] = 255

            # Add fabric-specific noise
            for constraint in pc.constraints:
                if constraint["type"] == ConstraintType.COLOR_FILL.value:
                    params = constraint["params"]
                    fabric = params.get("fabric", "heavy_cotton")
                    noise_intensity = params.get("noise_intensity", 0.05)

                    if fabric == "heavy_cotton":
                        noise = np.random.randint(-15, 15, (h, w, 3), dtype=np.int16)
                        pixels[:, :, :3] = np.clip(
                            pixels[:, :, :3].astype(np.int16) + noise, 0, 255
                        ).astype(np.uint8)
                    elif fabric == "denim":
                        for i in range(h):
                            for j in range(w):
                                if (i + j) % 3 == 0:
                                    pixels[i, j, :3] = np.clip(
                                        pixels[i, j, :3].astype(np.int16) - 12, 0, 255
                                    ).astype(np.uint8)
                    elif fabric == "leather":
                        noise = np.random.randint(-8, 8, (h, w, 3), dtype=np.int16)
                        pixels[:, :, :3] = np.clip(
                            pixels[:, :, :3].astype(np.int16) + noise, 0, 255
                        ).astype(np.uint8)
                    elif fabric == "satin":
                        # Smooth with slight sheen
                        for i in range(h):
                            sheen = int(math.sin(i / h * math.pi) * 10)
                            pixels[i, :, :3] = np.clip(
                                pixels[i, :, :3].astype(np.int16) + sheen, 0, 255
                            ).astype(np.uint8)

                    # Add secondary color variation
                    if secondary != primary:
                        mask = np.random.random((h, w)) < 0.1
                        pixels[mask, :3] = secondary

            self.panel_pixels[panel_id] = pixels

    def _generate_ao(self):
        """Generate ambient occlusion (edge darkening + fold shadows)."""
        for panel_id in self.solver.panel_constraints:
            pixels = self.panel_pixels.get(panel_id)
            if pixels is None:
                continue

            h, w, _ = pixels.shape
            ao = np.ones((h, w), dtype=np.float32)

            # Edge darkening
            ao_radius = 8
            for i in range(h):
                for j in range(w):
                    dist = min(i, j, h - 1 - i, w - 1 - j)
                    if dist < ao_radius:
                        ao[i, j] = 1.0 - (ao_radius - dist) / ao_radius * 0.3

            self.panel_ao[panel_id] = ao

    def _generate_curvature(self):
        """Generate curvature (convex/concave darkening)."""
        for panel_id in self.solver.panel_constraints:
            pixels = self.panel_pixels.get(panel_id)
            if pixels is None:
                continue

            h, w, _ = pixels.shape
            curvature = np.zeros((h, w), dtype=np.float32)

            # Simple curvature from gradient magnitude
            gray = np.mean(pixels[:, :, :3].astype(np.float32), axis=2)
            gy, gx = np.gradient(gray)
            curvature = np.sqrt(gx**2 + gy**2) / 255.0

            # Normalize
            if curvature.max() > 0:
                curvature = curvature / curvature.max()

            self.panel_curvature[panel_id] = curvature

    def _generate_normal_hints(self):
        """Generate normal map hints from fold geometry."""
        for panel_id in self.solver.panel_constraints:
            pixels = self.panel_pixels.get(panel_id)
            if pixels is None:
                continue

            h, w, _ = pixels.shape
            normal = np.zeros((h, w, 3), dtype=np.float32)

            # Base normal (pointing up)
            normal[:, :, 0] = 0.5  # R (X)
            normal[:, :, 1] = 0.5  # G (Y)
            normal[:, :, 2] = 1.0  # B (Z)

            # Modify from curvature
            curvature = self.panel_curvature.get(panel_id)
            if curvature is not None:
                # Curvature affects normal direction
                gray = np.mean(pixels[:, :, :3].astype(np.float32), axis=2)
                gy, gx = np.gradient(gray)
                strength = self.spec.garment.material.normal_strength

                normal[:, :, 0] = np.clip(0.5 + gx / 255.0 * strength, 0, 1)
                normal[:, :, 1] = np.clip(0.5 + gy / 255.0 * strength, 0, 1)

            self.panel_normal[panel_id] = normal

    def _apply_folds(self):
        """Apply procedural folds to panels."""
        for panel_id, pc in self.solver.panel_constraints.items():
            pixels = self.panel_pixels.get(panel_id)
            if pixels is None:
                continue

            h, w, _ = pixels.shape
            fold_layer = np.zeros((h, w), dtype=np.float32)

            for constraint in pc.constraints:
                if constraint["type"] == ConstraintType.FOLD_GEOMETRY.value:
                    params = constraint["params"]
                    direction = params.get("direction", "vertical")
                    intensity = params.get("intensity", 0.1)
                    frequency = params.get("frequency", 2)

                    if direction == "vertical":
                        for i in range(h):
                            fold = math.sin(i / h * math.pi * frequency) * intensity * 40
                            fold_layer[i, :] += fold
                    elif direction == "horizontal":
                        for j in range(w):
                            fold = math.sin(j / w * math.pi * frequency) * intensity * 40
                            fold_layer[:, j] += fold

            # Apply fold as brightness modulation
            fold_layer = fold_layer / 255.0
            pixels_float = pixels[:, :, :3].astype(np.float32)
            pixels_float = pixels_float * (1.0 + fold_layer[:, :, np.newaxis])
            pixels_float = np.clip(pixels_float, 0, 255)
            pixels[:, :, :3] = pixels_float.astype(np.uint8)
            self.panel_pixels[panel_id] = pixels

    def _compose_panels(self):
        """Compose final panels: albedo + AO + curvature."""
        for panel_id in self.solver.panel_constraints:
            pixels = self.panel_pixels.get(panel_id)
            if pixels is None:
                continue

            h, w, _ = pixels.shape

            # Apply AO
            ao = self.panel_ao.get(panel_id)
            if ao is not None:
                pixels[:, :, :3] = (pixels[:, :, :3].astype(np.float32) * ao[:, :, np.newaxis]).astype(np.uint8)

            # Apply curvature darkening
            curvature = self.panel_curvature.get(panel_id)
            if curvature is not None:
                curvature_darkening = 1.0 - curvature * 0.2
                pixels[:, :, :3] = (pixels[:, :, :3].astype(np.float32) * curvature_darkening[:, :, np.newaxis]).astype(np.uint8)

            self.panel_pixels[panel_id] = pixels

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def generate_garment(spec: ClothingSpec, solver_result: SolverResult) -> Dict[str, np.ndarray]:
    """Convenience function."""
    engine = ProceduralGarmentEngine(spec, solver_result)
    return engine.generate()
