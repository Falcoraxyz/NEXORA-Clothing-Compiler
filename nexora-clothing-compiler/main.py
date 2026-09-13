"""
Main entry point for NEXORA Clothing Compiler v2.1
Uses official Roblox template layout (585×559)
"""

import os
import sys
import json
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.compiler.dsl_schema import ClothingSpec, EXAMPLE_SPEC, EXAMPLE_TSHIRT_SPEC, EXAMPLE_PANTS_SPEC
from src.compiler.constraint_solver import ConstraintSolver, solve_constraints
from src.compiler.uv_constraint_graph import build_uv_graph
from src.engine.template_generator import ProceduralTemplateGeneratorV2, generate_roblox_template_v2
from src.validator.vision_metrics import VisionMetrics


def compile_clothing(dsl_json: dict, output_path: str = None) -> Image.Image:
    """
    Compile a clothing specification into a Roblox template PNG.
    Uses official Roblox template layout (585×559).
    """
    print("=" * 60)
    print("NEXORA Clothing Compiler v2.1 (Official Template)")
    print("=" * 60)
    
    # Step 1: Parse DSL
    print(f"\n[1/5] Parsing Clothing DSL...")
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
    print(f"\n[2/5] Solving constraints...")
    solver_result = solve_constraints(spec)
    print(f"  Template size: {solver_result.template_size}")
    print(f"  Panels: {len(solver_result.panel_constraints)}")
    print(f"  Edge constraints: {len(solver_result.edge_constraints)}")
    
    # Step 3: Generate template
    print(f"\n[3/5] Generating template...")
    template = generate_roblox_template_v2(spec, solver_result, output_path)
    
    # Step 4: Validate
    print(f"\n[4/5] Validating...")
    metrics = VisionMetrics()
    
    # Build panel positions from graph
    graph = build_uv_graph(spec.garment.garment_type.value)
    panel_positions = {}
    for pid, panel in graph.panels.items():
        panel_positions[pid] = panel.template_position
    
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
    
    # Step 5: Report
    print(f"\n[5/5] Report:")
    print(f"  Template size: {template.size}")
    print(f"  Output path: {output_path or 'N/A'}")
    if report['pass']:
        print(f"  Status: ✓ READY FOR ROBLOX STUDIO")
    else:
        print(f"  Status: ⚠ NEEDS REVISION")
    
    print(f"\n{'=' * 60}")
    return template


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def main():
    """Run the compiler with example specs."""
    results = {}
    
    # Test Shirt
    print("=" * 60)
    print("TEST 1: Shirt (Gangster Hoodie)")
    print("=" * 60)
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output", "gangster_hoodie_v2.png"
    )
    template = compile_clothing(EXAMPLE_SPEC, output_path)
    results["shirt"] = output_path
    
    # Test T-Shirt
    print("\n" + "=" * 60)
    print("TEST 2: T-Shirt (Band Tee)")
    print("=" * 60)
    output_path2 = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output", "band_tee.png"
    )
    template2 = compile_clothing(EXAMPLE_TSHIRT_SPEC, output_path2)
    results["tshirt"] = output_path2
    
    # Test Pants
    print("\n" + "=" * 60)
    print("TEST 3: Pants (Cargo Pants)")
    print("=" * 60)
    output_path3 = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output", "cargo_pants.png"
    )
    template3 = compile_clothing(EXAMPLE_PANTS_SPEC, output_path3)
    results["pants"] = output_path3
    
    print(f"\n\nSummary:")
    for name, path in results.items():
        print(f"  {name}: {path}")
    return results


if __name__ == "__main__":
    main()
