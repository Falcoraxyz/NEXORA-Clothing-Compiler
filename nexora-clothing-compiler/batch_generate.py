"""
Batch Generator
Generate multiple clothing templates from a list of specs.
"""

import os
import sys
import json
from typing import List, Dict, Any
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.compiler.dsl_schema import ClothingSpec, EXAMPLE_SPEC, EXAMPLE_TSHIRT_SPEC, EXAMPLE_PANTS_SPEC
from main import compile_clothing


class BatchGenerator:
    """Generate multiple clothing templates in one run."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.results = []
    
    def generate_batch(self, specs: List[Dict[str, Any]]) -> List[Dict]:
        """
        Generate templates from a list of specs.
        
        Args:
            specs: List of dicts with 'name', 'spec', and optional 'filename'
        
        Returns:
            List of results with paths and status
        """
        print(f"\n{'=' * 60}")
        print(f"BATCH GENERATION: {len(specs)} items")
        print(f"{'=' * 60}\n")
        
        for i, item in enumerate(specs, 1):
            name = item.get("name", f"item_{i}")
            spec = item.get("spec", {})
            filename = item.get("filename", f"{name.lower().replace(' ', '_')}.png")
            output_path = os.path.join(self.output_dir, filename)
            
            print(f"\n[{i}/{len(specs)}] Generating: {name}")
            print("-" * 40)
            
            try:
                template = compile_clothing(spec, output_path)
                self.results.append({
                    "name": name,
                    "path": output_path,
                    "size": template.size,
                    "status": "success"
                })
            except Exception as e:
                print(f"  ERROR: {e}")
                self.results.append({
                    "name": name,
                    "path": None,
                    "size": None,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Summary
        print(f"\n{'=' * 60}")
        print("BATCH SUMMARY")
        print(f"{'=' * 60}")
        success = sum(1 for r in self.results if r["status"] == "success")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        print(f"  Success: {success}")
        print(f"  Failed: {failed}")
        for r in self.results:
            status = "✓" if r["status"] == "success" else "✗"
            print(f"  {status} {r['name']}")
        
        return self.results


# Predefined batch presets
BATCH_PRESETS = [
    {
        "name": "Gangster Hoodie",
        "spec": EXAMPLE_SPEC,
        "filename": "gangster_hoodie.png"
    },
    {
        "name": "Band Tee",
        "spec": EXAMPLE_TSHIRT_SPEC,
        "filename": "band_tee.png"
    },
    {
        "name": "Cargo Pants",
        "spec": EXAMPLE_PANTS_SPEC,
        "filename": "cargo_pants.png"
    },
]


def run_batch():
    """Run batch generation with presets."""
    generator = BatchGenerator()
    return generator.generate_batch(BATCH_PRESETS)


if __name__ == "__main__":
    run_batch()
