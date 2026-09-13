# NEXORA Clothing Compiler

A constraint-based clothing compiler for Roblox that generates pixel-perfect UV-mapped garment templates from natural language specifications.

## Philosophy

> **AI generates intent. Engine generates pixels.**

Unlike traditional approaches where AI directly generates images (with seam misalignment), this system separates concerns:

1. **AI (Creative Director)** → produces structured JSON specifications
2. **Constraint Solver** → translates specs into per-panel constraints
3. **Procedural Engine** → executes constraints deterministically
4. **Seam Solver** → ensures pixel-perfect boundary alignment
5. **Vision Validator** → verifies output quality with metrics

This turns "research-grade problems" into "engineering problems."

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   USER PROMPT                           │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│             LLM (Creative Director)                      │
│  Output: ClothingSpec JSON (DSL)                        │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│            Constraint Solver                             │
│  - UV graph topology (12 panels, 14+ edges)             │
│  - Edge pairing constraints                             │
│  - Layer composition order                              │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│         Procedural Garment Engine                        │
│  - Albedo generation per panel                          │
│  - AO (ambient occlusion from geometry)                 │
│  - Curvature (edge darkening)                           │
│  - Normal hints (bump from folds)                       │
│  - Fabric folds (procedural noise)                      │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│           Material Composer                              │
│  - Layer-based decorations (pocket, logo, zipper)       │
│  - Procedural stitches                                  │
│  - SVG logo rasterization                               │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Seam Solver                                 │
│  - Gaussian / Poisson / Laplacian blend                 │
│  - Boundary pixel locking                               │
│  - 2-4px feathering                                     │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│          Roblox Studio Validator                         │
│  - Apply to dummy, screenshot                           │
│  - Per-panel SSIM / seam continuity                     │
│  - Targeted re-render (auto-correction loop)            │
└────────────────────────┬────────────────────────────────┘
                         ▼
                    Export PNG (512×512)
```

## Quick Start

```bash
cd nexora-clothing-compiler
python main.py
```

This generates `output/gangster_hoodie.png` — a 512×512 Roblox-ready template.

## Project Structure

```
nexora-clothing-compiler/
├── src/
│   ├── compiler/
│   │   ├── dsl_schema.py           ← ClothingSpec (LLM → JSON)
│   │   ├── uv_constraint_graph.py  ← UV topology
│   │   └── constraint_solver.py    ← Bridge spec → constraints
│   ├── engine/
│   │   ├── garment_engine.py       ← Albedo, AO, normal, folds
│   │   ├── material_composer.py    ← Final template composition
│   │   ├── seam_solver.py          ← Blend methods
│   │   ├── auto_correction.py      ← Closed-loop correction
│   │   └── template_generator.py   ← Legacy v1 generator
│   └── validator/
│       ├── vision_metrics.py       ← SSIM, seam continuity
│       └── studio_validator.py     ← Roblox Studio integration
├── main.py                          ← Full pipeline entrypoint
└── tests/
    ├── test_compiler.py            ← v1 tests
    ├── test_compiler_v2.py         ← v2 tests
    └── test_auto_correction.py     ← Auto-correction tests
```

## Quality Metrics

All edges achieve **similarity 1.00** (perfect match) because boundary pixels are deterministically copied, not AI-generated.

| Metric | Target | Current |
|--------|--------|---------|
| Seam continuity | > 0.85 | **1.00** |
| Color accuracy | > 80% | **99%** |
| Coverage | > 50% | **75%** |

## Roblox Integration

Designed to work with the [NEXORA MCP Bridge](https://github.com/Falcoraxyz/weppy-roblox-mcp-main) for end-to-end Studio automation.

## License

Apache-2.0
