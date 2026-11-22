# pure_lib3mf 0.3.0

**No dependencies outside the Python standard library.** Pure Python 3MF reader/writer using `zipfile`, `xml.etree.ElementTree`, `dataclasses`, and `math`. The public API resembles the 3MF Consortium's Python wrapper where practical (`get_wrapper`, `CreateModel`, `AddMeshObject`, `AddBuildItem`, `QueryReader`, `QueryWriter`, material group methods). It does **not** load or require the native library.

This is an **independent, partial implementation of lib3mf**, not a drop-in replacement, an official library build, a formal ISO conformance validator, or a certified slicer integration.

## What's implemented

1. **Production Extension — reading:** Load multiple `.model` parts; resolve root `<item>` and `<component>` `p:path` references and OPC model relationships; remap duplicate per-part IDs for the in-memory API; preserve original paths/local IDs; reject forbidden cross-part references from non-root models.
2. **Package preservation:** Byte-identical output on unmodified imports. When editing, preserve unrelated ZIP entries, thumbnails, vendor slicer settings, relationship files, unknown XML attributes/children, Production UUIDs, and unknown resource types. Block edits to signed packages. Changing geometry may leave slicer-specific settings semantically stale; no claim is made that all vendor projects will remain functional.
3. **Production Extension — writing NEW packages:** `Model.EnableProductionExtension(True)` and `Model.AssignResourceToPart(resource, '/3D/Objects/part.model')`; create child XML model parts, cross-part `p:path` build/component references, required UUIDs, root and per-model relationships, and matching `[Content_Types].xml`. Repeated saves keep the generated UUIDs stable. Adding a new `.model` part to a *previously imported* package is not implemented; creation of new multi-file packages is supported.
4. **Materials and Properties Extension:** `Texture2D`, `Texture2DGroup`, `Tex2Coord`, `CompositeMaterials`, `CompositeConstituent`, `MultiPropertyGroup`, `MultiPropertyLayer`, plus existing base materials and color groups. Read, modify, and write `m:texture2d`, `m:texture2dgroup`/`m:tex2coord`, `m:compositematerials`/`m:composite`, `m:multiproperties`/`m:multi`; store JPEG/PNG bytes as package attachments and add 3D Texture relationships. Object-level properties and triangle `pid`/`p1`/`p2`/`p3` references can use these groups. Only 2D texture packaging is supported: no decoding or sampling of image pixels (not required for writing the image bytes).
5. **Validation and test tooling:** `MeshObject.ValidateGeometry()` checks indexed and geometrical degeneracy, duplicate faces, non-manifold edges/vertices, inconsistent winding, disconnected-shell signed volume, and optional pairwise triangle intersections (bounded by `max_pairs`). `Check3MFPackage()` checks ZIP integrity, the package manifest, relationships, model readability, and mesh diagnostics. `check_3mf.py` provides a JSON-report command-line interface.

## Installation

Copy `lib3mf.py` into your project and `import lib3mf`. No `pip install` step or native binary is needed. Tested with Python 3.13; targeted at Python 3.9+.

## Basic usage

```python
import lib3mf

wrapper = lib3mf.get_wrapper()
model = wrapper.CreateModel()
mesh = model.AddMeshObject()
mesh.SetName('Tetrahedron')
mesh.SetGeometry([(0,0,0),(1,0,0),(0,1,0),(0,0,1)],
                 [(0,2,1),(0,1,3),(0,3,2),(1,2,3)])
model.AddBuildItem(mesh, wrapper.GetIdentityTransform())
model.QueryWriter('3mf').WriteToFile('tetra.3mf')

loaded = wrapper.CreateModel()
loaded.QueryReader('3mf').ReadFromFile('tetra.3mf')
print(next(iter(loaded.GetMeshObjects())).GetTriangleCount())
```

## Multi-file Production package

```python
model = wrapper.CreateModel()
model.EnableProductionExtension(True)
part = model.AddMeshObject()
part.SetGeometry([(0,0,0),(1,0,0),(0,1,0),(0,0,1)],
                 [(0,2,1),(0,1,3),(0,3,2),(1,2,3)])
model.AssignResourceToPart(part, '/3D/Objects/part.model')
model.AddBuildItem(part)
model.QueryWriter('3mf').WriteToFile('production.3mf')
```

The child path is an **internal ZIP path**, not an external filename. Shared material/texture resource dependencies must be assigned to the same part as their mesh, and any non-root component references must remain local to that child part. Root components can refer to other model parts.

For a complete runnable textured example, see `example_advanced.py`. It embeds a tiny PNG as its image attachment and demonstrates a new Production package.

## Texture, composite and multiproperties example

```python
picture = model.AddAttachment('/3D/Textures/label.png', lib3mf.TEXTURE_REL)
picture.ReadFromFile('label.png')
tex = model.AddTexture2DFromAttachment(picture)
coords = model.AddTexture2DGroup(tex)
uv0 = coords.AddTex2Coord((0, 0))
uv1 = coords.AddTex2Coord((1, 0))
uv2 = coords.AddTex2Coord((0, 1))
mesh.SetTriangleProperties(0, lib3mf.TriangleProperties(coords.GetResourceID(),
                                                         [uv0, uv1, uv2]))
```

Also supports `AddCompositeMaterials(base_group)`, `.AddComposite([(property_id, ratio), ...])`, `AddMultiPropertyGroup()`, `.AddLayer(MultiPropertyLayer(resource_id, 'mix'|'multiply'))`, and `.AddMultiProperty([index_per_layer, ...])`.

## Validation

```python
mesh_report = mesh.ValidateGeometry(check_self_intersections=True, max_pairs=200000)
print(mesh_report.ok, mesh_report.signed_volume, mesh_report.to_dict())

with open('sample.3mf', 'rb') as f:
    package_report = lib3mf.Check3MFPackage(f.read())
print(package_report.to_dict())
```

For a CLI report:

```bash
python check_3mf.py my-model.3mf
python check_3mf.py --intersections my-model.3mf
```

Strict writer mode (`writer.SetStrictModeActive(True)`) rejects structurally invalid meshes and flagged geometric errors (other than optional self-intersections). The optional pairwise triangle intersection checker has worst-case quadratic complexity and skips checks beyond `max_pairs`; it is **not an exact robust computational geometry engine**, and triangles sharing vertex indices are excluded from intersection testing. No automatic repair is performed.

## Tests and fixtures

```bash
python -m unittest -v test_lib3mf test_production test_materials_production test_validation
python example_advanced.py
python check_3mf.py example_materials_production.3mf
```

The suite has **43 passing unit tests** covering core geometry, imported Production parts, foreign ZIP/XML preservation, new multi-part writes, texture bytes and links, material group editing, stable UUIDs, mesh diagnostics, and package checks. All included `.3mf` fixtures are **synthetic or generated by this module**.

For *external* interoperability testing, supply downloaded files from the [Consortium 3mf-samples repository](https://github.com/3MFConsortium/3mf-samples) and real 3MF files exported from PrusaSlicer, OrcaSlicer, Bambu Studio, or other slicers to `check_3mf.py`. They have **not** been tested in this delivery. Tests against actual slicer programs (opening and resaving in those programs) and formal XSD/ISO test-suite certification also remain outstanding.

## Important remaining limitations

- Not full native lib3mf parity. No beam lattices, slice stacks, volumetric/implicit meshes, encrypted content, production alternatives, advanced PBR/display-property interpretation, or all vendor-specific extensions.
- A copied slicer project setting can become inconsistent if you change geometry, IDs, assembly structure, or settings cross-references. Unknown ZIP parts are preserved as bytes, not semantically interpreted.
- The mesh validator detects many common errors but cannot guarantee printability, mesh repair, or formally correct solid geometry. It does not implement an exact 3D boolean-intersection algorithm.
- New standalone child `.model` parts cannot yet be inserted into an imported package; only new packages can assign parts. Edits of existing imported multi-file structures are supported.
- ZIP files are repacked when changed; unchanged ZIP members retain their uncompressed bytes, but not necessarily their original compressed representation.
- No actual Consortium example files or real slicer exports are bundled, and the test suite is not an independent certification tool.

## Primary specifications

- [3MF Core Specification](https://github.com/3MFConsortium/spec_core)
- [3MF Production Extension](https://github.com/3MFConsortium/spec_production)
- [3MF Materials and Properties Extension](https://github.com/3MFConsortium/spec_materials)
- [Official lib3mf bindings and documentation](https://github.com/3MFConsortium/lib3mf)

All runtime imports in the module come from Python's standard library.

## Official 3MF Consortium test suite regression runner

`test_3mf_conformance.py` runs against the Consortium's [test_suites repository](https://github.com/3MFConsortium/test_suites) (v2.4.1, as documented by the Consortium). Download or clone the corpus separately; this project does not redistribute its test cases. The runner takes an extracted directory **or a ZIP of the repository** (no need to unpack the ZIP):

```bash
# Run all known tests, with unsupported extensions reported as SKIP.
python test_3mf_conformance.py /path/to/test_suites \
    --json results.json --csv results.csv

# Focus on the core/production/material suites.
python test_3mf_conformance.py /path/to/test_suites.zip \
    --suites 2,3,5,6 --roundtrip rewrite

# List the cases first, or attempt extensions currently unsupported by this module.
python test_3mf_conformance.py /path/to/test_suites --list
python test_3mf_conformance.py /path/to/test_suites --include-unsupported
```

The suite harness uses folder names `positive_test_cases` / `negative_test_cases` as the expectation. **Positive** means the reader and our package checker accept the file and the optional round-trip preserves supported geometry and opaque attachments. **Negative** means at least one of the reader or package checker rejects it. This is useful for detecting regressions, but NOT a formal 3MF/XSD conformance score: neither the reader nor `Check3MFPackage()` implements the full specification, including all semantic constraints. The default `--roundtrip rewrite` injects temporary model metadata in memory before writing (never modifies the corpus) to ensure it really exercises the serializer; `--roundtrip copy` only exercises unchanged-package preservation, and `--roundtrip none` tests read/check alone. All three are safe for input files. All failures are printed; all cases and diagnostics are available in JSON/CSV reports.

Suites 1, 4, 7, 8, 10 and 11, and required unknown extensions, are SKIP by default. Use `--include-unsupported` to attempt them; passing a few of those tests does not imply extension implementation. Internal synthetic tests verify the runner's controls, but **the official conformance corpus has not been run** in this environment and no Consortium conformity is claimed.
