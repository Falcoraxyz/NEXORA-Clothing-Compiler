"""
Test script for NEXORA Clothing Compiler v2.
Verifies all components work end-to-end.
"""

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.compiler.dsl_schema import ClothingSpec, EXAMPLE_SPEC
from src.compiler.uv_constraint_graph import build_uv_graph, EdgePosition
from src.compiler.constraint_solver import ConstraintSolver, solve_constraints
from src.engine.garment_engine import ProceduralGarmentEngine
from src.engine.material_composer import MaterialComposer
from src.engine.seam_solver import SeamSolver
from src.validator.vision_metrics import VisionMetrics
from main import compile_clothing_v2, hex_to_rgb


def test_dsl_schema():
    """Test DSL schema parsing and serialization."""
    print("\n" + "=" * 50)
    print("TEST 1: DSL Schema")
    print("=" * 50)
    
    spec = ClothingSpec.from_dict(EXAMPLE_SPEC)
    assert spec.version == "1.0"
    assert spec.name == "Gangster Hoodie"
    assert spec.garment.hood == True
    assert spec.garment.zipper.style.value == "full"
    
    serialized = spec.to_dict()
    assert serialized["name"] == "Gangster Hoodie"
    
    print("✓ DSL parsing: PASS")
    print("✓ DSL serialization: PASS")
    return spec


def test_constraint_solver(spec):
    """Test constraint solver."""
    print("\n" + "=" * 50)
    print("TEST 2: Constraint Solver")
    print("=" * 50)
    
    solver = ConstraintSolver(spec)
    result = solver.solve()
    
    assert len(result.panel_constraints) > 0
    assert len(result.edge_constraints) > 0
    assert result.template_size == (512, 512)
    
    print(f"✓ Panels: {len(result.panel_constraints)}")
    print(f"✓ Edge constraints: {len(result.edge_constraints)}")
    print(f"✓ Template size: {result.template_size}")
    print(f"✓ Global constraints: {list(result.global_constraints.keys())}")
    
    return result


def test_garment_engine(spec, solver_result):
    """Test procedural garment engine."""
    print("\n" + "=" * 50)
    print("TEST 3: Procedural Garment Engine")
    print("=" * 50)
    
    engine = ProceduralGarmentEngine(spec, solver_result)
    panel_pixels = engine.generate()
    
    assert len(panel_pixels) > 0
    for pid, pixels in panel_pixels.items():
        assert pixels.shape[0] == 128
        assert pixels.shape[1] == 128
        assert pixels.shape[2] == 4  # RGBA
    
    print(f"✓ Generated: {len(panel_pixels)} panels")
    print(f"✓ Panel size: {list(panel_pixels.values())[0].shape}")
    
    return panel_pixels


def test_material_composer(spec, solver_result, panel_pixels):
    """Test material composer."""
    print("\n" + "=" * 50)
    print("TEST 4: Material Composer")
    print("=" * 50)
    
    composer = MaterialComposer(spec, solver_result, panel_pixels)
    template = composer.compose()
    
    assert template.size == (512, 512)
    assert template.mode == "RGBA"
    
    print(f"✓ Template size: {template.size}")
    print(f"✓ Template mode: {template.mode}")
    
    return template


def test_seam_solver(solver_result, panel_pixels):
    """Test seam solver."""
    print("\n" + "=" * 50)
    print("TEST 5: Seam Solver")
    print("=" * 50)
    
    solver = SeamSolver(solver_result, panel_pixels)
    solved_pixels = solver.solve()
    
    assert len(solved_pixels) > 0
    print(f"✓ Solved: {len(solved_pixels)} panels")
    
    return solved_pixels


def test_vision_metrics(template, solver_result, spec):
    """Test vision metrics."""
    print("\n" + "=" * 50)
    print("TEST 6: Vision Metrics")
    print("=" * 50)
    
    composer = MaterialComposer(spec, solver_result, {})
    metrics = VisionMetrics()
    
    report = metrics.full_report(
        template,
        composer.panel_positions,
        solver_result.edge_constraints,
        hex_to_rgb(spec.garment.color.primary),
    )
    
    print(f"✓ Coverage: {report['coverage']:.1%}")
    print(f"✓ Color accuracy: {report['color_accuracy']:.1%}")
    if report['seam_continuity']:
        print(f"✓ Seam checks: {len(report['seam_continuity'])}")
    print(f"✓ Overall: {'PASS' if report['pass'] else 'FAIL'}")
    
    return report


def test_full_pipeline():
    """Test the full v2 pipeline."""
    print("\n" + "=" * 50)
    print("TEST 7: Full Pipeline (v2)")
    print("=" * 50)
    
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output", "full_pipeline_test.png"
    )
    
    template = compile_clothing_v2(EXAMPLE_SPEC, output_path)
    
    assert template.size == (512, 512)
    assert os.path.exists(output_path)
    
    print(f"✓ Full pipeline: PASS")
    print(f"✓ Output: {output_path}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("NEXORA Clothing Compiler v2 - Integration Tests")
    print("=" * 60)
    
    try:
        spec = test_dsl_schema()
        solver_result = test_constraint_solver(spec)
        panel_pixels = test_garment_engine(spec, solver_result)
        template = test_material_composer(spec, solver_result, panel_pixels)
        test_seam_solver(solver_result, panel_pixels)
        test_vision_metrics(template, solver_result, spec)
        test_full_pipeline()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
