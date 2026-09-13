"""
Test Auto Correction Loop.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.compiler.dsl_schema import EXAMPLE_SPEC, ClothingSpec
from src.compiler.constraint_solver import solve_constraints
from src.engine.auto_correction import AutoCorrectionLoop, run_auto_correction


def test_auto_correction():
    """Test the auto-correction loop."""
    print("\n" + "=" * 50)
    print("TEST: Auto Correction Loop")
    print("=" * 50)
    
    spec = ClothingSpec.from_dict(EXAMPLE_SPEC)
    solver_result = solve_constraints(spec)
    
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output", "auto_corrected.png"
    )
    
    result = run_auto_correction(spec, solver_result, output_path)
    
    assert result["template"] is not None
    assert result["iterations"] >= 0
    
    print(f"✓ Iterations: {result['iterations']}")
    print(f"✓ Pass: {result['report']['pass']}")
    print(f"✓ History: {len(result['history'])} entries")
    
    return result


def main():
    print("\n" + "=" * 60)
    print("Auto Correction Loop Test")
    print("=" * 60)
    
    try:
        test_auto_correction()
        
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
