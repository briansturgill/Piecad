Piecad is intended to be quick to type with good default arguments.

Take a quick look at [QuickHelp](https://briansturgill.github.io/Piecad/qh.html)
to get a feel for what sort of calls are available.
When viewing QuickHelp, positioning you mouse over a name will give you
a signature of the function and a brief description.
Click the link attached to the name to see more details..

In addition to the various functions and classes that make up Piecad, there are
3 names of importance: `np` (a short hand for numpy), `trimesh` and `math`.

Numpy is a numeric package for Python... there are many useful things for
computational geometry. Trimesh handles meshes, the guts for 3d objects.
Math is the Python math library.  You won't need to import any of these,
they are used within Piecad and so are already imported, but as they are
used a lot, we passed the names into Piecad's namespace.

You also have all of Python's builtins available to you:
The functions abs, len, max, min, pow, round, and sum are particularly useful.

Python puts hypot, sqrt, ceil and floor in the math package, so you
will need to say `math.hypot`, `math.sqrt`, `math.ceil` and `math.floor` to use them.

Piecad uses degrees (rather than radians) exclusively in its API.
Thus, at the top level, we provide trig calls such as cos, sin, tan
and arc versions that work in degrees.
Degrees are much more pleasant to use when creating real world models.
You should avoid using the trig functions from the Python math package
as they work in radians.

A first program:

```python
from piecad import *    # Much more efficient to type when using a `*` import.

# center, by default centers at (0,0,0)
cb1 = cuboid((25, 20, 10)).center()
cb2 = cube(4).translate((0, 0, 5))
cb = union(cb1, cb2)
# corner, is like center, but it puts the minimum boundig box corner at *(0, 0, 0)"
cb = cb.corner().color("red")

# Technically `cube` is like a 3d square and `cuboid` is like a 3d rectangle.
# For convenience, `cube` and `cuboid` accept each others argument style.
# Also, `square` and `rectangle` behave similarly

view(cb1)  # Uses matplotlib to let you view a 3d model.  Works with 2D also (uses a very thin extrude).
view(cb2)  # This cues a view, you won't see it until program exit or a call to view_all_now()
view(cb)

# Saves a 3d model in your Downloads directory.
# Use "./cb.3mf" if you want it in the current directory.
save("cb.3mf", cb)

# Visual Studio Code and Pycharm have timeouts during "atexit" execution... 
# Use `view_all_now()` to view with out the timeout.
view_all_now()
```
