# "Easy as Pie" CAD (Piecad)

It is my opinionted view of what a good, simple CAD API should look like.

[Documentation](https://briansturgill.github.io/Piecad)

INSTALLATION IS STILL IN PROGRESS -- FINISHED SOON

For many years I used [OpenSCAD](https://www.openscad.org),
but the functional language it uses was often a hinderance and its speed
was poor.

## Credits

Piecad is based on [Manifold](https://github.com/elalish/manifold).
Manifold incorporates [Clipper2](https://github.com/AngusJohnson/Clipper2) for 2D objects.
It also uses [`quickhull`](https://github.com/akuukka/quickhull) for 3d convex hulls.
You can see Manifold's web site for other packages that are used.

Piecad also uses [isect_segments-bentley_ottmann](https://github.com/ideasman42/isect_segments-bentley_ottmann)
to check for polygon self intersections. Also, [fontTools](https://github.com/fonttools/fonttools) and [fontPens](https://github.com/robotools/fontPens) to support text.

We include two fonts: `Hack-Regular.tts` and `Roboto-Regular.tts`, see `piecad/fonts` for the licenses.
