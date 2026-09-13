import sys
sys.path.insert(0, '.')
from src.compiler.nl_to_spec import convert_nl_to_spec
from main import compile_clothing

text = "oversized black hoodie with silver zipper and skull logo"
spec = convert_nl_to_spec(text)

print(f"Input: {text}")
print(f"Spec: {spec['name']} ({spec['garment']['type']})")
print(f"Logo: {spec['garment']['logo']}")

output_path = "output/user_hoodie.png"
template = compile_clothing(spec, output_path)
print(f"\nGenerated: {output_path} ({template.size[0]}x{template.size[1]})")
