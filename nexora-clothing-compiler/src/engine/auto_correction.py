"""
Auto Correction Loop
Implements closed-loop feedback: detect failing panels, re-render only those panels.
"""

import os
import sys
import time
from typing import Dict, List, Tuple, Optional
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.compiler.dsl_schema import ClothingSpec
from src.compiler.constraint_solver import SolverResult
from src.engine.garment_engine import ProceduralGarmentEngine
from src.engine.material_composer import MaterialComposer
from src.engine.seam_solver import SeamSolver
from src.validator.vision_metrics import VisionMetrics


class AutoCorrectionLoop:
    """
    Closed-loop correction system.
    
    Flow:
        1. Generate template
        2. Validate (SSIM per edge)
        3. If edge fails → identify affected panels
        4. Re-render only those panels
        5. Re-compose
        6. Re-validate
        7. Repeat until all edges pass (or max iterations)
    """

    def __init__(self, spec: ClothingSpec, solver_result: SolverResult,
                 max_iterations: int = 5):
        self.spec = spec
        self.solver = solver_result
        self.max_iterations = max_iterations
        self.iteration = 0
        
        # Track which panels need re-render
        self.panels_to_fix: set = set()
        self.history: List[Dict] = []
        
        # Panel positions (standard Roblox shirt layout)
        self.panel_positions = self._get_panel_positions()

    def run(self) -> Dict:
        """
        Run the auto-correction loop.
        Returns the final template and report.
        """
        print("[AutoCorrection] Starting closed-loop correction...")
        print(f"  Max iterations: {self.max_iterations}")
        
        # Step 1: Initial generation
        print(f"\n--- Iteration 0 (Initial) ---")
        panel_pixels = self._generate_garment()
        self._compose_seams_and_save(panel_pixels)
        
        # Step 2: Validate
        report = self._validate(panel_pixels)
        self.history.append({
            "iteration": 0,
            "report": report,
            "panels_fixed": [],
        })
        
        # Step 3: Loop until pass or max iterations
        while not report["pass"] and self.iteration < self.max_iterations:
            self.iteration += 1
            print(f"\n--- Iteration {self.iteration} ---")
            
            # Identify panels to fix
            self.panels_to_fix = self._identify_failing_panels(report)
            
            if not self.panels_to_fix:
                print("  No panels to fix (validation issue unknown)")
                break
            
            print(f"  Panels to fix: {self.panels_to_fix}")
            
            # Re-render only failing panels
            panel_pixels = self._regenerate_panels(panel_pixels, self.panels_to_fix)
            
            # Re-compose
            self._compose_seams_and_save(panel_pixels)
            
            # Re-validate
            report = self._validate(panel_pixels)
            self.history.append({
                "iteration": self.iteration,
                "report": report,
                "panels_fixed": list(self.panels_to_fix),
            })
        
        # Final report
        print(f"\n--- Final Result ---")
        print(f"  Iterations: {self.iteration}")
        print(f"  Pass: {report['pass']}")
        print(f"  Coverage: {report['coverage']:.1%}")
        print(f"  Color accuracy: {report['color_accuracy']:.1%}")
        if report["seam_continuity"]:
            failed = [k for k, v in report["seam_continuity"].items() if not v["pass"]]
            print(f"  Failed seams: {len(failed)}")
            for edge_key in failed:
                print(f"    {edge_key}: {report['seam_continuity'][edge_key]['similarity']:.2f}")
        
        return {
            "template": self._get_current_template(),
            "report": report,
            "iterations": self.iteration,
            "history": self.history,
        }

    def _generate_garment(self) -> Dict[str, np.ndarray]:
        """Generate garment pixel data."""
        engine = ProceduralGarmentEngine(self.spec, self.solver)
        return engine.generate()

    def _compose_seams_and_save(self, panel_pixels: Dict[str, np.ndarray]):
        """Compose materials, solve seams, update stored pixels."""
        # Compose decorations + stitches
        composer = MaterialComposer(self.spec, self.solver, panel_pixels)
        template = composer.compose()
        
        # Extract pixels back
        panel_pixels.update(self._extract_panel_pixels(template))
        
        # Solve seams
        seam_solver = SeamSolver(self.solver, panel_pixels)
        solved_pixels = seam_solver.solve()
        
        # Re-compose with solved seams
        composer = MaterialComposer(self.spec, self.solver, solved_pixels)
        self._current_template = composer.compose()
        
        # Update stored pixels
        self._current_pixels = self._extract_panel_pixels(self._current_template)

    def _validate(self, panel_pixels: Dict[str, np.ndarray]) -> Dict:
        """Run vision metrics validation."""
        if self._current_template is None:
            composer = MaterialComposer(self.spec, self.solver, panel_pixels)
            self._current_template = composer.compose()
        
        metrics = VisionMetrics()
        return metrics.full_report(
            self._current_template,
            self.panel_positions,
            self.solver.edge_constraints,
            self._hex_to_rgb(self.spec.garment.color.primary),
        )

    def _identify_failing_panels(self, report: Dict) -> set:
        """Identify which panels need re-rendering based on failed edges."""
        failing_panels = set()
        
        for edge_key, seam in report.get("seam_continuity", {}).items():
            if not seam["pass"]:
                # Parse edge key: "panelA.edgeA-panelB.edgeB"
                parts = edge_key.split("-")
                if len(parts) == 2:
                    panel_a = parts[0].split(".")[0]
                    panel_b = parts[1].split(".")[0]
                    failing_panels.add(panel_a)
                    failing_panels.add(panel_b)
        
        # Also check for other issues
        if report["coverage"] < 0.5:
            # Low coverage → regenerate all panels
            failing_panels.update(self.solver.panel_constraints.keys())
        
        return failing_panels

    def _regenerate_panels(self, existing_pixels: Dict[str, np.ndarray],
                           panels_to_fix: set) -> Dict[str, np.ndarray]:
        """Re-render only the specified panels, keep others unchanged."""
        new_pixels = existing_pixels.copy()
        
        for panel_id in panels_to_fix:
            if panel_id not in self.solver.panel_constraints:
                continue
            
            print(f"    Regenerating: {panel_id}")
            
            # Regenerate single panel with variation
            pc = self.solver.panel_constraints[panel_id]
            primary = self._hex_to_rgb(self.spec.garment.color.primary)
            
            # Create new panel with slight variation
            h, w = 128, 128
            panel_img = np.zeros((h, w, 4), dtype=np.uint8)
            
            # Base color
            panel_img[:, :, 0] = primary[0]
            panel_img[:, :, 1] = primary[1]
            panel_img[:, :, 2] = primary[2]
            panel_img[:, :, 3] = 255
            
            # Apply constraints (color fill, material, folds)
            for constraint in pc.constraints:
                if constraint["type"] == "color_fill":
                    params = constraint["params"]
                    fabric = params.get("fabric", "heavy_cotton")
                    noise_intensity = params.get("noise_intensity", 0.05)
                    
                    # Different seed for variation
                    np.random.seed(hash(panel_id) + self.iteration)
                    noise = np.random.randint(-15, 15, (h, w, 3), dtype=np.int16)
                    panel_img[:, :, :3] = np.clip(
                        panel_img[:, :, :3].astype(np.int16) + noise, 0, 255
                    ).astype(np.uint8)
                
                elif constraint["type"] == "material_props":
                    params = constraint["params"]
                    ao_radius = params.get("ao_radius", 8)
                    ao_intensity = params.get("ao_edge_darkening", 0.3)
                    
                    # Apply AO
                    ao = np.ones((h, w), dtype=np.float32)
                    for i in range(h):
                        for j in range(w):
                            dist = min(i, j, h - 1 - i, w - 1 - j)
                            if dist < ao_radius:
                                ao[i, j] = 1.0 - (ao_radius - dist) / ao_radius * ao_intensity
                    
                    panel_img[:, :, :3] = (panel_img[:, :, :3].astype(np.float32) * ao[:, :, np.newaxis]).astype(np.uint8)
            
            # Apply boundary constraints (copy from existing adjacent panels)
            for edge_constraint in self.solver.edge_constraints:
                if edge_constraint["type"] != "boundary_match":
                    continue
                
                panel_a = edge_constraint["edge_a"]["panel"]
                edge_a = edge_constraint["edge_a"]["edge"]
                panel_b = edge_constraint["edge_b"]["panel"]
                edge_b = edge_constraint["edge_b"]["edge"]
                
                if panel_id == panel_a and panel_b not in panels_to_fix:
                    # Copy edge from B (which is already good)
                    edge_data = self._get_edge_pixels(new_pixels.get(panel_b), edge_b)
                    if edge_data is not None:
                        self._set_edge_pixels(panel_img, edge_a, edge_data)
                
                elif panel_id == panel_b and panel_a not in panels_to_fix:
                    # Copy edge from A (which is already good)
                    edge_data = self._get_edge_pixels(new_pixels.get(panel_a), edge_a)
                    if edge_data is not None:
                        self._set_edge_pixels(panel_img, edge_b, edge_data)
            
            new_pixels[panel_id] = panel_img
        
        return new_pixels

    def _get_edge_pixels(self, pixels: Optional[np.ndarray], edge_name: str) -> Optional[np.ndarray]:
        """Get edge pixel data."""
        if pixels is None:
            return None
        h, w, c = pixels.shape
        if edge_name == "top":
            return pixels[0, :, :].copy()
        elif edge_name == "bottom":
            return pixels[h - 1, :, :].copy()
        elif edge_name == "left":
            return pixels[:, 0, :].copy()
        elif edge_name == "right":
            return pixels[:, w - 1, :].copy()
        return None

    def _set_edge_pixels(self, pixels: np.ndarray, edge_name: str, data: np.ndarray):
        """Set edge pixel data."""
        h, w, c = pixels.shape
        if edge_name == "top":
            pixels[0, :, :] = data
        elif edge_name == "bottom":
            pixels[h - 1, :, :] = data
        elif edge_name == "left":
            pixels[:, 0, :] = data
        elif edge_name == "right":
            pixels[:, w - 1, :] = data

    def _extract_panel_pixels(self, template: Image.Image) -> Dict[str, np.ndarray]:
        """Extract panel pixels from template."""
        template_np = np.array(template)
        panel_size = 128
        layout = [
            ("back_left", 0, 0), ("top_left", 128, 0), ("front_left", 256, 0), ("bottom_left", 384, 0),
            ("back_right", 0, 128), ("top_right", 128, 128), ("front_right", 256, 128), ("bottom_right", 384, 128),
            ("left_sleeve_top", 0, 256), ("left_sleeve_bottom", 128, 256),
            ("right_sleeve_top", 256, 256), ("right_sleeve_bottom", 384, 256),
        ]
        
        pixels = {}
        for panel_id, x, y in layout:
            if y + panel_size <= template_np.shape[0] and x + panel_size <= template_np.shape[1]:
                pixels[panel_id] = template_np[y:y+panel_size, x:x+panel_size].copy()
        
        return pixels

    def _get_current_template(self) -> Optional[Image.Image]:
        return getattr(self, "_current_template", None)

    def _get_panel_positions(self) -> Dict[str, Tuple[int, int, int, int]]:
        """Get panel positions in template."""
        panel_size = 128
        positions = {}
        layout = [
            ("back_left", 0, 0), ("top_left", 128, 0), ("front_left", 256, 0), ("bottom_left", 384, 0),
            ("back_right", 0, 128), ("top_right", 128, 128), ("front_right", 256, 128), ("bottom_right", 384, 128),
            ("left_sleeve_top", 0, 256), ("left_sleeve_bottom", 128, 256),
            ("right_sleeve_top", 256, 256), ("right_sleeve_bottom", 384, 256),
        ]
        for panel_id, x, y in layout:
            positions[panel_id] = (x, y, panel_size, panel_size)
        return positions

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def run_auto_correction(spec: ClothingSpec, solver_result: SolverResult,
                        output_path: str = None) -> Dict:
    """Run auto-correction loop."""
    loop = AutoCorrectionLoop(spec, solver_result)
    result = loop.run()
    
    if output_path and result["template"]:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result["template"].save(output_path)
        print(f"\n  Saved: {output_path}")
    
    return result
