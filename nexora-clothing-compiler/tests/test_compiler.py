"""
Test script for NEXORA Clothing Compiler.
Verifies all components work end-to-end.
"""

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.compiler.dsl_schema import ClothingSpec, EXAMPLE_SPEC
from src.compiler.uv_constraint_graph import build_uv_graph, EdgePosition
from src.engine.template_generator import ProceduralTemplateGenerator, generate_roblox_template


def test_dsl_schema():
    """Test DSL schema parsing and serialization."""
    print("\n" + "=" * 50)
    print("TEST 1: DSL Schema")
    print("=" * 50)
    
    # Test parsing from dict
    spec = ClothingSpec.from_dict(EXAMPLE_SPEC)
    assert spec.version == "1.0"
    assert spec.name == "Gangster Hoodie"
    assert spec.theme == "gangster"
    assert spec.garment.garment_type.value == "shirt"
    assert spec.garment.hood == True
    assert spec.garment.zipper.style.value == "full"
    assert spec.garment.pocket.style.value == "kangaroo"
    assert spec.garment.logo.motif == "skull"
    assert "chain" in spec.garment.extras
    
    # Test serialization
    serialized = spec.to_dict()
    assert serialized["name"] == "Gangster Hoodie"
    assert serialized["garment"]["hood"] == True
    assert serialized["garment"]["zipper"]["style"] == "full"
    
    print("✓ DSL parsing: PASS")
    print("✓ DSL serialization: PASS")
    print(f"✓ Parsed spec: {spec.name} ({spec.theme})")
    
    return spec


def test_uv_constraint_graph(spec):
    """Test UV constraint graph construction."""
    print("\n" + "=" * 50)
    print("TEST 2: UV Constraint Graph")
    print("=" * 50)
    
    graph = build_uv_graph(spec.garment.garment_type.value)
    
    # Verify panels exist
    assert len(graph.panels) > 0
    print(f"✓ Panels created: {len(graph.panels)}")
    
    # Verify constraints exist
    assert len(graph.constraints) > 0
    print(f"✓ Constraints created: {len(graph.constraints)}")
    
    # Verify locked edges
    locked = graph.get_locked_edges()
    print(f"✓ Locked edges: {len(locked)}")
    
    # Verify shared edges
    shared = graph.get_shared_edges()
    print(f"✓ Shared edge pairs: {len(shared)}")
    
    # Print panel details
    print(f"\nPanel details:")
    for pid, panel in list(graph.panels.items())[:4]:
        edges = list(panel.edges.keys())
        print(f"  {pid}: {panel.name} at {panel.template_position}, edges={[e.value for e in edges]}")
    
    return graph


def test_template_generation(spec):
    """Test template generation."""
    print("\n" + "=" * 50)
    print("TEST 3: Template Generation")
    print("=" * 50)
    
    generator = ProceduralTemplateGenerator(spec)
    template = generator.generate_template()
    
    # Verify template properties
    assert template.size == (512, 512)
    print(f"✓ Template size: {template.size}")
    
    assert template.mode == "RGBA"
    print(f"✓ Template mode: {template.mode}")
    
    # Verify content exists
    pixels = list(template.getdata())
    non_empty = sum(1 for p in pixels if p[3] > 0)
    coverage = non_empty / len(pixels)
    print(f"✓ Coverage: {coverage:.1%}")
    
    # Save template
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "test_template.png")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    generator.save(output_path)
    
    # Verify file exists
    assert os.path.exists(output_path)
    file_size = os.path.getsize(output_path)
    print(f"✓ File saved: {output_path} ({file_size:,} bytes)")
    
    return template


def test_convenience_function():
    """Test the convenience function."""
    print("\n" + "=" * 50)
    print("TEST 4: Convenience Function")
    print("=" * 50)
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "convenience_test.png")
    template = generate_roblox_template(ClothingSpec.from_dict(EXAMPLE_SPEC), output_path)
    
    assert template.size == (512, 512)
    assert os.path.exists(output_path)
    print(f"✓ Convenience function works: {output_path}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("NEXORA Clothing Compiler - Integration Tests")
    print("=" * 60)
    
    try:
        spec = test_dsl_schema()
        test_uv_constraint_graph(spec)
        test_template_generation(spec)
        test_convenience_function()
        
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
