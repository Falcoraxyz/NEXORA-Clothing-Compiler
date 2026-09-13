"""
FLUX Texture Synthesizer
Generates realistic fabric textures using FLUX image model.
Caches textures per fabric type to avoid redundant API calls.
"""

import os
import sys
import json
import hashlib
import requests
import numpy as np
from PIL import Image
from typing import Dict, Optional, Tuple
from io import BytesIO

# Will use ComfyUI API or direct FLUX API
# For now, structure is ready — actual API call depends on available endpoint

class FLUXTextureSynthesizer:
    """
    Generates fabric textures using FLUX.
    
    Architecture:
        - FLUX generates albedo only (base color texture)
        - Engine adds AO, normal, curvature procedurally
        - Textures are cached per fabric type to save API calls
        
    Supported fabrics:
        - heavy_cotton, denim, leather, satin, nylon, wool
    """
    
    # Cache directory for generated textures
    CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cache", "textures")
    
    # FLUX API endpoint (ComfyUI or direct)
    FLUX_API_ENDPOINT = "http://127.0.0.1:8188"  # ComfyUI default port
    
    # Fabric-specific prompts for FLUX
    FABRIC_PROMPTS = {
        "heavy_cotton": "seamless fabric texture, heavy cotton, matte finish, soft weave pattern, neutral lighting, flat lay photography, high detail",
        "denim": "seamless denim fabric texture, blue jeans material, diagonal weave pattern, matte finish, flat lay photography, high detail",
        "leather": "seamless leather fabric texture, natural grain pattern, matte finish, brown leather, flat lay photography, high detail",
        "satin": "seamless satin fabric texture, silky smooth, subtle sheen, matte finish, flat lay photography, high detail",
        "nylon": "seamless nylon fabric texture, synthetic material, subtle weave, matte finish, flat lay photography, high detail",
        "wool": "seamless wool fabric texture, knitted pattern, soft fibers, matte finish, flat lay photography, high detail",
    }
    
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        os.makedirs(self.CACHE_DIR, exist_ok=True)
    
    def generate_fabric_texture(self, fabric_type: str, 
                                 resolution: int = 512,
                                 seed: Optional[int] = None) -> np.ndarray:
        """
        Generate a fabric texture using FLUX.
        
        Args:
            fabric_type: Type of fabric (e.g., "heavy_cotton", "denim")
            resolution: Texture resolution (default 512)
            seed: Random seed for reproducibility
            
        Returns:
            numpy array of shape (resolution, resolution, 3) with RGB values
        """
        # Check cache first
        if self.use_cache:
            cached = self._get_cached_texture(fabric_type, resolution)
            if cached is not None:
                print(f"  [FLUX] Using cached texture for {fabric_type}")
                return cached
        
        # Get prompt for fabric type
        prompt = self.FABRIC_PROMPTS.get(fabric_type, self.FABRIC_PROMPTS["heavy_cotton"])
        
        # Generate texture using FLUX
        texture = self._call_flux_api(prompt, resolution, seed)
        
        # Cache the result
        if self.use_cache and texture is not None:
            self._cache_texture(fabric_type, resolution, texture)
        
        return texture
    
    def _call_flux_api(self, prompt: str, resolution: int, 
                        seed: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Call FLUX API to generate texture.
        Currently uses ComfyUI workflow structure.
        """
        # TODO: Implement actual ComfyUI API call
        # For now, return None (will fall back to procedural)
        
        # ComfyUI API structure (pseudo-code):
        # workflow = self._build_comfyui_workflow(prompt, resolution, seed)
        # response = requests.post(
        #     f"{self.FLUX_API_ENDPOINT}/prompt",
        #     json={"prompt": workflow},
        #     timeout=120
        # )
        # if response.status_code == 200:
        #     result = response.json()
        #     image_data = self._get_comfyui_image(result["prompt_id"])
        #     return np.array(image_data)
        
        print(f"  [FLUX] API call not implemented yet — using procedural fallback")
        return None
    
    def _get_cached_texture(self, fabric_type: str, resolution: int) -> Optional[np.ndarray]:
        """Load texture from cache if available."""
        cache_key = self._get_cache_key(fabric_type, resolution)
        cache_path = os.path.join(self.CACHE_DIR, f"{cache_key}.npy")
        
        if os.path.exists(cache_path):
            try:
                return np.load(cache_path)
            except Exception as e:
                print(f"  [FLUX] Cache load error: {e}")
        
        return None
    
    def _cache_texture(self, fabric_type: str, resolution: int, texture: np.ndarray):
        """Save texture to cache."""
        cache_key = self._get_cache_key(fabric_type, resolution)
        cache_path = os.path.join(self.CACHE_DIR, f"{cache_key}.npй")
        
        try:
            np.save(cache_path, texture)
            print(f"  [FLUX] Cached texture: {cache_key}")
        except Exception as e:
            print(f"  [FLUX] Cache save error: {e}")
    
    def _get_cache_key(self, fabric_type: str, resolution: int) -> str:
        """Generate cache key for fabric type."""
        return f"{fabric_type}_{resolution}"
    
    def _build_comfyui_workflow(self, prompt: str, resolution: int, 
                                 seed: Optional[int] = None) -> Dict:
        """
        Build ComfyUI workflow JSON for FLUX text-to-image.
        """
        # TODO: Build actual ComfyUI workflow
        # This is a placeholder structure
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"}
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["1", 1]}
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "bad quality, blurry, distorted", "clip": ["1", 1]}
            },
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": resolution, "height": resolution, "batch_size": 1}
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed or 42,
                    "steps": 20,
                    "cfg": 1.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0]
                }
            },
            "6": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["5", 0], "vae": ["1", 2]}
            },
            "7": {
                "class_type": "SaveImage",
                "inputs": {"images": ["6", 0], "filename_prefix": "flux_texture"}
            }
        }


class ProceduralTextureFallback:
    """
    Fallback texture generator when FLUX is not available.
    Uses numpy to generate procedural fabric textures.
    """
    
    @staticmethod
    def generate(fabric_type: str, resolution: int = 512) -> np.ndarray:
        """Generate procedural fabric texture."""
        if fabric_type == "denim":
            return ProceduralTextureFallback._denim(resolution)
        elif fabric_type == "leather":
            return ProceduralTextureFallback._leather(resolution)
        elif fabric_type == "satin":
            return ProceduralTextureFallback._satin(resolution)
        elif fabric_type == "nylon":
            return ProceduralTextureFallback._nylon(resolution)
        elif fabric_type == "wool":
            return ProceduralTextureFallback._wool(resolution)
        else:  # heavy_cotton
            return ProceduralTextureFallback._cotton(resolution)
    
    @staticmethod
    def _cotton(resolution: int) -> np.ndarray:
        """Procedural cotton texture."""
        texture = np.zeros((resolution, resolution, 3), dtype=np.uint8)
        base_color = 128
        
        for y in range(resolution):
            for x in range(resolution):
                # Subtle weave pattern
                weave = int(np.sin(x * 0.5) * np.sin(y * 0.5) * 10)
                noise = np.random.randint(-5, 5)
                val = np.clip(base_color + weave + noise, 0, 255)
                texture[y, x] = [val, val, val]
        
        return texture
    
    @staticmethod
    def _denim(resolution: int) -> np.ndarray:
        """Procedural denim texture."""
        texture = np.zeros((resolution, resolution, 3), dtype=np.uint8)
        
        for y in range(resolution):
            for x in range(resolution):
                # Diagonal weave pattern
                diagonal = (x + y) % 4
                if diagonal == 0:
                    val = 80
                elif diagonal == 1:
                    val = 100
                elif diagonal == 2:
                    val = 90
                else:
                    val = 110
                
                noise = np.random.randint(-5, 5)
                val = np.clip(val + noise, 0, 255)
                texture[y, x] = [val, val + 10, val + 30]  # Blue tint
        
        return texture
    
    @staticmethod
    def _leather(resolution: int) -> np.ndarray:
        """Procedural leather texture."""
        texture = np.zeros((resolution, resolution, 3), dtype=np.uint8)
        
        for y in range(resolution):
            for x in range(resolution):
                # Grain pattern
                grain = int(np.sin(x * 0.3) * np.cos(y * 0.3) * 15)
                noise = np.random.randint(-8, 8)
                val = np.clip(100 + grain + noise, 0, 255)
                texture[y, x] = [val, val - 10, val - 20]  # Brown tint
        
        return texture
    
    @staticmethod
    def _satin(resolution: int) -> np.ndarray:
        """Procedural satin texture."""
        texture = np.zeros((resolution, resolution, 3), dtype=np.uint8)
        
        for y in range(resolution):
            for x in range(resolution):
                # Smooth with subtle sheen
                sheen = int(np.sin(y / resolution * np.pi) * 20)
                noise = np.random.randint(-3, 3)
                val = np.clip(140 + sheen + noise, 0, 255)
                texture[y, x] = [val, val, val]
        
        return texture
    
    @staticmethod
    def _nylon(resolution: int) -> np.ndarray:
        """Procedural nylon texture."""
        texture = np.zeros((resolution, resolution, 3), dtype=np.uint8)
        
        for y in range(resolution):
            for x in range(resolution):
                # Fine synthetic weave
                weave = int(np.sin(x * 0.8) * np.sin(y * 0.8) * 8)
                noise = np.random.randint(-3, 3)
                val = np.clip(120 + weave + noise, 0, 255)
                texture[y, x] = [val, val, val]
        
        return texture
    
    @staticmethod
    def _wool(resolution: int) -> np.ndarray:
        """Procedural wool texture."""
        texture = np.zeros((resolution, resolution, 3), dtype=np.uint8)
        
        for y in range(resolution):
            for x in range(resolution):
                # Knitted pattern
                knit = int(np.sin(x * 0.4) * np.sin(y * 0.4) * 12)
                noise = np.random.randint(-10, 10)
                val = np.clip(130 + knit + noise, 0, 255)
                texture[y, x] = [val, val, val]
        
        return texture


def get_fabric_texture(fabric_type: str, resolution: int = 512,
                        use_flux: bool = False) -> np.ndarray:
    """
    Get fabric texture — tries FLUX first, falls back to procedural.
    
    Args:
        fabric_type: Type of fabric
        resolution: Texture resolution
        use_flux: Whether to try FLUX API first
        
    Returns:
        numpy array of shape (resolution, resolution, 3)
    """
    if use_flux:
        synthesizer = FLUXTextureSynthesizer()
        texture = synthesizer.generate_fabric_texture(fabric_type, resolution)
        if texture is not None:
            return texture
    
    # Fallback to procedural
    return ProceduralTextureFallback.generate(fabric_type, resolution)
