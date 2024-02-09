import sys
import os

if len(sys.argv) != 2:
    print("Should have 1 argument.")
    sys.exit(1)


idx = sys.argv[1].rindex(".example")
example_name=sys.argv[1][:idx]

with open(sys.argv[1], "r") as f:
    example_code = f.readlines()

example_model = f"tmp/{example_name}.glb"
example_creator = f"tmp/{example_name}.py"
example_html = f"tmp/{example_name}.html"

template = f"""
<html>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<head>
<style>
body {{
	background-color: lightblue;
	color: black;
}}
pre {{
    margin: 0;
    text-align: left;
}}
.cd {{
	padding-top: 0px;
}}
.mv {{
	display: block;
	margin-left: auto;
	margin-right: auto;
	width: 300px;
}}
</style>
</head>
<body>
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
<!--link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/default.min.css">-->
<!--script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>-->
<!--script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>-->
<!--script>hljs.highlightAll();</script>-->
    <table width="100%">
    <tr>
    <td class="cd">
<code>
<pre>
{"".join(example_code)}
</pre>
</code>
    </td>
		</tr>
		<tr>
    <td>
		<div class="mv">
    <model-viewer src="../models/{example_name}.glb" ar ar-scale="fixed" interaction-prompt="none" camera-controls touch-action="pan-y" disable-zoom alt="Output of code example." shadow-intensity="2" camera-orbit="0deg 180deg 0" xr-environment></model-viewer>
		</div>
    </td>
    </tr>
    </table>
</body>
</html>
"""

with open(example_html, "w") as f:
    f.write(template)

with open(example_creator, "w") as f:
    f.write("from piecad import *\n")
    f.write("".join(example_code))
    f.write("if type(out) == Obj2d: out = out.extrude(0.2)\n")
    f.write("out = out.color(\"khaki\")\n")
    f.write(f"save(\"{example_model}\", out)\n")

ret = os.system(f"python {example_creator}")
sys.exit(0 if ret == 0 else 1)
