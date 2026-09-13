"""
NEXORA Web Dashboard
FastAPI server with HTML frontend for clothing generation.
Run with: uvicorn web.server:app --reload --port 8080
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.compiler.dsl_schema import ClothingSpec, EXAMPLE_SPEC, EXAMPLE_TSHIRT_SPEC, EXAMPLE_PANTS_SPEC
from src.compiler.nl_to_spec import convert_nl_to_spec
from src.compiler.uv_constraint_graph import build_uv_graph
from src.engine.template_generator import ProceduralTemplateGeneratorV2
from src.compiler.constraint_solver import solve_constraints
from src.validator.vision_metrics import VisionMetrics
from main import compile_clothing, hex_to_rgb

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
STATIC_DIR = BASE_DIR / "web" / "static"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(title="NEXORA Clothing Compiler", version="2.1")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class GenerateRequest(BaseModel):
    spec: dict
    filename: Optional[str] = None


class ValidateRequest(BaseModel):
    spec: dict


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "example_spec": json.dumps(EXAMPLE_SPEC, indent=2),
        "example_tshirt": json.dumps(EXAMPLE_TSHIRT_SPEC, indent=2),
        "example_pants": json.dumps(EXAMPLE_PANTS_SPEC, indent=2),
    })


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    """Generate template from spec JSON."""
    try:
        filename = req.filename or "template.png"
        if not filename.endswith(".png"):
            filename += ".png"
        
        output_path = str(OUTPUT_DIR / filename)
        template = compile_clothing(req.spec, output_path)
        
        return JSONResponse({
            "success": True,
            "path": output_path,
            "size": template.size,
            "filename": filename,
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
        }, status_code=400)


@app.post("/api/validate")
async def validate(req: ValidateRequest):
    """Validate a spec without generating."""
    try:
        spec = ClothingSpec.from_dict(req.spec)
        solver_result = solve_constraints(spec)
        graph = build_uv_graph(spec.garment.garment_type.value)
        
        panel_positions = {}
        for pid, panel in graph.panels.items():
            panel_positions[pid] = panel.template_position
        
        return JSONResponse({
            "success": True,
            "garment_type": spec.garment.garment_type.value,
            "template_size": solver_result.template_size,
            "panels": len(solver_result.panel_constraints),
            "edge_constraints": len(solver_result.edge_constraints),
            "panel_positions": {k: list(v) for k, v in panel_positions.items()},
            "spec_summary": {
                "name": spec.name,
                "theme": spec.theme,
                "fit": spec.garment.fit,
                "color": spec.garment.color.primary,
                "material": spec.garment.material.fabric.value,
                "zipper": spec.garment.zipper.style.value,
                "pocket": spec.garment.pocket.style.value,
                "stitch": spec.garment.stitch.type.value,
                "hood": spec.garment.hood,
                "logo": spec.garment.logo.motif if spec.garment.logo and spec.garment.logo.is_valid else None,
                "extras": spec.garment.extras,
            }
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
        }, status_code=400)


@app.get("/api/presets")
async def presets():
    """Get all preset specs."""
    return JSONResponse({
        "shirt": EXAMPLE_SPEC,
        "tshirt": EXAMPLE_TSHIRT_SPEC,
        "pants": EXAMPLE_PANTS_SPEC,
    })


@app.get("/api/outputs")
async def outputs():
    """List generated output files."""
    files = []
    for f in OUTPUT_DIR.glob("*.png"):
        files.append({
            "name": f.name,
            "size": f.stat().st_size,
            "modified": f.stat().st_mtime,
        })
    return JSONResponse(sorted(files, key=lambda x: x["modified"], reverse=True))


@app.post("/api/nl-to-spec")
async def nl_to_spec(text: str):
    """Convert natural language to spec JSON."""
    try:
        spec = convert_nl_to_spec(text)
        return JSONResponse({"success": True, "spec": spec})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


def start():
    """Start the web server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)


if __name__ == "__main__":
    start()
