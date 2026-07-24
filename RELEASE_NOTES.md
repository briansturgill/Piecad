# 1.1.0

Changed the `save` function to have filenames that don't have path separators to be prepended
the the user's Downloads directory.

In other words, `save("file.obj", o)` will be the same as `save("/home/brian/Downloads/file.obj", o)`

Before, `save("file.obj", o)` would be the same as `save("./file.obj", o)`

This is a minor breaking changed, thus I incremented the middle version number.

If you were using `save` to save files to the current directory, prepend a `./` or `.\\`
to the filename to get the earlier behavior.
