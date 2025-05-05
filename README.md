# "Easy as Pie" CAD (Piecad)

For many years I used [OpenSCAD](https://www.openscad.org),
but the functional language it uses was often a hinderance and its speed
was poor. **Piecad** is my opinionted view of what a good, simple CAD API should look like.
It is written in [Python](https://www.python.org).
Its primary focus is the creation of models for 3D printing.

To install (virtual environment recommended):

```sh
pip install piecad
```

[Documentation](https://briansturgill.github.io/Piecad)

[Piecad-Viewer](https://github.com/briansturgill/Piecad-Viewer):
Piecad has a `view` function which works like a 3d `print` (also does 2D).
Piecad-Viewer provides the window that displays the model/image from each `view` call.
You can use arrow keys to swtich between the models/images.

# My Piecad development environment.

I have one window where I run vi as my editor.

I have another window that is `piecad_viewer`.

I use the script below to watch for changes in all `*.py` files, the argument to
the script is the name of the main python file. When any python file is written, python
is ran on that main python file.

So I use `view` calls for what I need to see. Edit, then when I write, the `pywatch` script
below causes those views to be displayed.


```python
#!/usr/bin/env python3
import sys
import os
import time
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class MyEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        pass

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(event)
            os.system(f"python {sys.argv[1]}")

    def on_deleted(self, event):
        pass

    def on_moved(self, event):
        pass

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: pywatch _file_")
        sys.exit(1)
    path_to_watch = "."  # Current directory
    event_handler = MyEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```


## CREDITS

Piecad is based on [Manifold](https://github.com/elalish/manifold), a 3D CAD package written in C++.
Manifold incorporates [Clipper2](https://github.com/AngusJohnson/Clipper2) for 2D objects.
It also uses [`quickhull`](https://github.com/akuukka/quickhull) for 3d convex hulls.
You can see Manifold's web site for other packages that are used.

Piecad uses the [trimesh](https://github.com/mikedh/trimesh) package for mesh loading/saving and
for Piecad-Viewer.

Piecad also uses [isect_segments-bentley_ottmann](https://github.com/ideasman42/isect_segments-bentley_ottmann)
to check for polygon self intersections. Also, [fontTools](https://github.com/fonttools/fonttools) and [fontPens](https://github.com/robotools/fontPens) are used to support text.

We include two fonts: `Hack-Regular.tts` and `Roboto-Regular.tts`, see `piecad/fonts` for the licenses.
