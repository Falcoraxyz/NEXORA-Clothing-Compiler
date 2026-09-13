"""
Constraint Solver
Translates ClothingSpec + UV graph into actionable per-panel constraints.
Outputs a deterministic constraint map that the engine executes.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum

from src.compiler.dsl_schema import ClothingSpec, GarmentType
from src.compiler.uv_constraint_graph import (
    UVConstraintGraph, EdgePosition, EdgeConstraint, build_uv_graph
)


class ConstraintType(str, Enum):
    BOUNDARY_MATCH = "boundary_match"      # Edge must match adjacent panel
    COLOR_FILL = "color_fill"              # Fill interior with color
    MATERIAL_PROPS = "material_props"      # AO, roughness, normal
    FOLD_GEOMETRY = "fold_geometry"        # Fabric fold direction/stiffness
    DECORATION = "decoration"              # Logo, pocket, zipper, etc.
    STITCH_PATTERN = "stitch_pattern"      # Procedural stitch


@dataclass
class PanelConstraint:
    """Constraints for a single panel."""
    panel_id: str
    constraints: List[Dict[str, Any]] = field(default_factory=list)

    def add(self, constraint_type: ConstraintType, params: Dict[str, Any]):
        self.constraints.append({
            "type": constraint_type.value,
            "params": params,
        })


@dataclass
class SolverResult:
    """Result of constraint solving."""
    garment_type: str
    template_size: Tuple[int, int]
    panel_constraints: Dict[str, PanelConstraint] = field(default_factory=dict)
    edge_constraints: List[Dict[str, Any]] = field(default_factory=list)
    global_constraints: Dict[str, Any] = field(default_factory=dict)

    def get_panel(self, panel_id: str) -> Optional[PanelConstraint]:
        return self.panel_constraints.get(panel_id)

    def summary(self) -> str:
        lines = [
            f"SolverResult: {self.garment_type} @ {self.template_size}",
            f"  Panels: {len(self.panel_constraints)}",
            f"  Edge constraints: {len(self.edge_constraints)}",
        ]
        for pid, pc in self.panel_constraints.items():
            lines.append(f"  {pid}: {len(pc.constraints)} constraints")
        return "\n".join(lines)


class ConstraintSolver:
    """
    Translates a ClothingSpec into actionable constraints per panel.
    
    This is the bridge between "what the user wants" and "what the engine executes".
    """

    def __init__(self, spec: ClothingSpec):
        self.spec = spec
        self.graph = build_uv_graph(spec.garment.garment_type.value)
        self.garment = spec.garment

    def solve(self) -> SolverResult:
        """Run all constraint generation steps."""
        result = SolverResult(
            garment_type=self.spec.garment.garment_type.value,
            template_size=(512, 512),
        )

        # Step 1: Boundary constraints (UV edge matching)
        self._solve_boundary_constraints(result)

        # Step 2: Interior fill constraints (color, material)
        self._solve_interior_constraints(result)

        # Step 3: Fold geometry constraints
        self._solve_fold_constraints(result)

        # Step 4: Decoration constraints (logo, pocket, etc.)
        self._solve_decoration_constraints(result)

        # Step 5: Stitch constraints
        self._solve_stitch_constraints(result)

        # Step 6: Global constraints
        self._solve_global_constraints(result)

        return result

    def _solve_boundary_constraints(self, result: SolverResult):
        """Generate edge-matching constraints from UV graph."""
        for constraint in self.graph.constraints:
            pa_id, ea_pos = constraint.edge_a
            pb_id, eb_pos = constraint.edge_b

            edge_constraint = {
                "type": ConstraintType.BOUNDARY_MATCH.value,
                "edge_a": {"panel": pa_id, "edge": ea_pos.value},
                "edge_b": {"panel": pb_id, "edge": eb_pos.value},
                "constraint_id": constraint.constraint_id,
                "flip": constraint.flip,
                "blend_width": 3,  # pixels
                "blend_method": "gaussian",
            }
            result.edge_constraints.append(edge_constraint)

    def _solve_interior_constraints(self, result: SolverResult):
        """Generate interior fill constraints for each panel."""
        primary = self.garment.color.primary
        secondary = self.garment.color.secondary
        material = self.garment.material

        for panel_id, panel in self.graph.panels.items():
            pc = PanelConstraint(panel_id=panel_id)

            # Color fill
            pc.add(ConstraintType.COLOR_FILL, {
                "color": primary,
                "secondary_color": secondary,
                "fabric": material.fabric.value,
                "noise_intensity": 0.05,
            })

            # Material properties
            pc.add(ConstraintType.MATERIAL_PROPS, {
                "roughness": material.roughness,
                "metallic": material.metallic,
                "normal_strength": material.normal_strength,
                "ao_edge_darkening": 0.3,
                "ao_radius": 8,  # pixels from edge
            })

            result.panel_constraints[panel_id] = pc

    def _solve_fold_constraints(self, result: SolverResult):
        """Generate fabric fold geometry constraints."""
        fit = self.garment.fit
        garment_type = self.garment.garment_type

        # Determine fold intensity based on fit
        if fit == "oversized":
            fold_intensity = 0.15
            fold_frequency = 3
        elif fit == "slim":
            fold_intensity = 0.05
            fold_frequency = 2
        else:  # regular
            fold_intensity = 0.10
            fold_frequency = 2

        # Folds run vertically for shirts, horizontally for pants
        if garment_type == GarmentType.PANTS:
            fold_direction = "horizontal"
        else:
            fold_direction = "vertical"

        for panel_id in self.graph.panels:
            pc = result.panel_constraints.get(panel_id, PanelConstraint(panel_id=panel_id))
            pc.add(ConstraintType.FOLD_GEOMETRY, {
                "direction": fold_direction,
                "intensity": fold_intensity,
                "frequency": fold_frequency,
                "decay_from_edge": 0.5,  # folds fade near boundaries
            })
            result.panel_constraints[panel_id] = pc

    def _solve_decoration_constraints(self, result: SolverResult):
        """Generate decoration placement constraints."""
        # Pocket
        if self.garment.pocket.style.value != "none":
            front_panel = self._get_front_panel()
            if front_panel:
                pc = result.panel_constraints.get(front_panel, PanelConstraint(panel_id=front_panel))
                pc.add(ConstraintType.DECORATION, {
                    "type": "pocket",
                    "style": self.garment.pocket.style.value,
                    "position": self.garment.pocket.position,
                    "size": self.garment.pocket.size,
                    "color": self.garment.color.secondary or self.garment.color.primary,
                })
                result.panel_constraints[front_panel] = pc

        # Logo
        if self.garment.logo:
            logo_panel = self._get_panel_for_position(self.garment.logo.position)
            if logo_panel:
                pc = result.panel_constraints.get(logo_panel, PanelConstraint(panel_id=logo_panel))
                pc.add(ConstraintType.DECORATION, {
                    "type": "logo",
                    "style": self.garment.logo.style.value,
                    "motif": self.garment.logo.motif,
                    "position": self.garment.logo.position,
                    "scale": self.garment.logo.scale,
                    "color": self.garment.color.accent or "#FFFFFF",
                })
                result.panel_constraints[logo_panel] = pc

        # Zipper
        if self.garment.zipper.style.value != "none":
            # Zipper runs down the front center
            front_panels = [pid for pid in self.graph.panels if "front" in pid]
            for fp in front_panels:
                pc = result.panel_constraints.get(fp, PanelConstraint(panel_id=fp))
                pc.add(ConstraintType.DECORATION, {
                    "type": "zipper",
                    "style": self.garment.zipper.style.value,
                    "color": self.garment.zipper.color,
                    "material": self.garment.zipper.material,
                    "position": "center",
                })
                result.panel_constraints[fp] = pc

        # Extras
        for extra in self.garment.extras:
            if extra == "chain":
                front_panel = self._get_front_panel()
                if front_panel:
                    pc = result.panel_constraints.get(front_panel, PanelConstraint(panel_id=front_panel))
                    pc.add(ConstraintType.DECORATION, {
                        "type": "chain",
                        "color": "#C0C0C0",
                        "start": "neck",
                        "end": "chest",
                    })
                    result.panel_constraints[front_panel] = pc

    def _solve_stitch_constraints(self, result: SolverResult):
        """Generate procedural stitch constraints."""
        if self.garment.stitch.type.value == "none":
            return

        for panel_id in self.graph.panels:
            pc = result.panel_constraints.get(panel_id, PanelConstraint(panel_id=panel_id))
            pc.add(ConstraintType.STITCH_PATTERN, {
                "type": self.garment.stitch.type.value,
                "color": self.garment.stitch.color,
                "distance_from_edge": self.garment.stitch.distance_from_edge,
                "spacing": self.garment.stitch.spacing,
                "apply_to_edges": ["top", "bottom", "left", "right"],
            })
            result.panel_constraints[panel_id] = pc

    def _solve_global_constraints(self, result: SolverResult):
        """Global template constraints."""
        result.global_constraints = {
            "template_size": (512, 512),
            "panel_size": 128,
            "background": (0, 0, 0, 0),  # Transparent
            "blend_width": 3,
            "seam_method": "gaussian",  # gaussian, poisson, laplacian
            "color_space": "sRGB",
        }

    def _get_front_panel(self) -> Optional[str]:
        """Get the primary front panel ID."""
        for pid in ["front_left", "front_right"]:
            if pid in self.graph.panels:
                return pid
        return None

    def _get_panel_for_position(self, position: str) -> Optional[str]:
        """Map a named position to a panel."""
        if "left" in position and "chest" in position:
            return "front_left"
        elif "right" in position and "chest" in position:
            return "front_right"
        elif "back" in position:
            return "back_left"
        elif "sleeve" in position:
            if "left" in position:
                return "left_sleeve_top"
            return "right_sleeve_top"
        return "front_left"  # default


def solve_constraints(spec: ClothingSpec) -> SolverResult:
    """Convenience function."""
    solver = ConstraintSolver(spec)
    return solver.solve()
