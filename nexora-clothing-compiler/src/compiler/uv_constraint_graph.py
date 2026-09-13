"""
UV Constraint Graph
Represents the topology of a Roblox garment template.
Each panel has edges that must match with adjacent panel edges.
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
class UVEdge:
    """Represents one edge of a panel."""
    edge_id: int
    panel_id: str
    position: EdgePosition
    # The pixels along this edge (row or column indices)
    # For a 512x512 panel, this would be 512 pixels
    pixels: Optional[List[Tuple[int, int, int]]] = None  # RGB tuples
    locked: bool = False  # If True, this edge is a constraint boundary

    def get_pixel_positions(self, panel_size: int) -> List[Tuple[int, int]]:
        """Get (x, y) positions for this edge."""
        positions = []
        if self.position == EdgePosition.TOP:
            positions = [(x, 0) for x in range(panel_size)]
        elif self.position == EdgePosition.BOTTOM:
            positions = [(x, panel_size - 1) for x in range(panel_size)]
        elif self.position == EdgePosition.LEFT:
            positions = [(0, y) for y in range(panel_size)]
        elif self.position == EdgePosition.RIGHT:
            positions = [(panel_size - 1, y) for y in range(panel_size)]
        return positions


@dataclass
class UVPanel:
    """Represents one panel in the UV template."""
    panel_id: str
    name: str
    # Position in the final template (x, y, width, height)
    template_position: Tuple[int, int, int, int]
    edges: Dict[EdgePosition, UVEdge] = field(default_factory=dict)
    # Interior region (excluding boundary pixels)
    interior_bounds: Optional[Tuple[int, int, int, int]] = None

    def __post_init__(self):
        if not self.edges:
            self.edges = {}
        if not self.interior_bounds:
            x, y, w, h = self.template_position
            # Interior is 1px inset from each edge
            self.interior_bounds = (x + 1, y + 1, w - 2, h - 2)


@dataclass
class EdgeConstraint:
    """Links two edges that must match."""
    constraint_id: int
    edge_a: Tuple[str, EdgePosition]  # (panel_id, position)
    edge_b: Tuple[str, EdgePosition]  # (panel_id, position)
    # Optional: flip direction (for mirrored panels)
    flip: bool = False


@dataclass
class UVConstraintGraph:
    """
    Complete UV topology for a garment type.
    Contains all panels and their edge constraints.
    """
    garment_type: str
    panels: Dict[str, UVPanel] = field(default_factory=dict)
    constraints: List[EdgeConstraint] = field(default_factory=list)
    panel_size: int = 64  # Each panel is 64x64 pixels in Roblox template

    def add_panel(self, panel: UVPanel):
        self.panels[panel.panel_id] = panel

    def add_constraint(self, constraint: EdgeConstraint):
        self.constraints.append(constraint)

    def get_shared_edges(self) -> List[Tuple[str, EdgePosition, str, EdgePosition]]:
        """Get all pairs of edges that must match."""
        shared = []
        for c in self.constraints:
            shared.append((c.edge_a[0], c.edge_a[1], c.edge_b[0], c.edge_b[1]))
        return shared

    def get_locked_edges(self) -> List[Tuple[str, EdgePosition]]:
        """Get all edges that are locked (boundary constraints)."""
        locked = []
        for panel in self.panels.values():
            for pos, edge in panel.edges.items():
                if edge.locked:
                    locked.append((panel.panel_id, pos))
        return locked

    def get_interior_panels(self) -> Dict[str, Tuple[int, int, int, int]]:
        """Get interior bounds for each panel (where AI can generate)."""
        interiors = {}
        for pid, panel in self.panels.items():
            interiors[pid] = panel.interior_bounds
        return interiors


def build_roblox_shirt_graph() -> UVConstraintGraph:
    """
    Build the UV constraint graph for a Roblox Shirt template.
    
    Roblox Shirt template layout (512x512):
    ┌─────────┬─────────┬─────────┬─────────┐
    │  Back   │  Top    │  Front  │ Bottom  │
    │ (L-Back)│ (L-Top) │ (L-Frn) │ (L-Bot) │
    ├─────────┼─────────┼─────────┼─────────┤
    │  Back   │  Top    │  Front  │ Bottom  │
    │ (R-Back)│ (R-Top) │ (R-Frn) │ (R-Bot) │
    ├─────────┼─────────┼─────────┼─────────┤
    │  L-Slv  │ L-Slv   │ R-Slv   │ R-Slv   │
    │  (Top)  │ (Bot)   │ (Top)   │ (Bot)   │
    └─────────┴─────────┴─────────┴─────────┘
    
    Each panel is 128x128 in the template.
    """
    graph = UVConstraintGraph(garment_type="shirt", panel_size=64)
    
    # Panel definitions: (id, name, template_position)
    # Template is 512x512, divided into 4x4 grid of 128x128 panels
    panels_def = [
        ("back_left", "Back Left", (0, 0, 128, 128)),
        ("top_left", "Top Left", (128, 0, 128, 128)),
        ("front_left", "Front Left", (256, 0, 128, 128)),
        ("bottom_left", "Bottom Left", (384, 0, 128, 128)),
        ("back_right", "Back Right", (0, 128, 128, 128)),
        ("top_right", "Top Right", (128, 128, 128, 128)),
        ("front_right", "Front Right", (256, 128, 128, 128)),
        ("bottom_right", "Bottom Right", (384, 128, 128, 128)),
        ("left_sleeve_top", "Left Sleeve Top", (0, 256, 128, 128)),
        ("left_sleeve_bottom", "Left Sleeve Bottom", (128, 256, 128, 128)),
        ("right_sleeve_top", "Right Sleeve Top", (256, 256, 128, 128)),
        ("right_sleeve_bottom", "Right Sleeve Bottom", (384, 256, 128, 128)),
    ]
    
    for pid, name, pos in panels_def:
        panel = UVPanel(
            panel_id=pid,
            name=name,
            template_position=pos,
        )
        # Add edges
        for edge_pos in EdgePosition:
            edge = UVEdge(
                edge_id=len(graph.constraints) * 4 + len(panel.edges),
                panel_id=pid,
                position=edge_pos,
            )
            panel.edges[edge_pos] = edge
        graph.add_panel(panel)
    
    # Define constraints (edges that must match)
    # Front panel edges connect to adjacent panels
    constraints_def = [
        # Front Left connects to Front Right along vertical center
        ("front_left", EdgePosition.RIGHT, "front_right", EdgePosition.LEFT),
        # Front Left connects to Top Left
        ("front_left", EdgePosition.TOP, "top_left", EdgePosition.BOTTOM),
        # Front Left connects to Bottom Left
        ("front_left", EdgePosition.BOTTOM, "bottom_left", EdgePosition.TOP),
        # Front Right connects to Top Right
        ("front_right", EdgePosition.TOP, "top_right", EdgePosition.BOTTOM),
        # Front Right connects to Bottom Right
        ("front_right", EdgePosition.BOTTOM, "bottom_right", EdgePosition.TOP),
        # Back Left connects to Back Right
        ("back_left", EdgePosition.RIGHT, "back_right", EdgePosition.LEFT),
        # Back Left connects to Top Left
        ("back_left", EdgePosition.TOP, "top_left", EdgePosition.TOP),  # mirrored
        # Back Right connects to Top Right
        ("back_right", EdgePosition.TOP, "top_right", EdgePosition.TOP),  # mirrored
        # Sleeve connections
        ("left_sleeve_top", EdgePosition.BOTTOM, "left_sleeve_bottom", EdgePosition.TOP),
        ("right_sleeve_top", EdgePosition.BOTTOM, "right_sleeve_bottom", EdgePosition.TOP),
        # Left sleeve connects to body
        ("left_sleeve_top", EdgePosition.RIGHT, "back_left", EdgePosition.LEFT),
        ("left_sleeve_bottom", EdgePosition.RIGHT, "top_left", EdgePosition.LEFT),
        # Right sleeve connects to body
        ("right_sleeve_top", EdgePosition.LEFT, "front_right", EdgePosition.RIGHT),
        ("right_sleeve_bottom", EdgePosition.LEFT, "bottom_right", EdgePosition.RIGHT),
    ]
    
    for i, (pa, ea, pb, eb) in enumerate(constraints_def):
        constraint = EdgeConstraint(
            constraint_id=i,
            edge_a=(pa, ea),
            edge_b=(pb, eb),
        )
        graph.add_constraint(constraint)
        # Mark edges as locked
        graph.panels[pa].edges[ea].locked = True
        graph.panels[pb].edges[eb].locked = True
    
    return graph


def build_roblox_pants_graph() -> UVConstraintGraph:
    """
    Build the UV constraint graph for Roblox Pants template.
    
    Roblox Pants template layout (512x512):
    ┌─────────┬─────────┬─────────┬─────────┐
    │ L-Leg   │ L-Leg   │ R-Leg   │ R-Leg   │
    │ (Back)  │ (Front) │ (Front) │ (Back)  │
    ├─────────┼─────────┼─────────┼─────────┤
    │ L-Leg   │ L-Leg   │ R-Leg   │ R-Leg   │
    │ (Back)  │ (Front) │ (Front) │ (Back)  │
    ├─────────┼─────────┼─────────┼─────────┤
    │ L-Leg   │ L-Leg   │ R-Leg   │ R-Leg   │
    │ (Back)  │ (Front) │ (Front) │ (Back)  │
    ├─────────┼─────────┼─────────┼─────────┤
    │ L-Leg   │ L-Leg   │ R-Leg   │ R-Leg   │
    │ (Back)  │ (Front) │ (Front) │ (Back)  │
    └─────────┴─────────┴─────────┴─────────┘
    """
    graph = UVConstraintGraph(garment_type="pants", panel_size=64)
    
    panels_def = [
        ("left_leg_back_1", "Left Leg Back 1", (0, 0, 128, 128)),
        ("left_leg_front_1", "Left Leg Front 1", (128, 0, 128, 128)),
        ("right_leg_front_1", "Right Leg Front 1", (256, 0, 128, 128)),
        ("right_leg_back_1", "Right Leg Back 1", (384, 0, 128, 128)),
        ("left_leg_back_2", "Left Leg Back 2", (0, 128, 128, 128)),
        ("left_leg_front_2", "Left Leg Front 2", (128, 128, 128, 128)),
        ("right_leg_front_2", "Right Leg Front 2", (256, 128, 128, 128)),
        ("right_leg_back_2", "Right Leg Back 2", (384, 128, 128, 128)),
        ("left_leg_back_3", "Left Leg Back 3", (0, 256, 128, 128)),
        ("left_leg_front_3", "Left Leg Front 3", (128, 256, 128, 128)),
        ("right_leg_front_3", "Right Leg Front 3", (256, 256, 128, 128)),
        ("right_leg_back_3", "Right Leg Back 3", (384, 256, 128, 128)),
        ("left_leg_back_4", "Left Leg Back 4", (0, 384, 128, 128)),
        ("left_leg_front_4", "Left Leg Front 4", (128, 384, 128, 128)),
        ("right_leg_front_4", "Right Leg Front 4", (256, 384, 128, 128)),
        ("right_leg_back_4", "Right Leg Back 4", (384, 384, 128, 128)),
    ]
    
    for pid, name, pos in panels_def:
        panel = UVPanel(
            panel_id=pid,
            name=name,
            template_position=pos,
        )
        for edge_pos in EdgePosition:
            edge = UVEdge(
                edge_id=len(graph.constraints) * 4 + len(panel.edges),
                panel_id=pid,
                position=edge_pos,
            )
            panel.edges[edge_pos] = edge
        graph.add_panel(panel)
    
    # Pants constraints - simplified for brevity
    constraints_def = [
        # Left leg connections
        ("left_leg_back_1", EdgePosition.RIGHT, "left_leg_front_1", EdgePosition.LEFT),
        ("left_leg_back_1", EdgePosition.BOTTOM, "left_leg_back_2", EdgePosition.TOP),
        ("left_leg_front_1", EdgePosition.BOTTOM, "left_leg_front_2", EdgePosition.TOP),
        ("left_leg_back_2", EdgePosition.BOTTOM, "left_leg_back_3", EdgePosition.TOP),
        ("left_leg_front_2", EdgePosition.BOTTOM, "left_leg_front_3", EdgePosition.TOP),
        ("left_leg_back_3", EdgePosition.BOTTOM, "left_leg_back_4", EdgePosition.TOP),
        ("left_leg_front_3", EdgePosition.BOTTOM, "left_leg_front_4", EdgePosition.TOP),
        # Right leg connections
        ("right_leg_front_1", EdgePosition.RIGHT, "right_leg_back_1", EdgePosition.LEFT),
        ("right_leg_front_1", EdgePosition.BOTTOM, "right_leg_front_2", EdgePosition.TOP),
        ("right_leg_back_1", EdgePosition.BOTTOM, "right_leg_back_2", EdgePosition.TOP),
        ("right_leg_front_2", EdgePosition.BOTTOM, "right_leg_front_3", EdgePosition.TOP),
        ("right_leg_back_2", EdgePosition.BOTTOM, "right_leg_back_3", EdgePosition.TOP),
        ("right_leg_front_3", EdgePosition.BOTTOM, "right_leg_front_4", EdgePosition.TOP),
        ("right_leg_back_3", EdgePosition.BOTTOM, "right_leg_back_4", EdgePosition.TOP),
    ]
    
    for i, (pa, ea, pb, eb) in enumerate(constraints_def):
        constraint = EdgeConstraint(
            constraint_id=i,
            edge_a=(pa, ea),
            edge_b=(pb, eb),
        )
        graph.add_constraint(constraint)
        graph.panels[pa].edges[ea].locked = True
        graph.panels[pb].edges[eb].locked = True
    
    return graph


# Factory function
def build_uv_graph(garment_type: str) -> UVConstraintGraph:
    """Build UV constraint graph based on garment type."""
    if garment_type in ("shirt", "tshirt", "jacket"):
        return build_roblox_shirt_graph()
    elif garment_type == "pants":
        return build_roblox_pants_graph()
    else:
        raise ValueError(f"Unknown garment type: {garment_type}")
