# 1.1.0

Changed the `save` function to have filenames that don't have path separators to be prepended
the the user's Downloads directory.

In other words, `save("file.obj", o)` will be the same as `save("/home/brian/Downloads/file.obj", o)`

Before, `save("file.obj", o)` would be the same as `save("./file.obj", o)`

This is a minor breaking changed, thus I incremented the middle version number.

If you were using `save` to save files to the current directory, prepend a `./` or `.\\`
to the filename to get the earlier behavior.

# 1.2.0

Added several new things:  hull_points, resize, minkowskis_sum, minkowski_difference, lithophane

Changed internal Path class to be retured by a primitives_2d `path` function.

Changed `set_default_segments()` to `Config.set_default_segments`.

# 1.3.0

Used special features of Manifold3d to allow a single object to have multiple colors.
This necessitated a breaking change in the Piecad-Viewer protocol.

# 1.4.0

Switched to using 64-bit Meshes in Manifold to match Manifold internals.

Added support for .piecadrc which can containing Config settings.

Trimesh color export in 3mf is broken, added direct export capability.
For color export, .3mf or .ply are the two best option.

Piecad has long had checking of 2d polygons. This release adds similar
support for 3d polyhedrons.  3d checking is far more difficult.
We use matplotlib to give visualization to found 3d problems.

# 2.0.0
Large number of additons and cleanups.
Experimental fillet and chamfer added.
matplotlib-based viewer.
Improved documentation.

# 2.0.5
Changes from Piecad 2.0.4:
  - Path.close() closes the active subpath and returns Path, not Obj2d.
  - Path.new_path(point) starts an independent open subpath.
  - Command records retain original line, quadratic/cubic Bezier and SVG arc
    parameters; polygon sampling is deferred until to_points()/to_Obj2d().
  - Path.to_Obj2d(include_open=False)
    constructs a single compound Obj2d from the eligible subpaths.

    Backward-incompatible: existing code using path(...).line_to(...).close()
    as an Obj2d must change the trailing call to .close().to_Obj2d().
