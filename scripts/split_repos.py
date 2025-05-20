#!/usr/bin/env python3
"""
Split a plain-text list of Git repo URLs into N roughly equal JSON batches
and emit both the batch files and a GitHub-matrix descriptor (matrix.json).
"""
import json, math, pathlib, sys
repos_file, batch_size = sys.argv[1], int(sys.argv[2])
with open(repos_file) as f:
    repos = [l.strip() for l in f if l.strip()]
batches_dir = pathlib.Path("batches"); batches_dir.mkdir(exist_ok=True)
matrix = []
for i in range(math.ceil(len(repos) / batch_size)):
    chunk = repos[i*batch_size:(i+1)*batch_size]
    batch_path = batches_dir / f"batch{i}.json"
    json.dump(chunk, open(batch_path, "w"))
    matrix.append({"file": batch_path.name, "batch": i})
json.dump({"include": matrix}, open("matrix.json", "w"))
print(f"Created {len(matrix)} batches.")
