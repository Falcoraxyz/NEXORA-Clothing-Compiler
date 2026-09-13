import sys
sys.path.insert(0, '.')
from src.compiler.nl_to_spec import convert_nl_to_spec
from main import compile_clothing

# Test dengan berbagai warna dan material
test_cases = [
    ("blue denim jacket", "slim fit blue denim jacket with silver zipper"),
    ("red hoodie", "oversized red hoodie with white logo print"),
    ("black leather pants", "slim fit black leather pants"),
    ("white cotton shirt", "regular white cotton shirt with black buttons"),
]

for name, text in test_cases:
    spec = convert_nl_to_spec(text)
    output_path = f"output/texture_{name.replace(' ', '_')}.png"
    template = compile_clothing(spec, output_path)
    print(f"Generated: {output_path}")
