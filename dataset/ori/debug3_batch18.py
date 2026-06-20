import sys
sys.path.insert(0, r"C:\dev\leadership\dataset\ori")

with open(r"C:\dev\leadership\dataset\ori\generate_batch18.py", "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace(
    "assert all(20 <= len(s['text']) <= 120 for s in samples)",
    """for s in samples:
    if len(s['text']) < 20 or len(s['text']) > 120:
        print(f"OFFENDER len={len(s['text'])} id={s['label_id']} dt={s['data_type']} text={s['text']}")"""
)
code = code.split("# Write")[0]

# Redirect stdout to file
with open(r"C:\dev\leadership\dataset\ori\debug_output.txt", "w", encoding="utf-8") as out:
    sys.stdout = out
    exec(code)
    sys.stdout = sys.__stdout__

print("Done")
