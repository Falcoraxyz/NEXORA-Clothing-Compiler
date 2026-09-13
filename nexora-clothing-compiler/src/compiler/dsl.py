"""
NEXORA Clothing DSL
A domain-specific language for describing clothing.

Syntax:
    garment <type> {
        fit <fit_type>
        color <role> <hex>
        material <fabric>
        
        hood { ... }
        pocket <style> { ... }
        zipper <style> { ... }
        sleeve <length>
        
        logo {
            style <style>
            motif <text>
            position <pos>
            scale <float>
        }
        
        extras { <item>, <item>, ... }
    }

Example:
    garment hoodie {
        fit oversized
        color primary #111111
        color secondary #333333
        color accent #FF0000
        material heavy_cotton
        
        hood {
            enabled
        }
        
        pocket kangaroo {
            position center
            size 0.6
        }
        
        zipper full {
            color #C0C0C0
            material metal
        }
        
        logo {
            style graffiti
            motif "FLEX"
            position center
            scale 0.4
        }
        
        extras { chain }
    }
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================================
# TOKENS
# ============================================================

class TokenType(str, Enum):
    # Keywords
    GARMENT = "GARMENT"
    FIT = "FIT"
    COLOR = "COLOR"
    MATERIAL = "MATERIAL"
    HOOD = "HOOD"
    POCKET = "POCKET"
    ZIPPER = "ZIPPER"
    SLEEVE = "SLEEVE"
    LOGO = "LOGO"
    EXTRAS = "EXTRAS"
    STYLE = "STYLE"
    MOTIF = "MOTIF"
    POSITION = "POSITION"
    SCALE = "SCALE"
    SIZE = "SIZE"
    ENABLED = "ENABLED"
    LENGTH = "LENGTH"
    
    # Symbols
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    
    # Literals
    STRING = "STRING"
    FLOAT = "FLOAT"
    HEX_COLOR = "HEX_COLOR"
    IDENTIFIER = "IDENTIFIER"
    
    # Special
    EOF = "EOF"
    NEWLINE = "NEWLINE"


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    col: int
    
    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, L{self.line}:{self.col})"


# ============================================================
# AST NODES
# ============================================================

@dataclass
class ASTNode:
    """Base AST node."""
    line: int = 0
    col: int = 0


@dataclass
class ColorNode(ASTNode):
    role: str = "primary"
    hex_value: str = "#000000"


@dataclass
class FitNode(ASTNode):
    value: str = "regular"


@dataclass
class MaterialNode(ASTNode):
    fabric: str = "heavy_cotton"
    roughness: float = 0.7
    metallic: float = 0.0
    normal_strength: float = 0.5


@dataclass
class HoodNode(ASTNode):
    enabled: bool = True


@dataclass
class PocketNode(ASTNode):
    style: str = "none"
    position: str = "center"
    size: float = 0.5


@dataclass
class ZipperNode(ASTNode):
    style: str = "none"
    color: str = "#C0C0C0"
    material: str = "metal"


@dataclass
class SleeveNode(ASTNode):
    length: float = 1.0


@dataclass
class LogoNode(ASTNode):
    style: str = "none"
    motif: str = ""
    position: str = "left_chest"
    scale: float = 0.3


@dataclass
class ExtrasNode(ASTNode):
    items: List[str] = field(default_factory=list)


@dataclass
class StitchNode(ASTNode):
    style: str = "single"
    color: str = "#000000"
    distance: float = 3.0
    spacing: float = 2.0


@dataclass
class GarmentNode(ASTNode):
    garment_type: str = "shirt"
    fit: FitNode = field(default_factory=FitNode)
    colors: List[ColorNode] = field(default_factory=list)
    material: MaterialNode = field(default_factory=MaterialNode)
    hood: Optional[HoodNode] = None
    pocket: PocketNode = field(default_factory=PocketNode)
    zipper: ZipperNode = field(default_factory=ZipperNode)
    sleeve: SleeveNode = field(default_factory=SleeveNode)
    logo: Optional[LogoNode] = None
    extras: ExtrasNode = field(default_factory=ExtrasNode)
    stitch: StitchNode = field(default_factory=StitchNode)
    length: float = 1.0


@dataclass
class ProgramNode(ASTNode):
    garment: GarmentNode = field(default_factory=GarmentNode)


# ============================================================
# LEXER
# ============================================================

class LexerError(Exception):
    def __init__(self, message, line, col):
        super().__init__(f"Lexer error at L{line}:{col}: {message}")
        self.line = line
        self.col = col


class Lexer:
    """Tokenize clothing DSL source code."""
    
    KEYWORDS = {
        "garment": TokenType.GARMENT,
        "fit": TokenType.FIT,
        "color": TokenType.COLOR,
        "material": TokenType.MATERIAL,
        "hood": TokenType.HOOD,
        "pocket": TokenType.POCKET,
        "zipper": TokenType.ZIPPER,
        "sleeve": TokenType.SLEEVE,
        "logo": TokenType.LOGO,
        "extras": TokenType.EXTRAS,
        "style": TokenType.STYLE,
        "motif": TokenType.MOTIF,
        "position": TokenType.POSITION,
        "scale": TokenType.SCALE,
        "size": TokenType.SIZE,
        "enabled": TokenType.ENABLED,
        "length": TokenType.LENGTH,
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire source."""
        while self.pos < len(self.source):
            self._skip_whitespace()
            if self.pos >= len(self.source):
                break
            
            char = self.source[self.pos]
            
            if char == '\n':
                self._advance()
            elif char == '{':
                self._emit(TokenType.LBRACE)
                self._advance()
            elif char == '}':
                self._emit(TokenType.RBRACE)
                self._advance()
            elif char == '[':
                self._emit(TokenType.LBRACKET)
                self._advance()
            elif char == ']':
                self._emit(TokenType.RBRACKET)
                self._advance()
            elif char == ',':
                self._emit(TokenType.COMMA)
                self._advance()
            elif char == '#':
                self._read_hex_color()
            elif char == '"':
                self._read_string()
            elif char == '-' or char.isdigit():
                self._read_number()
            elif char.isalpha() or char == '_':
                self._read_identifier()
            else:
                raise LexerError(f"Unexpected character: {char!r}", self.line, self.col)
        
        self._emit(TokenType.EOF)
        return self.tokens
    
    def _advance(self):
        if self.pos < len(self.source) and self.source[self.pos] == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        self.pos += 1
    
    def _skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\r':
            self._advance()
    
    def _emit(self, token_type: TokenType, value: Any = None):
        self.tokens.append(Token(token_type, value, self.line, self.col))
    
    def _read_hex_color(self):
        """Read #RRGGBB color."""
        start = self.pos
        self._advance()  # skip #
        hex_str = ""
        while self.pos < len(self.source) and self.source[self.pos] in "0123456789ABCDEFabcdef":
            hex_str += self.source[self.pos]
            self._advance()
        if len(hex_str) != 6:
            raise LexerError(f"Invalid hex color: #{hex_str}", self.line, self.col)
        self._emit(TokenType.HEX_COLOR, f"#{hex_str.upper()}")
    
    def _read_string(self):
        """Read double-quoted string."""
        self._advance()  # skip opening "
        value = ""
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            value += self.source[self.pos]
            self._advance()
        if self.pos >= len(self.source):
            raise LexerError("Unterminated string", self.line, self.col)
        self._advance()  # skip closing "
        self._emit(TokenType.STRING, value)
    
    def _read_number(self):
        """Read integer or float."""
        start = self.pos
        if self.source[self.pos] == '-':
            self._advance()
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self._advance()
        if self.pos < len(self.source) and self.source[self.pos] == '.':
            self._advance()
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                self._advance()
        value = self.source[start:self.pos]
        self._emit(TokenType.FLOAT, float(value))
    
    def _read_identifier(self):
        """Read identifier or keyword."""
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self._advance()
        value = self.source[start:self.pos]
        
        # Check if keyword
        token_type = self.KEYWORDS.get(value.lower(), TokenType.IDENTIFIER)
        self._emit(token_type, value)


# ============================================================
# PARSER
# ============================================================

class ParserError(Exception):
    def __init__(self, message, token=None):
        loc = f" L{token.line}:{token.col}" if token else ""
        super().__init__(f"Parser error{loc}: {message}")
        self.token = token


class Parser:
    """Parse tokens into AST."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self) -> ProgramNode:
        """Parse program."""
        garment = self._parse_garment()
        return ProgramNode(garment=garment)
    
    def _current(self) -> Token:
        return self.tokens[self.pos]
    
    def _eat(self, token_type: TokenType) -> Token:
        token = self._current()
        if token.type != token_type:
            raise ParserError(f"Expected {token_type}, got {token.type}", token)
        self.pos += 1
        return token
    
    def _match(self, *types: TokenType) -> bool:
        return self._current().type in types
    
    def _parse_garment(self) -> GarmentNode:
        """Parse garment block."""
        token = self._eat(TokenType.GARMENT)
        node = GarmentNode(line=token.line, col=token.col)
        
        # Garment type
        if self._match(TokenType.IDENTIFIER):
            node.garment_type = self._eat(TokenType.IDENTIFIER).value
        elif self._match(TokenType.HOOD):
            node.garment_type = "hoodie"
            self._eat(TokenType.HOOD)
        
        self._eat(TokenType.LBRACE)
        
        while not self._match(TokenType.RBRACE):
            if self._match(TokenType.FIT):
                node.fit = self._parse_fit()
            elif self._match(TokenType.COLOR):
                node.colors.append(self._parse_color())
            elif self._match(TokenType.MATERIAL):
                node.material = self._parse_material()
            elif self._match(TokenType.HOOD):
                node.hood = self._parse_hood()
            elif self._match(TokenType.POCKET):
                node.pocket = self._parse_pocket()
            elif self._match(TokenType.ZIPPER):
                node.zipper = self._parse_zipper()
            elif self._match(TokenType.SLEEVE):
                node.sleeve = self._parse_sleeve()
            elif self._match(TokenType.LOGO):
                node.logo = self._parse_logo()
            elif self._match(TokenType.EXTRAS):
                node.extras = self._parse_extras()
            elif self._match(TokenType.STITCH):
                node.stitch = self._parse_stitch()
            else:
                raise ParserError(f"Unexpected token: {self._current()}", self._current())
        
        self._eat(TokenType.RBRACE)
        return node
    
    def _parse_fit(self) -> FitNode:
        self._eat(TokenType.FIT)
        token = self._eat(TokenType.IDENTIFIER)
        return FitNode(value=token.value, line=token.line, col=token.col)
    
    def _parse_color(self) -> ColorNode:
        self._eat(TokenType.COLOR)
        role = "primary"
        if self._match(TokenType.IDENTIFIER):
            role = self._eat(TokenType.IDENTIFIER).value
        hex_token = self._eat(TokenType.HEX_COLOR)
        return ColorNode(role=role, hex_value=hex_token.value, line=hex_token.line, col=hex_token.col)
    
    def _parse_material(self) -> MaterialNode:
        self._eat(TokenType.MATERIAL)
        token = self._eat(TokenType.IDENTIFIER)
        return MaterialNode(fabric=token.value, line=token.line, col=token.col)
    
    def _parse_hood(self) -> HoodNode:
        token = self._eat(TokenType.HOOD)
        node = HoodNode(enabled=True, line=token.line, col=token.col)
        if self._match(TokenType.LBRACE):
            self._eat(TokenType.LBRACE)
            if self._match(TokenType.ENABLED):
                self._eat(TokenType.ENABLED)
                node.enabled = True
            self._eat(TokenType.RBRACE)
        return node
    
    def _parse_pocket(self) -> PocketNode:
        self._eat(TokenType.POCKET)
        node = PocketNode()
        if self._match(TokenType.IDENTIFIER):
            node.style = self._eat(TokenType.IDENTIFIER).value
        if self._match(TokenType.LBRACE):
            self._eat(TokenType.LBRACE)
            while not self._match(TokenType.RBRACE):
                if self._match(TokenType.POSITION):
                    self._eat(TokenType.POSITION)
                    node.position = self._eat(TokenType.IDENTIFIER).value
                elif self._match(TokenType.SIZE):
                    self._eat(TokenType.SIZE)
                    node.size = self._eat(TokenType.FLOAT).value
                else:
                    raise ParserError(f"Unexpected token in pocket: {self._current()}", self._current())
            self._eat(TokenType.RBRACE)
        return node
    
    def _parse_zipper(self) -> ZipperNode:
        self._eat(TokenType.ZIPPER)
        node = ZipperNode()
        if self._match(TokenType.IDENTIFIER):
            node.style = self._eat(TokenType.IDENTIFIER).value
        if self._match(TokenType.LBRACE):
            self._eat(TokenType.LBRACE)
            while not self._match(TokenType.RBRACE):
                if self._match(TokenType.COLOR):
                    self._eat(TokenType.COLOR)
                    node.color = self._eat(TokenType.HEX_COLOR).value
                elif self._match(TokenType.MATERIAL):
                    self._eat(TokenType.MATERIAL)
                    node.material = self._eat(TokenType.IDENTIFIER).value
                else:
                    raise ParserError(f"Unexpected token in zipper: {self._current()}", self._current())
            self._eat(TokenType.RBRACE)
        return node
    
    def _parse_sleeve(self) -> SleeveNode:
        self._eat(TokenType.SLEEVE)
        length = self._eat(TokenType.FLOAT).value
        return SleeveNode(length=length)
    
    def _parse_logo(self) -> LogoNode:
        self._eat(TokenType.LOGO)
        node = LogoNode()
        self._eat(TokenType.LBRACE)
        while not self._match(TokenType.RBRACE):
            if self._match(TokenType.STYLE):
                self._eat(TokenType.STYLE)
                node.style = self._eat(TokenType.IDENTIFIER).value
            elif self._match(TokenType.MOTIF):
                self._eat(TokenType.MOTIF)
                node.motif = self._eat(TokenType.STRING).value
            elif self._match(TokenType.POSITION):
                self._eat(TokenType.POSITION)
                node.position = self._eat(TokenType.IDENTIFIER).value
            elif self._match(TokenType.SCALE):
                self._eat(TokenType.SCALE)
                node.scale = self._eat(TokenType.FLOAT).value
            else:
                raise ParserError(f"Unexpected token in logo: {self._current()}", self._current())
        self._eat(TokenType.RBRACE)
        return node
    
    def _parse_extras(self) -> ExtrasNode:
        self._eat(TokenType.EXTRAS)
        node = ExtrasNode()
        self._eat(TokenType.LBRACKET)
        while not self._match(TokenType.RBRACKET):
            if self._match(TokenType.IDENTIFIER):
                node.items.append(self._eat(TokenType.IDENTIFIER).value)
            if self._match(TokenType.COMMA):
                self._eat(TokenType.COMMA)
        self._eat(TokenType.RBRACKET)
        return node
    
    def _parse_stitch(self) -> StitchNode:
        self._eat(TokenType.STITCH)
        node = StitchNode()
        if self._match(TokenType.IDENTIFIER):
            node.style = self._eat(TokenType.IDENTIFIER).value
        return node


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def parse_dsl(source: str) -> ProgramNode:
    """Parse DSL source into AST."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def dsl_to_json(ast: ProgramNode) -> dict:
    """Convert AST to JSON spec (backward compatible)."""
    g = ast.garment
    
    # Build colors
    colors = {"primary": "#111111", "secondary": "#222222", "accent": "#FFFFFF"}
    for c in g.colors:
        colors[c.role] = c.hex_value
    
    # Build logo
    logo = None
    if g.logo and g.logo.style != "none" and g.logo.motif:
        logo = {
            "style": g.logo.style,
            "motif": g.logo.motif,
            "position": g.logo.position,
            "scale": g.logo.scale
        }
    
    return {
        "version": "1.0",
        "name": f"Custom {g.garment_type.title()}",
        "description": f"Generated from DSL",
        "theme": "custom",
        "garment": {
            "type": g.garment_type,
            "fit": g.fit.value,
            "hood": g.hood.enabled if g.hood else False,
            "sleeve_length": g.sleeve.length,
            "length": g.length,
            "color": colors,
            "material": {
                "fabric": g.material.fabric,
                "roughness": g.material.roughness,
                "metallic": g.material.metallic,
                "normal_strength": g.material.normal_strength
            },
            "zipper": {
                "style": g.zipper.style,
                "color": g.zipper.color,
                "material": g.zipper.material
            },
            "pocket": {
                "style": g.pocket.style,
                "position": g.pocket.position,
                "size": g.pocket.size
            },
            "stitch": {
                "type": g.stitch.style,
                "color": g.stitch.color,
                "distance_from_edge": g.stitch.distance,
                "spacing": g.stitch.spacing
            },
            "logo": logo,
            "extras": g.extras.items
        }
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    source = """
    garment hoodie {
        fit oversized
        color primary #111111
        color secondary #333333
        color accent #FF0000
        material heavy_cotton
        
        hood {
            enabled
        }
        
        pocket kangaroo {
            position center
            size 0.6
        }
        
        zipper full {
            color #C0C0C0
            material metal
        }
        
        logo {
            style graffiti
            motif "FLEX"
            position center
            scale 0.4
        }
        
        extras [chain]
    }
    """
    
    ast = parse_dsl(source)
    print("AST parsed successfully!")
    print(f"  Garment type: {ast.garment.garment_type}")
    print(f"  Fit: {ast.garment.fit.value}")
    print(f"  Colors: {[(c.role, c.hex_value) for c in ast.garment.colors]}")
    print(f"  Material: {ast.garment.material.fabric}")
    print(f"  Hood: {ast.garment.hood.enabled if ast.garment.hood else False}")
    print(f"  Pocket: {ast.garment.pocket.style}")
    print(f"  Zipper: {ast.garment.zipper.style}")
    print(f"  Logo: {ast.garment.logo.style} '{ast.garment.logo.motif}'" if ast.garment.logo else "  Logo: None")
    print(f"  Extras: {ast.garment.extras.items}")
    
    json_spec = dsl_to_json(ast)
    print(f"\nJSON spec generated:")
    import json
    print(json.dumps(json_spec, indent=2))
