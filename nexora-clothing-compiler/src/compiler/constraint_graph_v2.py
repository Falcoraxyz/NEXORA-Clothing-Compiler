"""
Constraint Graph v2
Graph-based constraint system with hard/soft constraints and priorities.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum


class ConstraintType(str, Enum):
    HARD = "hard"      # Must be satisfied
    SOFT = "soft"      # Should be satisfied
    COSMETIC = "cosmetic"  # Nice to have


class EdgePosition(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class PanelNode:
    """A panel in the UV template."""
    panel_id: str
    name: str
    template_position: Tuple[int, int, int, int]
    edges: Dict[EdgePosition, 'EdgeConstraint'] = field(default_factory=dict)


@dataclass
class EdgeConstraint:
    """Constraint between two panel edges."""
    edge_id: int
    panel_a: str
    edge_a: EdgePosition
    panel_b: str
    edge_b: EdgePosition
    constraint_type: ConstraintType = ConstraintType.HARD
    priority: int = 100  # Lower = higher priority
    weight: float = 1.0  # For soft constraints
    
    def __repr__(self):
        return (f"EdgeConstraint({self.panel_a}.{self.edge_a.value} -> "
                f"{self.panel_b}.{self.edge_b.value}, "
                f"type={self.constraint_type.value}, priority={self.priority})")


@dataclass
class ConstraintGraph:
    """Complete constraint graph for a garment template."""
    garment_type: str
    template_size: Tuple[int, int]
    panels: Dict[str, PanelNode] = field(default_factory=dict)
    edges: List[EdgeConstraint] = field(default_factory=list)
    
    def add_panel(self, panel: PanelNode):
        self.panels[panel.panel_id] = panel
    
    def add_edge(self, edge: EdgeConstraint):
        self.edges.append(edge)
    
    def get_panel(self, panel_id: str) -> Optional[PanelNode]:
        return self.panels.get(panel_id)
    
    def get_edges_for_panel(self, panel_id: str) -> List[EdgeConstraint]:
        """Get all edges connected to a panel."""
        return [e for e in self.edges 
                if e.panel_a == panel_id or e.panel_b == panel_id]
    
    def get_hard_constraints(self) -> List[EdgeConstraint]:
        """Get all hard constraints."""
        return [e for e in self.edges if e.constraint_type == ConstraintType.HARD]
    
    def get_soft_constraints(self) -> List[EdgeConstraint]:
        """Get all soft constraints."""
        return [e for e in self.edges if e.constraint_type == ConstraintType.SOFT]
    
    def get_constraints_by_priority(self) -> List[EdgeConstraint]:
        """Get constraints sorted by priority."""
        return sorted(self.edges, key=lambda e: e.priority)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the constraint graph."""
        errors = []
        
        # Check for duplicate edges
        seen = set()
        for edge in self.edges:
            key = (edge.panel_a, edge.edge_a, edge.panel_b, edge.edge_b)
            reverse_key = (edge.panel_b, edge.edge_b, edge.panel_a, edge.edge_a)
            if key in seen or reverse_key in seen:
                errors.append(f"Duplicate edge: {edge}")
            seen.add(key)
        
        # Check for missing panels
        for edge in self.edges:
            if edge.panel_a not in self.panels:
                errors.append(f"Missing panel: {edge.panel_a}")
            if edge.panel_b not in self.panels:
                errors.append(f"Missing panel: {edge.panel_b}")
        
        # Check for edge compatibility
        for edge in self.edges:
            panel_a = self.panels.get(edge.panel_a)
            panel_b = self.panels.get(edge.panel_b)
            if panel_a and panel_b:
                # Check if edge lengths match for hard constraints
                if edge.constraint_type == ConstraintType.HARD:
                    len_a = self._get_edge_length(panel_a, edge.edge_a)
                    len_b = self._get_edge_length(panel_b, edge.edge_b)
                    if len_a != len_b:
                        errors.append(
                            f"Edge length mismatch: {edge.panel_a}.{edge.edge_a} ({len_a}) "
                            f"!= {edge.panel_b}.{edge.edge_b} ({len_b})"
                        )
        
        return len(errors) == 0, errors
    
    def _get_edge_length(self, panel: PanelNode, edge: EdgePosition) -> int:
        """Get the length of a panel edge."""
        x, y, w, h = panel.template_position
        if edge in (EdgePosition.TOP, EdgePosition.BOTTOM):
            return w
        return h
    
    def summary(self) -> str:
        """Get a summary of the constraint graph."""
        hard = len(self.get_hard_constraints())
        soft = len(self.get_soft_constraints())
        cosmetic = len([e for e in self.edges if e.constraint_type == ConstraintType.COSMETIC])
        
        lines = [
            f"ConstraintGraph: {self.garment_type} @ {self.template_size}",
            f"  Panels: {len(self.panels)}",
            f"  Edges: {len(self.edges)}",
            f"    Hard: {hard}",
            f"    Soft: {soft}",
            f"    Cosmetic: {cosmetic}",
        ]
        return "\n".join(lines)


def build_roblox_shirt_graph_v2() -> ConstraintGraph:
    """Build constraint graph for Roblox Shirt template (585×559)."""
    graph = ConstraintGraph(
        garment_type="shirt",
        template_size=(585, 559),
    )
    
    # Panel definitions
    panels_def = [
        ("front", "Front", (427, 74, 128, 128)),
        ("back", "Back", (231, 74, 128, 128)),
        ("top", "Top", (231, 8, 128, 64)),
        ("bottom", "Bottom", (231, 204, 128, 64)),
        ("torso_left", "Torso Left", (165, 74, 64, 128)),
        ("torso_right", "Torso Right", (361, 74, 64, 128)),
        ("left_small_1", "Left Small 1", (217, 289, 64, 64)),
        ("right_small_1", "Right Small 1", (308, 289, 64, 64)),
        ("left_small_2", "Left Small 2", (217, 485, 64, 64)),
        ("right_small_2", "Right Small 2", (308, 485, 64, 64)),
        ("left_arm_outer", "Left Arm Outer", (19, 355, 64, 128)),
        ("left_leg_outer", "Left Leg Outer", (85, 355, 64, 128)),
        ("left_arm_inner", "Left Arm Inner", (151, 355, 64, 128)),
        ("left_leg_inner", "Left Leg Inner", (217, 355, 64, 128)),
        ("right_leg_inner", "Right Leg Inner", (308, 355, 64, 128)),
        ("right_arm_inner", "Right Arm Inner", (374, 355, 64, 128)),
        ("right_leg_outer", "Right Leg Outer", (440, 355, 64, 128)),
        ("right_arm_outer", "Right Arm Outer", (506, 355, 64, 128)),
    ]
    
    for pid, name, pos in panels_def:
        panel = PanelNode(panel_id=pid, name=name, template_position=pos)
        graph.add_panel(panel)
    
    # Edge constraints with priorities
    # Hard constraints (priority 0-30): structural edges that must match
    # Soft constraints (priority 40-70): visual edges that should match
    # Cosmetic constraints (priority 80-100): nice-to-have visual consistency
    
    constraints_def = [
        # Body panel connections (HARD)
        ("front", EdgePosition.TOP, "top", EdgePosition.BOTTOM, ConstraintType.HARD, 0),
        ("front", EdgePosition.BOTTOM, "bottom", EdgePosition.TOP, ConstraintType.HARD, 0),
        ("front", EdgePosition.RIGHT, "torso_right", EdgePosition.LEFT, ConstraintType.HARD, 0),
        ("front", EdgePosition.LEFT, "torso_right", EdgePosition.RIGHT, ConstraintType.HARD, 0),
        
        ("back", EdgePosition.TOP, "top", EdgePosition.TOP, ConstraintType.HARD, 0),
        ("back", EdgePosition.BOTTOM, "bottom", EdgePosition.BOTTOM, ConstraintType.HARD, 0),
        ("back", EdgePosition.LEFT, "torso_left", EdgePosition.LEFT, ConstraintType.HARD, 0),
        ("back", EdgePosition.RIGHT, "torso_left", EdgePosition.RIGHT, ConstraintType.HARD, 0),
        
        ("torso_left", EdgePosition.RIGHT, "torso_right", EdgePosition.LEFT, ConstraintType.HARD, 10),
        
        ("top", EdgePosition.LEFT, "torso_left", EdgePosition.TOP, ConstraintType.HARD, 10),
        ("top", EdgePosition.RIGHT, "torso_right", EdgePosition.TOP, ConstraintType.HARD, 10),
        ("bottom", EdgePosition.LEFT, "torso_left", EdgePosition.BOTTOM, ConstraintType.HARD, 10),
        ("bottom", EdgePosition.RIGHT, "torso_right", EdgePosition.BOTTOM, ConstraintType.HARD, 10),
        
        # Small panel connections (SOFT)
        ("left_small_1", EdgePosition.BOTTOM, "left_arm_inner", EdgePosition.TOP, ConstraintType.SOFT, 40),
        ("right_small_1", EdgePosition.BOTTOM, "right_arm_inner", EdgePosition.TOP, ConstraintType.SOFT, 40),
        ("left_small_2", EdgePosition.TOP, "left_leg_inner", EdgePosition.BOTTOM, ConstraintType.SOFT, 40),
        ("right_small_2", EdgePosition.TOP, "right_leg_inner", EdgePosition.BOTTOM, ConstraintType.SOFT, 40),
        
        # Arm/Leg chain (SOFT)
        ("left_arm_outer", EdgePosition.RIGHT, "left_leg_outer", EdgePosition.LEFT, ConstraintType.SOFT, 50),
        ("left_leg_outer", EdgePosition.RIGHT, "left_arm_inner", EdgePosition.LEFT, ConstraintType.SOFT, 50),
        ("left_arm_inner", EdgePosition.RIGHT, "left_leg_inner", EdgePosition.LEFT, ConstraintType.SOFT, 50),
        
        ("right_leg_inner", EdgePosition.RIGHT, "right_arm_inner", EdgePosition.LEFT, ConstraintType.SOFT, 50),
        ("right_arm_inner", EdgePosition.RIGHT, "right_leg_outer", EdgePosition.LEFT, ConstraintType.SOFT, 50),
        ("right_leg_outer", EdgePosition.RIGHT, "right_arm_outer", EdgePosition.LEFT, ConstraintType.SOFT, 50),
        
        # Cosmetic constraints (color consistency between adjacent panels)
        ("front", EdgePosition.TOP, "back", EdgePosition.TOP, ConstraintType.COSMETIC, 80),
        ("front", EdgePosition.BOTTOM, "back", EdgePosition.BOTTOM, ConstraintType.COSMETIC, 80),
    ]
    
    for i, (pa, ea, pb, eb, ctype, priority) in enumerate(constraints_def):
        edge = EdgeConstraint(
            edge_id=i,
            panel_a=pa,
            edge_a=ea,
            panel_b=pb,
            edge_b=eb,
            constraint_type=ctype,
            priority=priority,
        )
        graph.add_edge(edge)
    
    return graph


def build_roblox_pants_graph_v2() -> ConstraintGraph:
    """Build constraint graph for Roblox Pants template."""
    graph = ConstraintGraph(
        garment_type="pants",
        template_size=(585, 559),
    )
    
    panels_def = [
        ("front", "Front Legs", (427, 74, 128, 128)),
        ("back", "Back Legs", (231, 74, 128, 128)),
        ("top", "Waist", (231, 8, 128, 64)),
        ("bottom", "Cuffs", (231, 204, 128, 64)),
        ("torso_left", "Waist Left", (165, 74, 64, 128)),
        ("torso_right", "Waist Right", (361, 74, 64, 128)),
        ("left_small_1", "Left Small 1", (217, 289, 64, 64)),
        ("right_small_1", "Right Small 1", (308, 289, 64, 64)),
        ("left_small_2", "Left Small 2", (217, 485, 64, 64)),
        ("right_small_2", "Right Small 2", (308, 485, 64, 64)),
        ("left_arm_outer", "Belt Left Outer", (19, 355, 64, 128)),
        ("left_leg_outer", "Left Leg Outer", (85, 355, 64, 128)),
        ("left_arm_inner", "Belt Left Inner", (151, 355, 64, 128)),
        ("left_leg_inner", "Left Leg Inner", (217, 355, 64, 128)),
        ("right_leg_inner", "Right Leg Inner", (308, 355, 64, 128)),
        ("right_arm_inner", "Belt Right Inner", (374, 355, 64, 128)),
        ("right_leg_outer", "Right Leg Outer", (440, 355, 64, 128)),
        ("right_arm_outer", "Belt Right Outer", (506, 355, 64, 128)),
    ]
    
    for pid, name, pos in panels_def:
        panel = PanelNode(panel_id=pid, name=name, template_position=pos)
        graph.add_panel(panel)
    
    constraints_def = [
        # Same topology as shirt
        ("front", EdgePosition.TOP, "top", EdgePosition.BOTTOM, ConstraintType.HARD, 0),
        ("front", EdgePosition.BOTTOM, "bottom", EdgePosition.TOP, ConstraintType.HARD, 0),
        ("front", EdgePosition.RIGHT, "torso_right", EdgePosition.LEFT, ConstraintType.HARD, 0),
        ("front", EdgePosition.LEFT, "torso_right", EdgePosition.RIGHT, ConstraintType.HARD, 0),
        
        ("back", EdgePosition.TOP, "top", EdgePosition.TOP, ConstraintType.HARD, 0),
        ("back", EdgePosition.BOTTOM, "bottom", EdgePosition.BOTTOM, ConstraintType.HARD, 0),
        ("back", EdgePosition.LEFT, "torso_left", EdgePosition.LEFT, ConstraintType.HARD, 0),
        ("back", EdgePosition.RIGHT, "torso_left", EdgePosition.RIGHT, ConstraintType.HARD, 0),
        
        ("torso_left", EdgePosition.RIGHT, "torso_right", EdgePosition.LEFT, ConstraintType.HARD, 10),
        
        ("top", EdgePosition.LEFT, "torso_left", EdgePosition.TOP, ConstraintType.HARD, 10),
        ("top", EdgePosition.RIGHT, "torso_right", EdgePosition.TOP, ConstraintType.HARD, 10),
        ("bottom", EdgePosition.LEFT, "torso_left", EdgePosition.BOTTOM, ConstraintType.HARD, 10),
        ("bottom", EdgePosition.RIGHT, "torso_right", EdgePosition.BOTTOM, ConstraintType.HARD, 10),
    ]
    
    for i, (pa, ea, pb, eb, ctype, priority) in enumerate(constraints_def):
        edge = EdgeConstraint(
            edge_id=i,
            panel_a=pa,
            edge_a=ea,
            panel_b=pb,
            edge_b=eb,
            constraint_type=ctype,
            priority=priority,
        )
        graph.add_edge(edge)
    
    return graph


def build_roblox_tshirt_graph_v2() -> ConstraintGraph:
    """Build constraint graph for T-Shirt (single panel)."""
    graph = ConstraintGraph(
        garment_type="tshirt",
        template_size=(512, 512),
    )
    
    panel = PanelNode(
        panel_id="front",
        name="Front",
        template_position=(0, 0, 512, 512)
    )
    graph.add_panel(panel)
    # No edges needed for single panel
    
    return graph


def build_constraint_graph_v2(garment_type: str) -> ConstraintGraph:
    """Build constraint graph based on garment type."""
    if garment_type == "tshirt":
        return build_roblox_tshirt_graph_v2()
    elif garment_type == "pants":
        return build_roblox_pants_graph_v2()
    else:  # shirt, jacket, hoodie
        return build_roblox_shirt_graph_v2()
