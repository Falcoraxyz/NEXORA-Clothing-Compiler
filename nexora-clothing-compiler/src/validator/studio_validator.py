"""
Roblox Studio Validator
Handles applying templates to Roblox Studio, screenshotting, and comparing.
Uses the NEXORA MCP bridge to communicate with Studio.
"""

import os
import json
import time
import base64
import requests
from typing import Dict, Optional, Tuple
from PIL import Image
import numpy as np


class RobloxStudioValidator:
    """
    Validates templates by applying them in Roblox Studio via MCP.
    Flow: Upload PNG → Apply Shirt → Spawn Dummy → Screenshot → Return
    """
    
    MCP_ENDPOINT = "http://localhost:3783"
    
    def __init__(self, mcp_endpoint: str = None):
        self.mcp_endpoint = mcp_endpoint or self.MCP_ENDPOINT
        self.session = requests.Session()
    
    def validate(self, template_path: str) -> Dict:
        """
        Full validation pipeline.
        Returns validation result with screenshot and metrics.
        """
        print("[StudioValidator] Starting validation pipeline...")
        
        # Step 1: Upload template to Roblox
        asset_id = self._upload_template(template_path)
        if not asset_id:
            return {"success": False, "error": "Upload failed"}
        print(f"  Uploaded: {asset_id}")
        
        # Step 2: Apply to dummy
        self._apply_to_dummy(asset_id)
        print("  Applied to dummy")
        
        # Step 3: Screenshot
        screenshot_path = self._screenshot_dummy()
        if not screenshot_path:
            return {"success": False, "error": "Screenshot failed"}
        print(f"  Screenshot: {screenshot_path}")
        
        # Step 4: Compare
        comparison = self._compare(screenshot_path)
        
        return {
            "success": True,
            "asset_id": asset_id,
            "screenshot_path": screenshot_path,
            "comparison": comparison,
        }
    
    def _upload_template(self, template_path: str) -> Optional[str]:
        """Upload PNG to Roblox as ImageAsset."""
        try:
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
        except Exception as e:
            print(f"  Upload error: {e}")
        
        return None
    
    def _apply_to_dummy(self, asset_id: str):
        """Apply the shirt texture to a dummy character."""
        try:
            self.session.post(
                f"{self.mcp_endpoint}/mcp",
                json={
                    "method": "execute_luau",
                    "params": {
                        "source": f'''
                            local dummy = Workspace:FindFirstClass("Model")
                            if dummy then
                                local shirt = dummy:FindFirstChildOfClass("Shirt")
                                if not shirt then
                                    shirt = Instance.new("Shirt")
                                    shirt.Parent = dummy
                                end
                                shirt.ShirtTemplate = "rbxassetid://{asset_id}"
                            end
                        '''
                    }
                },
                timeout=30,
            )
        except Exception as e:
            print(f"  Apply error: {e}")
    
    def _screenshot_dummy(self) -> Optional[str]:
        """Take a screenshot of the dummy."""
        try:
            response = self.session.post(
                f"{self.mcp_endpoint}/mcp",
                json={
                    "method": "execute_luau",
                    "params": {
                        "source": '''
                            local camera = Workspace.CurrentCamera
                            if camera then
                                camera.CameraType = "Scriptable"
                                local dummy = Workspace:FindFirstChildOfClass("Model")
                                if dummy then
                                    camera.CFrame = CFrame.new(dummy.Position + Vector3.new(0, 2, 5), dummy.Position)
                                end
                            end
                        '''
                    }
                },
                timeout=30,
            )
            
            # Wait for render
            time.sleep(1)
            
            # Capture
            response = self.session.post(
                f"{self.mcp_endpoint}/mcp",
                json={
                    "method": "execute_luau",
                    "params": {
                        "source": "return workspace.CurrentCamera:GetScreen()"}
                },
                timeout=30,
            )
            
            if response.status_code == 200:
                result = response.json()
                img_data = base64.b64decode(result.get("image", ""))
                screenshot_path = os.path.join(
                    os.path.dirname(__file__), "..", "..", "output", "screenshot.png"
                )
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                with open(screenshot_path, "wb") as f:
                    f.write(img_data)
                return screenshot_path
                
        except Exception as e:
            print(f"  Screenshot error: {e}")
        
        return None
    
    def _compare(self, screenshot_path: str) -> Dict:
        """Compare screenshot to expected template."""
        try:
            screenshot = Image.open(screenshot_path)
            screenshot_np = np.array(screenshot)
            
            # Basic metrics
            coverage = np.sum(screenshot_np[:, :, 3] > 0) / (screenshot_np.shape[0] * screenshot_np.shape[1])
            
            return {
                "coverage": coverage,
                "size": screenshot.size,
            }
        except Exception as e:
            return {"error": str(e)}


def validate_in_studio(template_path: str) -> Dict:
    """Convenience function."""
    validator = RobloxStudioValidator()
    return validator.validate(template_path)
