# "Easy as Pie" CAD (Piecad)

For many years I used [OpenSCAD](https://www.openscad.org),
but the functional language it uses was often a hinderance and its speed
was poor. **Piecad** is my opinionted view of what a good, simple CAD API should look like.
It is written in [Python](https://www.python.org).
Its primary focus is the creation of models for 3D printing.

To install using [pip](https://pypi.org/project/piecad) (virtual environment recommended):

```sh
pip install piecad
```

[QuickHelp](https://briansturgill.github.io/Piecad/qh.html)

[Documentation](https://briansturgill.github.io/Piecad)

[Examples](examples/README.md)

[Printable CheatSheet](https://briansturgill.github.io/Piecad/cs.pdf)

Piecad has a `view` function which works like a 3d `print` (also does 2D).
[Matplotlib](https://matplotlib.org/) provides the window that displays the model/image from each `view` call.
You can use arrow keys to swtich between the models/images.

The viewer is automatically started when you use a `view` call inside Piecad.
If you are running your program inside PyCharm or Microsoft Visual Studio, add a call
to `view_all_now()` as the last line of your program.
Type 'h' in the view window for a list of commands.


## CREDITS

Piecad is based on [Manifold](https://github.com/elalish/manifold), a 3D CAD package written in C++.
Manifold incorporates [Clipper2](https://github.com/AngusJohnson/Clipper2) for 2D objects.
It also uses [`quickhull`](https://github.com/akuukka/quickhull) for 3d convex hulls.
You can see Manifold's web site for other packages that are used.

Piecad uses the [trimesh](https://github.com/mikedh/trimesh) package for mesh loading/saving and
for Piecad-Viewer.

Piecad uses [Matplotlib](https://matplotlib.org/) for visualizations.

We include two fonts: `Hack-Regular.tts` and `Roboto-Regular.tts`, see `piecad/fonts` for the licenses.

See the [file](https://raw.githubusercontent.com/briansturgill/Piecad/refs/heads/main/pyproject.toml) for more packages
that are used in Piecad.
