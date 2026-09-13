"""
UV Constraint Graph - Roblox Official Template Layout
Based on Template-Shirts-R15.png (585×559)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class EdgePosition(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class UVPanel:
    """Represents one panel in the UV template."""
    panel_id: str
    name: str
    # Position in the template (x, y, width, height)
    template_position: Tuple[int, int, int, int]
    # Color in the template (for reference)
    template_color: Tuple[int, int, int] = (0, 0, 0)
    # Whether this panel is on the body (True) or limbs (False)
    is_body: bool = True


@dataclass
class EdgeConstraint:
    """Links two edges that must match."""
    constraint_id: int
    edge_a: Tuple[str, EdgePosition]  # (panel_id, position)
    edge_b: Tuple[str, EdgePosition]  # (panel_id, position)
    flip: bool = False


@dataclass
class UVConstraintGraph:
    """Complete UV topology for a garment type."""
    garment_type: str
    template_size: Tuple[int, int]
    panels: Dict[str, UVPanel] = field(default_factory=dict)
    constraints: List[EdgeConstraint] = field(default_factory=list)

    def add_panel(self, panel: UVPanel):
        self.panels[panel.panel_id] = panel

    def add_constraint(self, constraint: EdgeConstraint):
        self.constraints.append(constraint)

    def get_panel(self, panel_id: str) -> Optional[UVPanel]:
        return self.panels.get(panel_id)

    def get_body_panels(self) -> Dict[str, UVPanel]:
        return {pid: p for pid, p in self.panels.items() if p.is_body}

    def get_limb_panels(self) -> Dict[str, UVPanel]:
        return {pid: p for pid, p in self.panels.items() if not p.is_body}


def build_roblox_shirt_graph() -> UVConstraintGraph:
    """
    Build UV constraint graph for Roblox Shirt template.
    
    Template: 585×559 pixels
    Layout (from Template-Shirts-R15.png):
    
    Row 0 (y=8, h=64):     [Top 128×64]
    Row 1 (y=74, h=128):   [TorsoL 64×128][Back 128×128][TorsoR 64×128][Front 128×128]
    Row 2 (y=204, h=64):   [Bottom 128×64]
    Row 3 (y=289, h=64):   [LeftSmall1 64×64][RightSmall1 64×64]
    Row 4 (y=355, h=128):  [LArmOut 64×128][LLegOut 64×128][LArmIn 64×128][LLegIn 64×128][RLegIn 64×128][RArmIn 64×128][RLegOut 64×128][RArmOut 64×128]
    Row 5 (y=485, h=64):   [LeftSmall2 64×64][RightSmall2 64×64]
    
    UV Mapping (how panels wrap around the 3D avatar):
    - Front: torso front
    - Back: torso back
    - Top: shoulders/upper chest
    - Bottom: lower torso/waist
    - Torso L/R: sides of torso
    - LArm/RArm: left/right arms
    - LLeg/RLeg: left/legs (for shirt, these are empty or cuffs)
    - Small panels: connection pieces
    """
    graph = UVConstraintGraph(
        garment_type="shirt",
        template_size=(585, 559),
    )
    
    # Panel definitions from template analysis
    panels_def = [
        # Body panels
        ("front", "Front", (427, 74, 128, 128), (0, 116, 189), True),
        ("back", "Back", (231, 74, 128, 128), (226, 35, 26), True),
        ("top", "Top", (231, 8, 128, 64), (0, 162, 255), True),
        ("bottom", "Bottom", (231, 204, 128, 64), (246, 136, 2), True),
        ("torso_left", "Torso Left", (165, 74, 64, 128), (2, 183, 87), True),
        ("torso_right", "Torso Right", (361, 74, 64, 128), (246, 183, 2), True),
        
        # Small panels (connection pieces)
        ("left_small_1", "Left Small 1", (217, 289, 64, 64), (0, 162, 255), False),
        ("right_small_1", "Right Small 1", (308, 289, 64, 64), (0, 162, 255), False),
        ("left_small_2", "Left Small 2", (217, 485, 64, 64), (246, 136, 2), False),
        ("right_small_2", "Right Small 2", (308, 485, 64, 64), (246, 136, 2), False),
        
        # Arm/Leg panels (for shirt: arms)
        ("left_arm_outer", "Left Arm Outer", (19, 355, 64, 128), (246, 183, 2), False),
        ("left_leg_outer", "Left Leg Outer", (85, 355, 64, 128), (0, 116, 189), False),
        ("left_arm_inner", "Left Arm Inner", (151, 355, 64, 128), (2, 183, 87), False),
        ("left_leg_inner", "Left Leg Inner", (217, 355, 64, 128), (226, 35, 26), False),
        ("right_leg_inner", "Right Leg Inner", (308, 355, 64, 128), (226, 35, 26), False),
        ("right_arm_inner", "Right Arm Inner", (374, 355, 64, 128), (246, 183, 2), False),
        ("right_leg_outer", "Right Leg Outer", (440, 355, 64, 128), (0, 116, 189), False),
        ("right_arm_outer", "Right Arm Outer", (506, 355, 64, 128), (2, 183, 87), False),
    ]
    
    for pid, name, pos, color, is_body in panels_def:
        panel = UVPanel(
            panel_id=pid,
            name=name,
            template_position=pos,
            template_color=color,
            is_body=is_body,
        )
        graph.add_panel(panel)
    
    # Edge constraints - only between panels that share edges in UV space
    # For Roblox template, panels are laid out with gaps, so edges don't directly touch
    # The UV mapping handles the wrapping
    constraints_def = [
        # Body panel connections (adjacent in UV space)
        ("front", EdgePosition.TOP, "top", EdgePosition.BOTTOM),
        ("front", EdgePosition.BOTTOM, "bottom", EdgePosition.TOP),
        ("front", EdgePosition.RIGHT, "torso_right", EdgePosition.LEFT),
        ("front", EdgePosition.LEFT, "torso_right", EdgePosition.RIGHT),
        
        ("back", EdgePosition.TOP, "top", EdgePosition.TOP),
        ("back", EdgePosition.BOTTOM, "bottom", EdgePosition.BOTTOM),
        ("back", EdgePosition.LEFT, "torso_left", EdgePosition.LEFT),
        ("back", EdgePosition.RIGHT, "torso_left", EdgePosition.RIGHT),
        
        ("torso_left", EdgePosition.RIGHT, "torso_right", EdgePosition.LEFT),
        
        ("top", EdgePosition.LEFT, "torso_left", EdgePosition.TOP),
        ("top", EdgePosition.RIGHT, "torso_right", EdgePosition.TOP),
        ("bottom", EdgePosition.LEFT, "torso_left", EdgePosition.BOTTOM),
        ("bottom", EdgePosition.RIGHT, "torso_right", EdgePosition.BOTTOM),
    ]
    
    for i, (pa, ea, pb, eb) in enumerate(constraints_def):
        constraint = EdgeConstraint(
            constraint_id=i,
            edge_a=(pa, ea),
            edge_b=(pb, eb),
        )
        graph.add_constraint(constraint)
    
    return graph


def build_roblox_pants_graph() -> UVConstraintGraph:
    """
    Build UV constraint graph for Roblox Pants template.
    
    Template: 585×559 pixels (same layout as shirt)
    UV Mapping for Pants:
    - Front: upper legs front (thighs)
    - Back: upper legs back
    - Top: waist
    - Bottom: cuffs/knees
    - Torso L/R: waist sides
    - LLeg/RLeg: left/right legs
    - LArm/RArm: empty for pants (or belt area)
    - Small panels: connection pieces
    """
    graph = UVConstraintGraph(
        garment_type="pants",
        template_size=(585, 559),
    )
    
    # Same layout as shirt but different semantic meaning
    panels_def = [
        # Leg panels (main body for pants)
        ("front", "Front Legs", (427, 74, 128, 128), (0, 116, 189), True),
        ("back", "Back Legs", (231, 74, 128, 128), (226, 35, 26), True),
        ("top", "Waist", (231, 8, 128, 64), (0, 162, 255), True),
        ("bottom", "Cuffs", (231, 204, 128, 64), (246, 136, 2), True),
        ("torso_left", "Waist Left", (165, 74, 64, 128), (2, 183, 87), True),
        ("torso_right", "Waist Right", (361, 74, 64, 128), (246, 183, 2), True),
        
        # Small panels
        ("left_small_1", "Left Small 1", (217, 289, 64, 64), (0, 162, 255), False),
        ("right_small_1", "Right Small 1", (308, 289, 64, 64), (0, 162, 255), False),
        ("left_small_2", "Left Small 2", (217, 485, 64, 64), (246, 136, 2), False),
        ("right_small_2", "Right Small 2", (308, 485, 64, 64), (246, 136, 2), False),
        
        # Leg panels (for pants: actual legs, arms are empty)
        ("left_arm_outer", "Belt Left Outer", (19, 355, 64, 128), (246, 183, 2), False),
        ("left_leg_outer", "Left Leg Outer", (85, 355, 64, 128), (0, 116, 189), False),
        ("left_arm_inner", "Belt Left Inner", (151, 355, 64, 128), (2, 183, 87), False),
        ("left_leg_inner", "Left Leg Inner", (217, 355, 64, 128), (226, 35, 26), False),
        ("right_leg_inner", "Right Leg Inner", (308, 355, 64, 128), (226, 35, 26), False),
        ("right_arm_inner", "Belt Right Inner", (374, 355, 64, 128), (246, 183, 2), False),
        ("right_leg_outer", "Right Leg Outer", (440, 355, 64, 128), (0, 116, 189), False),
        ("right_arm_outer", "Belt Right Outer", (506, 355, 64, 128), (2, 183, 87), False),
    ]
    
    for pid, name, pos, color, is_body in panels_def:
        panel = UVPanel(
            panel_id=pid,
            name=name,
            template_position=pos,
            template_color=color,
            is_body=is_body,
        )
        graph.add_panel(panel)
    
    # Pants constraints (same topology as shirt)
    constraints_def = [
        ("front", EdgePosition.TOP, "top", EdgePosition.BOTTOM),
        ("front", EdgePosition.BOTTOM, "bottom", EdgePosition.TOP),
        ("front", EdgePosition.RIGHT, "torso_right", EdgePosition.LEFT),
        ("front", EdgePosition.LEFT, "torso_right", EdgePosition.RIGHT),
        
        ("back", EdgePosition.TOP, "top", EdgePosition.TOP),
        ("back", EdgePosition.BOTTOM, "bottom", EdgePosition.BOTTOM),
        ("back", EdgePosition.LEFT, "torso_left", EdgePosition.LEFT),
        ("back", EdgePosition.RIGHT, "torso_left", EdgePosition.RIGHT),
        
        ("torso_left", EdgePosition.RIGHT, "torso_right", EdgePosition.LEFT),
        
        ("top", EdgePosition.LEFT, "torso_left", EdgePosition.TOP),
        ("top", EdgePosition.RIGHT, "torso_right", EdgePosition.TOP),
        ("bottom", EdgePosition.LEFT, "torso_left", EdgePosition.BOTTOM),
        ("bottom", EdgePosition.RIGHT, "torso_right", EdgePosition.BOTTOM),
    ]
    
    for i, (pa, ea, pb, eb) in enumerate(constraints_def):
        constraint = EdgeConstraint(
            constraint_id=i,
            edge_a=(pa, ea),
            edge_b=(pb, eb),
        )
        graph.add_constraint(constraint)
    
    return graph


def build_uv_graph(garment_type: str) -> UVConstraintGraph:
    """Build UV constraint graph based on garment type."""
    if garment_type == "tshirt":
        return build_roblox_tshirt_graph()
    elif garment_type in ("shirt", "jacket"):
        return build_roblox_shirt_graph()
    elif garment_type == "pants":
        return build_roblox_pants_graph()
    else:
        raise ValueError(f"Unknown garment type: {garment_type}")


def build_roblox_tshirt_graph() -> UVConstraintGraph:
    """Build UV constraint graph for T-Shirt (single 512×512 panel)."""
    graph = UVConstraintGraph(
        garment_type="tshirt",
        template_size=(512, 512),
    )
    
    panel = UVPanel(
        panel_id="front",
        name="Front",
        template_position=(0, 0, 512, 512),
        template_color=(255, 255, 255),
        is_body=True,
    )
    graph.add_panel(panel)
    # No edge constraints needed — single panel
    
    return graph
