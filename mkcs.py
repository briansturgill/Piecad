import piecad
import inspect
import types
import sys
import io
from weasyprint import HTML

class FInfo:
    def __init__(self):
        pass

sections = {
        "piecad": "Info Functions",
        "piecad.bulk_ops": "Bulk Operations",
        "piecad.primitives_2d": "2d Primitives",
        "piecad.primitives_3d": "3d Primitives",
        "piecad.trigonometry": "Trigonometry (degrees)",
        "piecad.utilities": "Utility Functions",
        }
section_lists = {}

for k in sections.keys():
    section_lists[k] = []

all = []

def mk_fi(name, obj):
    fi = FInfo()
    fi.name = name
    fi.obj = obj
    fi.mod = obj.__module__
    fi.tag = ""
    fi.sig = str(inspect.signature(fi.obj))
    fi.sig = fi.sig.replace("piecad.", "")
    if fi.sig.find("->") == -1 and fi.name != "__init__":
        print("Missing return value", fi.name, fi.sig, file=sys.stderr)
    fi.long_ds = inspect.getdoc(fi.obj)
    if fi.long_ds != None:
        l = fi.long_ds.split('\n')
        if len(l) >= 1:
            fi.short_ds = l[0]
        else:
            fi.short_ds = None
    return fi

def doc_url(fi):
    l = fi.mod.split(".")
    if len(l) == 1:
        mod = "index"
    else:
        mod = l[1]
    url = f"{mod}.html#{fi.mod}.{fi.name}"
    return url

l = dir(piecad)
for i in l:
    if i[0] == '_':
        continue
    f = getattr(piecad, i)
    if inspect.isfunction(f) or hasattr(f, '__func__'): # isfunction doesn't detect classmember
        fi = mk_fi(i, f)
        section_lists[fi.obj.__module__].append(fi)
        all.append(fi)

all.sort(key=lambda x: x.name)

save_stdout = sys.stdout

def dump_cs_func(fi):
    if fi.name[0] == '_':
        return
    print("<p>")
    print(f"<pre><code>{fi.tag}{fi.name}{fi.sig}</code></pre>")
    if fi.short_ds != None:
        print("<br>")
        print(f"{fi.short_ds}")
    print("</p>")

def dump_cs_class(cname, c):
    print(f"<h2>class {cname}</h2>")
    mems = inspect.getmembers(c)
    for name, f in mems:
        if inspect.isfunction(f) or hasattr(f, '__func__'): # hasattr needed to detect classmethods
            fi = mk_fi(name, f)
            if cname == "Config":
                fi.tag = f"{cname}."
            dump_cs_func(fi)

def print_cheat_sheet():
    sys.stdout = io.StringIO()
    print("<!DOCTYPE html>")
    print("<html>")
    print("<head>")
    print("<style>")
    print("@page {")
    print("    size: letter landscape;")
    print("    margin: 5mm;")
    print("}")
    print(".container {")
    print("    column-count: 2;")
    print("    column-gap: 20px;")
    print("    column-rule: 1px solid lightblue;")
    print("}")
    print("code {")
    print("    white-space: pre-wrap;")
    print("    word-break: break-word;")
    print("    overflow-wrap: break-word;")
    print("    display: inline-block;")
    print("    background: #f4f4f4;")
    print("    padding: 2px 4px;")
    print("    border-radius: 4px;")
    print("    font-family: monospace;")
    print("}")
    print("pre {")
    print("    display: inline;")
    print("}")
    print("</style>")
    print("</head>")
    print("<body>")
    print("<div class=\"container\">")
    print("<h1>Piecad Cheatsheet</h1>")
    for k in sections.keys():
        print(f"<h2>{sections[k]}</h2>")
        section_lists[k].sort(key=lambda x: x.name)
        for fi in section_lists[k]:
            if inspect.isfunction(fi.obj):
                dump_cs_func(fi)
    dump_cs_class("Obj2d", getattr(piecad, "Obj2d", None))
    dump_cs_class("Obj3d", getattr(piecad, "Obj3d", None))
    dump_cs_class("Config", getattr(piecad, "Config", None))
    print("</div>")
    print("</body>")
    print("</html>")
    HTML(string=sys.stdout.getvalue()).write_pdf("docs/cs.pdf")
    sys.stdout.close()
    sys.stdout = save_stdout

def dump_qh_func(fi):
    if fi.name[0] == '_':
        return
    print("<p class=\"item\">")
    print(f"<a class=\"ahover\" href=\"{doc_url(fi)}\">")
    print(f"{fi.tag}{fi.name}")
    print("<span class=\"popup\">")
    print(f"<code>{fi.tag}{fi.name}{fi.sig}</code>")
    if fi.short_ds != None:
        print("<br>")
        print(f"{fi.short_ds}")
    print("</span>")
    print("</a>")
    print("</p>")

def dump_qh_class(cname, c):
    print(f"<h2>class {cname}</h2>")
    mems = inspect.getmembers(c)
    for name, f in mems:
        if inspect.isfunction(f) or hasattr(f, '__func__'): # hasattr needed to detect classmethods
            fi = mk_fi(name, f)
            if cname == "Config":
                fi.tag = f"{cname}."
            dump_qh_func(fi)

def print_qh():
    sys.stdout = open("docs/qh.html", "w")
    print("<!DOCTYPE html>")
    print("<html>")
    print("<head>")
    print("<style>")
    print(".item {")
    print("    margin: 5px 0;")
    print("}")
    print(".ahover {")
    print("    position: relative;")
    print("    cursor: pointer;")
    print("}")
    print(".popup {")
    print("    position: fixed;")
    print("    top: 5%;")
    print("    left: 50%;")
    print("    transform: translate(-50%, -50%);")
    print("    display: none;")
    print("    background-color: #f9f9f9;")
    print("    border: 1px solid #ccc;")
    print("    padding: 10px;")
    print("    z-index: 1;")
    print("    color: black;")
    print("    width: max-content;")
    print("    max-width: 100vw;")
    print("    box-sizing: border-box;")
    print("    padding: 10px;")
    print("    margin: auto;")
    print("}")
    print(".ahover:hover .popup {")
    print("    display: block;")
    print("}")
    print(".container {")
    print("    column-count: 6;")
    print("    column-gap: 10px;")
    print("    column-rule: 1px solid lightblue;")
    print("}")
    print("code {")
    print("    white-space: pre-wrap;")
    print("    word-break: break-word;")
    print("    overflow-wrap: break-word;")
    print("    display: inline-block;")
    print("    background: #f4f4f4;")
    print("    padding: 2px 4px;")
    print("    border-radius: 4px;")
    print("    font-family: monospace;")
    print("}")
    print("pre {")
    print("    display: inline;")
    print("}")
    print("</style>")
    print("</head>")
    print("<body>")
    print("<h1>Quick Help</h1>")
    print("<div class=\"container\">")
    print("<a href=\"https://www.github.com/briansturgill/Piecad\">Piecad github</a>")
    print("<br>")
    print("<a href=\"https://briansturgill.github.io/Piecad\">Piecad documentation</a>")
    for k in sections.keys():
        print(f"<h2>{sections[k]}</h2>")
        section_lists[k].sort(key=lambda x: x.name)
        for fi in section_lists[k]:
            if inspect.isfunction(fi.obj):
                dump_qh_func(fi)
    dump_qh_class("Obj2d", getattr(piecad, "Obj2d", None))
    dump_qh_class("Obj3d", getattr(piecad, "Obj3d", None))
    dump_qh_class("Config", getattr(piecad, "Config", None))
    print("</div>")
    print("</body>")
    print("</html>")
    sys.stdout.close()
    sys.stdout = save_stdout

print_cheat_sheet()
print_qh()