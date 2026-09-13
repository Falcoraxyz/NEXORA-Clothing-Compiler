"""
Semantic Analyzer
Validates AST and produces Intermediate Representation (IR).
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field

from .dsl import (
    ProgramNode, GarmentNode, ColorNode, FitNode, MaterialNode,
    HoodNode, PocketNode, ZipperNode, SleeveNode, LogoNode, ExtrasNode
)


class SemanticError(Exception):
    def __init__(self, message: str, line: int = 0, col: int = 0):
        super().__init__(f"Semantic error at L{line}:{col}: {message}")
        self.line = line
        self.col = col


# ============================================================
# INTERMEDIATE REPRESENTATION (IR)
# ============================================================

@dataclass
class IROperation:
    """Single IR operation (LLVM-style)."""
    op: str  # "add", "remove", "modify", "set"
    target: str  # "logo", "pocket", "zipper", etc.
    params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 50  # 0=highest, 100=lowest


@dataclass
class IRModule:
    """Complete IR for a garment."""
    operations: List[IROperation] = field(default_factory=list)
    symbols: Dict[str, Any] = field(default_factory=dict)
    
    def add(self, target: str, params: Dict, priority: int = 50):
        self.operations.append(IROperation("add", target, params, priority))
    
    def remove(self, target: str, priority: int = 50):
        self.operations.append(IROperation("remove", target, {}, priority))
    
    def modify(self, target: str, params: Dict, priority: int = 50):
        self.operations.append(IROperation("modify", target, params, priority))
    
    def set(self, target: str, value: Any, priority: int = 50):
        self.operations.append(IROperation("set", target, {"value": value}, priority))
    
    def get_operations_sorted(self) -> List[IROperation]:
        """Get operations sorted by priority."""
        return sorted(self.operations, key=lambda op: op.priority)
    
    def optimize(self):
        """Optimize IR: remove redundant operations."""
        # Remove duplicate sets to same target
        seen = set()
        optimized = []
        for op in self.operations:
            key = (op.op, op.target)
            if op.op == "set":
                if key not in seen:
                    seen.add(key)
                    optimized.append(op)
            else:
                optimized.append(op)
        self.operations = optimized
    
    def diff(self, other: 'IRModule') -> 'IRModule':
        """Compute diff between two IRs for incremental rendering."""
        result = IRModule()
        
        self_targets = {(op.op, op.target) for op in self.operations}
        other_targets = {(op.op, op.target) for op in other.operations}
        
        # Added or modified
        for op in self.operations:
            if (op.op, op.target) not in other_targets:
                result.operations.append(op)
        
        return result


# ============================================================
# SEMANTIC ANALYZER
# ============================================================

class SemanticAnalyzer:
    """
    Validates AST and produces IR.
    
    Checks:
    - Valid garment type
    - Valid fit type
    - Valid material type
    - Valid pocket style
    - Valid zipper style
    - Valid logo style
    - Valid color roles
    - Valid scale/size ranges
    - Conflict detection (e.g., zipper + no zipper)
    - Incremental changes (via IR diff)
    """
    
    VALID_GARMENTS = {"shirt", "tshirt", "jacket", "hoodie", "pants"}
    VALID_FITS = {"regular", "oversized", "slim"}
    VALID_MATERIALS = {"heavy_cotton", "denim", "leather", "satin", "nylon", "wool"}
    VALID_POCKETS = {"none", "kangaroo", "chest", "side", "cargo", "flap", "welt", "patch"}
    VALID_ZIPPERS = {"none", "full", "half", "invisible"}
    VALID_LOGO_STYLES = {"none", "embroidery", "print", "patch", "graffiti", "throwup", "tag", "wildstyle"}
    VALID_POSITIONS = {"left_chest", "right_chest", "center", "back", "sleeve"}
    VALID_EXTRAS = {"chain", "belt", "patch", "dirt"}
    VALID_COLOR_ROLES = {"primary", "secondary", "accent"}
    
    def __init__(self):
        self.errors: List[SemanticError] = []
        self.warnings: List[str] = []
        self.ir = IRModule()
    
    def analyze(self, program: ProgramNode) -> IRModule:
        """Analyze program AST and produce IR."""
        self.errors = []
        self.warnings = []
        self.ir = IRModule()
        
        self._analyze_garment(program.garment)
        
        if self.errors:
            error_msg = "\n".join(str(e) for e in self.errors)
            raise SemanticError(f"Validation failed:\n{error_msg}")
        
        # Optimize IR
        self.ir.optimize()
        
        return self.ir
    
    def _analyze_garment(self, garment: GarmentNode):
        """Analyze garment node."""
        # Validate garment type
        if garment.garment_type not in self.VALID_GARMENTS:
            self.errors.append(SemanticError(
                f"Invalid garment type: {garment.garment_type}. "
                f"Valid: {self.VALID_GARMENTS}",
                garment.line, garment.col
            ))
        
        # Validate fit
        if garment.fit.value not in self.VALID_FITS:
            self.errors.append(SemanticError(
                f"Invalid fit: {garment.fit.value}. Valid: {self.VALID_FITS}",
                garment.fit.line, garment.fit.col
            ))
        
        # Validate material
        if garment.material.fabric not in self.VALID_MATERIALS:
            self.errors.append(SemanticError(
                f"Invalid material: {garment.material.fabric}. Valid: {self.VALID_MATERIALS}",
                garment.material.line, garment.material.col
            ))
        
        # Validate pocket
        if garment.pocket.style not in self.VALID_POCKETS:
            self.errors.append(SemanticError(
                f"Invalid pocket style: {garment.pocket.style}. Valid: {self.VALID_POCKETS}",
                garment.pocket.line, garment.pocket.col
            ))
        
        # Validate zipper
        if garment.zipper.style not in self.VALID_ZIPPERS:
            self.errors.append(SemanticError(
                f"Invalid zipper style: {garment.zipper.style}. Valid: {self.VALID_ZIPPERS}",
                garment.zipper.line, garment.zipper.col
            ))
        
        # Validate logo
        if garment.logo:
            if garment.logo.style not in self.VALID_LOGO_STYLES:
                self.errors.append(SemanticError(
                    f"Invalid logo style: {garment.logo.style}. Valid: {self.VALID_LOGO_STYLES}",
                    garment.logo.line, garment.logo.col
                ))
            if garment.logo.position not in self.VALID_POSITIONS:
                self.errors.append(SemanticError(
                    f"Invalid logo position: {garment.logo.position}. Valid: {self.VALID_POSITIONS}",
                    garment.logo.line, garment.logo.col
                ))
            if not (0.1 <= garment.logo.scale <= 0.6):
                self.errors.append(SemanticError(
                    f"Logo scale must be between 0.1 and 0.6, got {garment.logo.scale}",
                    garment.logo.line, garment.logo.col
                ))
        
        # Validate colors
        for color in garment.colors:
            if color.role not in self.VALID_COLOR_ROLES:
                self.errors.append(SemanticError(
                    f"Invalid color role: {color.role}. Valid: {self.VALID_COLOR_ROLES}",
                    color.line, color.col
                ))
        
        # Validate extras
        for extra in garment.extras.items:
            if extra not in self.VALID_EXTRAS:
                self.warnings.append(f"Unknown extra: {extra}")
        
        # Conflict detection
        self._check_conflicts(garment)
        
        # Generate IR (if no errors)
        if not self.errors:
            self._generate_ir(garment)
    
    def _check_conflicts(self, garment: GarmentNode):
        """Detect conflicting specifications."""
        # Zipper conflicts
        if garment.zipper.style == "none" and garment.zipper.color != "#C0C0C0":
            self.warnings.append("Zipper is none but color is specified")
        
        # Logo conflicts
        if garment.logo and garment.logo.style == "none" and garment.logo.motif:
            self.warnings.append("Logo style is none but motif is specified")
        
        # Pocket conflicts
        if garment.pocket.style == "none" and garment.pocket.size != 0.5:
            self.warnings.append("Pocket is none but size is specified")
        
        # Fit conflicts
        if garment.fit.value == "slim" and garment.fit.value == "oversized":
            self.errors.append(SemanticError(
                "Cannot be both slim and oversized",
                garment.fit.line, garment.fit.col
            ))
    
    def _generate_ir(self, garment: GarmentNode):
        """Generate Intermediate Representation."""
        # Set garment type
        self.ir.set("garment_type", garment.garment_type, priority=0)
        self.ir.set("fit", garment.fit.value, priority=0)
        self.ir.set("length", garment.length, priority=0)
        
        # Set colors
        for color in garment.colors:
            self.ir.set(f"color.{color.role}", color.hex_value, priority=10)
        
        # Set material
        self.ir.set("material.fabric", garment.material.fabric, priority=10)
        self.ir.set("material.roughness", garment.material.roughness, priority=10)
        self.ir.set("material.metallic", garment.material.metallic, priority=10)
        self.ir.set("material.normal_strength", garment.material.normal_strength, priority=10)
        
        # Set hood
        if garment.hood:
            self.ir.set("hood.enabled", garment.hood.enabled, priority=20)
        else:
            self.ir.set("hood.enabled", False, priority=20)
        
        # Set pocket
        if garment.pocket.style != "none":
            self.ir.add("pocket", {
                "style": garment.pocket.style,
                "position": garment.pocket.position,
                "size": garment.pocket.size
            }, priority=30)
        else:
            self.ir.set("pocket.enabled", False, priority=30)
        
        # Set zipper
        if garment.zipper.style != "none":
            self.ir.add("zipper", {
                "style": garment.zipper.style,
                "color": garment.zipper.color,
                "material": garment.zipper.material
            }, priority=40)
        else:
            self.ir.set("zipper.enabled", False, priority=40)
        
        # Set logo
        if garment.logo and garment.logo.style != "none" and garment.logo.motif:
            self.ir.add("logo", {
                "style": garment.logo.style,
                "motif": garment.logo.motif,
                "position": garment.logo.position,
                "scale": garment.logo.scale
            }, priority=50)
        else:
            self.ir.set("logo.enabled", False, priority=50)
        
        # Set sleeve
        self.ir.set("sleeve.length", garment.sleeve.length, priority=60)
        
        # Set stitch
        self.ir.set("stitch.style", garment.stitch.style, priority=70)
        self.ir.set("stitch.color", garment.stitch.color, priority=70)
        
        # Set extras
        if garment.extras.items:
            self.ir.add("extras", {"items": garment.extras.items}, priority=80)


def analyze(program: ProgramNode) -> IRModule:
    """Convenience function."""
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(program)
