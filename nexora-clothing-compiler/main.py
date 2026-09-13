"""
Main entry point for NEXORA Clothing Compiler v2.0
Orchestrates the full pipeline: DSL → Solver → Engine → Composer → Seams → Validate
"""

import os
import sys
import json
from PIL import Image
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.compiler.dsl_schema import ClothingSpec, EXAMPLE_SPEC
from src.compiler.constraint_solver import ConstraintSolver, solve_constraints
from src.compiler.uv_constraint_graph import build_uv_graph
from src.engine.garment_engine import ProceduralGarmentEngine, generate_garment
from src.engine.material_composer import MaterialComposer, compose_materials
from src.engine.seam_solver import SeamSolver, solve_seams
from src.validator.vision_metrics import VisionMetrics, evaluate_template


def compile_clothing_v2(dsl_json: dict, output_path: str = None) -> Image.Image:
    """
    Compile a clothing specification into a Roblox template PNG (v2).
    
    Pipeline:
        DSL JSON → ClothingSpec → Constraint Solver → Garment Engine →
        Material Composer → Seam Solver → Vision Metrics → PNG
    
    Args:
        dsl_json: Clothing specification as dict (from LLM)
        output_path: Optional path to save the PNG
    
    Returns:
        PIL Image of the generated template
    """
    print("=" * 60)
    print("NEXORA Clothing Compiler v2.0")
    print("=" * 60)
    
    # Step 1: Parse DSL
    print(f"\n[1/6] Parsing Clothing DSL...")
    spec = ClothingSpec.from_dict(dsl_json)
    print(f"  Name: {spec.name}")
    print(f"  Theme: {spec.theme}")
    print(f"  Garment: {spec.garment.garment_type.value}")
    print(f"  Fit: {spec.garment.fit}")
    print(f"  Color: {spec.garment.color.primary}")
    print(f"  Material: {spec.garment.material.fabric.value}")
    print(f"  Zipper: {spec.garment.zipper.style.value}")
    print(f"  Pocket: {spec.garment.pocket.style.value}")
    print(f"  Stitch: {spec.garment.stitch.type.value}")
    print(f"  Hood: {spec.garment.hood}")
    if spec.garment.logo:
        print(f"  Logo: {spec.garment.logo.motif} ({spec.garment.logo.style.value})")
    if spec.garment.extras:
        print(f"  Extras: {', '.join(spec.garment.extras)}")
    
    # Step 2: Solve constraints
    print(f"\n[2/6] Solving constraints...")
    solver_result = solve_constraints(spec)
    print(f"  Panels: {len(solver_result.panel_constraints)}")
    print(f"  Edge constraints: {len(solver_result.edge_constraints)}")
    
    # Step 3: Generate garment geometry
    print(f"\n[3/6] Generating garment geometry...")
    engine = ProceduralGarmentEngine(spec, solver_result)
    panel_pixels = engine.generate()
    print(f"  Generated: {len(panel_pixels)} panels")
    
    # Step 4: Compose materials
    print(f"\n[4/6] Composing materials...")
    composer = MaterialComposer(spec, solver_result, panel_pixels)
    template = composer.compose()
    
    # Step 5: Solve seams
    print(f"\n[5/6] Solving seams...")
    # Re-extract pixels from template after decoration
    panel_pixels = extract_panel_pixels(template, solver_result)
    seam_solver = SeamSolver(solver_result, panel_pixels)
    panel_pixels = seam_solver.solve()
    # Re-compose with solved seams
    composer = MaterialComposer(spec, solver_result, panel_pixels)
    template = composer.compose()
    
    # Step 6: Validate
    print(f"\n[6/6] Validating...")
    metrics = VisionMetrics()
    panel_positions = composer.panel_positions
    report = metrics.full_report(
        template, 
        panel_positions,
        solver_result.edge_constraints,
        hex_to_rgb(spec.garment.color.primary),
    )
    
    print(f"  Coverage: {report['coverage']:.1%}")
    print(f"  Color accuracy: {report['color_accuracy']:.1%}")
    if report['seam_continuity']:
        for edge_key, seam in report['seam_continuity'].items():
            status = "✓" if seam['pass'] else "✗"
            print(f"  {status} {edge_key}: {seam['similarity']:.2f}")
    print(f"  Overall: {'PASS' if report['pass'] else 'FAIL'}")
    
    # Save
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        template.save(output_path)
        print(f"\n  Saved: {output_path}")
    
    print(f"\n{'=' * 60}")
    return template


def extract_panel_pixels(template: Image.Image, solver_result) -> dict:
    """Extract pixel data per panel from template."""
    panel_size = solver_result.global_constraints.get("panel_size", 128)
    template_np = np.array(template)
    
    # Standard layout
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
    
    pixels = {}
    for panel_id, x, y in layout:
        if y + panel_size <= template_np.shape[0] and x + panel_size <= template_np.shape[1]:
            pixels[panel_id] = template_np[y:y+panel_size, x:x+panel_size].copy()
    
    return pixels


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def main():
    """Run the v2 compiler with example spec."""
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output", "gangster_hoodie_v2.png"
    )
    
    # Use the example spec
    dsl_json = EXAMPLE_SPEC
    
    # Compile
    template = compile_clothing_v2(dsl_json, output_path)
    
    print(f"\nTemplate saved to: {output_path}")
    return template


if __name__ == "__main__":
    main()
