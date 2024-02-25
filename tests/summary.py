import sys
import json

# Compare two pytest benchmarks

if len(sys.argv) != 3:
    print("Usage: benchmark1.json benchmark2.json")


with open(sys.argv[1], "r") as f:
    b1 = json.load(f)

with open(sys.argv[2], "r") as f:
    b2 = json.load(f)

bmarks = {}


def ins_b(name, mean_in_ms, b_num):
    if name in bmarks:
        l = bmarks[name]
        l[b_num] = mean_in_ms
    else:
        l = [0, 0]
        l[b_num] = mean_in_ms
        bmarks[name] = l


for b in b1["benchmarks"]:
    ins_b(b["name"], b["stats"]["mean"] * 1000000, 0)
for b in b2["benchmarks"]:
    ins_b(b["name"], b["stats"]["mean"] * 1000000, 1)


l = list(bmarks.keys())


def sf(k1):
    return bmarks[k1][1]


l.sort(key=sf)


first = "Current"
second = "New"
header = f"{'Benchmark Name (times are means in us)':46}  {str.rjust(first,10)}  {str.rjust(second,10)}"
print(header)
print("---")
for k in l:
    v0 = bmarks[k][0]
    v1 = bmarks[k][1]
    print(f"{k:46}  {v0:10.2f}  {v1:10.2f}")
