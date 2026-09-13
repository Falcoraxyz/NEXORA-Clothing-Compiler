import sys
sys.path.insert(0, '.')
from src.compiler.dsl import parse_dsl, dsl_to_json
from main import compile_clothing

source = '''
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
'''

ast = parse_dsl(source)
json_spec = dsl_to_json(ast)

output_path = "output/dsl_hoodie.png"
template = compile_clothing(json_spec, output_path)
print(f"\nGenerated from DSL: {output_path} ({template.size[0]}x{template.size[1]})")
