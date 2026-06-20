import sys
sys.path.insert(0, r"C:\dev\leadership\dataset\ori")

# Read the original script
with open(r"C:\dev\leadership\dataset\ori\generate_batch18.py", "r", encoding="utf-8") as f:
    code = f.read()

# Patch assertion to print and continue
code = code.replace(
    "assert all(20 <= len(s['text']) <= 120 for s in samples)",
    """for s in samples:
    if len(s['text']) < 20 or len(s['text']) > 120:
        print(f"SHORT/LONG len={len(s['text'])} id={s['label_id']} dt={s['data_type']} text={s['text']}")"""
)

# Remove write part
code = code.split("# Write")[0]

exec(code)
