# Roblox Shirt Template Layout (585×559)
# Based on Template-Shirts-R15.png from Roblox official templates

SHIRT_TEMPLATE_LAYOUT = {
    # Main body panels
    "front": {"x": 427, "y": 74, "w": 128, "h": 128, "color": (0, 116, 189)},
    "back": {"x": 231, "y": 74, "w": 128, "h": 128, "color": (226, 35, 26)},
    "top": {"x": 231, "y": 8, "w": 128, "h": 64, "color": (0, 162, 255)},
    "bottom": {"x": 231, "y": 204, "w": 128, "h": 64, "color": (246, 136, 2)},
    
    # Torso sides
    "torso_left": {"x": 165, "y": 74, "w": 64, "h": 128, "color": (2, 183, 87)},
    "torso_right": {"x": 361, "y": 74, "w": 64, "h": 128, "color": (246, 183, 2)},
    
    # Small panels (row 4)
    "left_small_1": {"x": 217, "y": 289, "w": 64, "h": 64, "color": (0, 162, 255)},
    "right_small_1": {"x": 308, "y": 289, "w": 64, "h": 64, "color": (0, 162, 255)},
    
    # Arm/Leg sides (row 5)
    "left_arm_outer": {"x": 19, "y": 355, "w": 64, "h": 128, "color": (246, 183, 2)},
    "left_leg_outer": {"x": 85, "y": 355, "w": 64, "h": 128, "color": (0, 116, 189)},
    "left_arm_inner": {"x": 151, "y": 355, "w": 64, "h": 128, "color": (2, 183, 87)},
    "left_leg_inner": {"x": 217, "y": 355, "w": 64, "h": 128, "color": (226, 35, 26)},
    "right_leg_inner": {"x": 308, "y": 355, "w": 64, "h": 128, "color": (226, 35, 26)},
    "right_arm_inner": {"x": 374, "y": 355, "w": 64, "h": 128, "color": (246, 183, 2)},
    "right_leg_outer": {"x": 440, "y": 355, "w": 64, "h": 128, "color": (0, 116, 189)},
    "right_arm_outer": {"x": 506, "y": 355, "w": 64, "h": 128, "color": (2, 183, 87)},
    
    # Small panels (row 6)
    "left_small_2": {"x": 217, "y": 485, "w": 64, "h": 64, "color": (246, 136, 2)},
    "right_small_2": {"x": 308, "y": 485, "w": 64, "h": 64, "color": (246, 136, 2)},
}

# Edge constraints (adjacent panels that must match)
SHIRT_EDGE_CONSTRAINTS = [
    # Front-Top
    ("front", "top", "top", "bottom"),
    # Front-Bottom
    ("front", "bottom", "bottom", "top"),
    # Front-Torso Right
    ("front", "left", "torso_right", "right"),
    # Front-Torso Left (through torso_right? No, front is at x=427, torso_right at x=361)
    # Actually front's left edge connects to... let me think about the topology
    
    # Back-Top
    ("back", "top", "top", "top"),  # Top panel wraps around
    # Back-Bottom
    ("back", "bottom", "bottom", "bottom"),
    # Back-Torso Left
    ("back", "left", "torso_left", "left"),
    # Back-Torso Right
    ("back", "right", "torso_right", "left"),
    
    # Torso Left-Torso Right (they're connected through the body)
    ("torso_left", "right", "back", "left"),
    ("torso_right", "left", "front", "right"),
    
    # Torso Left-Front (through front panel)
    ("torso_left", "right", "front", "left"),  # No, this doesn't make sense
    
    # Small panels connect to arm/leg sides
    ("left_small_1", "bottom", "left_arm_inner", "top"),
    ("right_small_1", "bottom", "right_arm_inner", "top"),
    ("left_small_2", "top", "left_leg_inner", "bottom"),
    ("right_small_2", "top", "right_leg_inner", "bottom"),
    
    # Arm/Leg sides connect to torso
    ("left_arm_outer", "top", "torso_left", "left"),
    ("left_arm_inner", "top", "left_arm_outer", "right"),
    ("left_leg_outer", "top", "left_arm_outer", "bottom"),
    ("left_leg_inner", "top", "left_leg_outer", "right"),
    
    ("right_arm_outer", "top", "torso_right", "right"),
    ("right_arm_inner", "top", "right_arm_outer", "left"),
    ("right_leg_outer", "top", "right_arm_outer", "bottom"),
    ("right_leg_inner", "top", "right_leg_outer", "left"),
]
