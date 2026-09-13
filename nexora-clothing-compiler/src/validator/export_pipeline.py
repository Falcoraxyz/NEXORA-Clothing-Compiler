"""
Roblox Export Pipeline
Complete workflow: generate → upload → apply → screenshot → validate
Uses NEXORA MCP bridge to communicate with Roblox Studio.
"""

import os
import sys
import json
import time
import base64
import requests
from typing import Dict, Optional, Tuple
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.compiler.dsl_schema import ClothingSpec, EXAMPLE_SPEC, EXAMPLE_TSHIRT_SPEC, EXAMPLE_PANTS_SPEC
from main import compile_clothing


class RobloxExportPipeline:
    """
    Complete pipeline for exporting clothing to Roblox Studio.
    
    Flow:
        1. Generate template PNG
        2. Upload to Roblox as ImageAsset
        3. Apply to dummy character
        4. Take screenshot
        5. Validate result
    """
    
    MCP_ENDPOINT = "http://localhost:3783"
    
    def __init__(self, mcp_endpoint: str = None):
        self.mcp_endpoint = mcp_endpoint or self.MCP_ENDPOINT
        self.session = requests.Session()
    
    def export(self, spec: Dict, name: str = None) -> Dict:
        """
        Full export pipeline.
        
        Args:
            spec: ClothingSpec as dict
            name: Optional name for the asset
            
        Returns:
            Dict with export results
        """
        print("=" * 60)
        print("ROBLOX EXPORT PIPELINE")
        print("=" * 60)
        
        result = {
            "success": False,
            "steps": {},
        }
        
        # Step 1: Generate template
        print("\n[1/5] Generating template...")
        try:
            template_path = f"output/{name or 'template'}.png"
            os.makedirs("output", exist_ok=True)
            template = compile_clothing(spec, template_path)
            result["steps"]["generate"] = {
                "success": True,
                "path": template_path,
                "size": template.size,
            }
            print(f"  ✓ Generated: {template_path} ({template.size[0]}x{template.size[1]})")
        except Exception as e:
            result["steps"]["generate"] = {"success": False, "error": str(e)}
            print(f"  ✗ Failed: {e}")
            return result
        
        # Step 2: Upload to Roblox
        print("\n[2/5] Uploading to Roblox...")
        try:
            asset_id = self._upload_template(template_path)
            if asset_id:
                result["steps"]["upload"] = {
                    "success": True,
                    "asset_id": asset_id,
                }
                print(f"  ✓ Uploaded: rbxassetid://{asset_id}")
            else:
                result["steps"]["upload"] = {"success": False, "error": "Upload failed"}
                print("  ✗ Upload failed")
                return result
        except Exception as e:
            result["steps"]["upload"] = {"success": False, "error": str(e)}
            print(f"  ✗ Upload error: {e}")
            return result
        
        # Step 3: Apply to dummy
        print("\n[3/5] Applying to dummy...")
        try:
            self._apply_to_dummy(asset_id, spec)
            result["steps"]["apply"] = {"success": True}
            print("  ✓ Applied to dummy")
        except Exception as e:
            result["steps"]["apply"] = {"success": False, "error": str(e)}
            print(f"  ✗ Apply error: {e}")
        
        # Step 4: Screenshot
        print("\n[4/5] Taking screenshot...")
        try:
            screenshot_path = f"output/{name or 'template'}_screenshot.png"
            self._screenshot_dummy(screenshot_path)
            result["steps"]["screenshot"] = {
                "success": True,
                "path": screenshot_path,
            }
            print(f"  ✓ Screenshot: {screenshot_path}")
        except Exception as e:
            result["steps"]["screenshot"] = {"success": False, "error": str(e)}
            print(f"  ✗ Screenshot error: {e}")
        
        # Step 5: Validate
        print("\n[5/5] Validating...")
        try:
            validation = self._validate_screenshot(screenshot_path)
            result["steps"]["validate"] = {
                "success": True,
                "metrics": validation,
            }
            print(f"  ✓ Validation complete")
        except Exception as e:
            result["steps"]["validate"] = {"success": False, "error": str(e)}
            print(f"  ✗ Validation error: {e}")
        
        result["success"] = all(
            step.get("success", False) 
            for step in result["steps"].values()
        )
        
        print(f"\n{'=' * 60}")
        print(f"EXPORT {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"{'=' * 60}")
        
        return result
    
    def _upload_template(self, template_path: str) -> Optional[str]:
        """Upload PNG to Roblox as ImageAsset."""
        with open(template_path, "rb") as f:
            png_data = base64.b64encode(f.read()).decode()
        
        response = self.session.post(
            f"{self.mcp_endpoint}/mcp",
            json={
                "method": "manage_assets",
                "params": {
                    "action": "load_asset",
                    "texture": png_data,
                    "asset_type": "image",
                }
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("asset_id")
        
        return None
    
    def _apply_to_dummy(self, asset_id: str, spec: Dict):
        """Apply the shirt texture to a dummy character."""
        garment_type = spec.get("garment", {}).get("type", "shirt")
        
        # Map garment type to Roblox class
        class_map = {
            "shirt": "Shirt",
            "tshirt": "ShirtGraphic",
            "pants": "Pants",
        }
        class_name = class_map.get(garment_type, "Shirt")
        
        # Property name for the texture
        property_map = {
            "Shirt": "ShirtTemplate",
            "ShirtGraphic": "Graphic",
            "Pants": "PantsTemplate",
        }
        property_name = property_map.get(class_name, "ShirtTemplate")
        
        luau_code = f'''
            local dummy = Workspace:FindFirstChildOfClass("Model")
            if dummy then
                local garment = dummy:FindFirstChildOfClass("{class_name}")
                if not garment then
                    garment = Instance.new("{class_name}")
                    garment.Parent = dummy
                end
                garment.{property_name} = "rbxassetid://{asset_id}"
            end
        '''
        
        response = self.session.post(
            f"{self.mcp_endpoint}/mcp",
            json={
                "method": "execute_luau",
                "params": {"source": luau_code}
            },
            timeout=30,
        )
        
        return response.status_code == 200
    
    def _screenshot_dummy(self, output_path: str):
        """Take a screenshot of the dummy."""
        # Position camera
        luau_code = '''
            local camera = Workspace.CurrentCamera
            if camera then
                camera.CameraType = "Scriptable"
                local dummy = Workspace:FindFirstChildOfClass("Model")
                if dummy then
                    local root = dummy:FindFirstChild("HumanoidRootPart")
                    if root then
                        camera.CFrame = CFrame.new(root.Position + Vector3.new(0, 2, 5), root.Position)
                    end
                end
            end
        '''
        
        self.session.post(
            f"{self.mcp_endpoint}/mcp",
            json={
                "method": "execute_luau",
                "params": {"source": luau_code}
            },
            timeout=30,
        )
        
        # Wait for render
        time.sleep(1)
        
        # Capture screenshot
        luau_code = '''
            local camera = Workspace.CurrentCamera
            if camera then
                return camera:GetScreen()
            end
            return nil
        '''
        
        response = self.session.post(
            f"{self.mcp_endpoint}/mcp",
            json={
                "method": "execute_luau",
                "params": {"source": luau_code}
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            img_data = base64.b64decode(result.get("image", ""))
            with open(output_path, "wb") as f:
                f.write(img_data)
    
    def _validate_screenshot(self, screenshot_path: str) -> Dict:
        """Validate the screenshot."""
        screenshot = Image.open(screenshot_path)
        screenshot_np = np.array(screenshot)
        
        # Basic metrics
        coverage = np.sum(screenshot_np[:, :, 3] > 0) / (screenshot_np.shape[0] * screenshot_np.shape[1])
        
        return {
            "coverage": coverage,
            "size": screenshot.size,
        }


def export_to_roblox(spec: Dict, name: str = None) -> Dict:
    """Convenience function."""
    pipeline = RobloxExportPipeline()
    return pipeline.export(spec, name)


if __name__ == "__main__":
    # Test export
    result = export_to_roblox(EXAMPLE_SPEC, "gangster_hoodie")
    print(json.dumps(result, indent=2))
