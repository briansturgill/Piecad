"""Dependency-free 3MF model/package reader and writer (lib3mf-inspired API).

Uses Python's standard library only: zipfile, ElementTree, dataclasses, math.
Supports Core meshes/build items, Production multi-model references and generation,
Materials and Properties groups (textures, UV, composites, multiproperties),
conservative preservation of unknown ZIP/XML information, and mesh validation.

This is an independent partial implementation, not native lib3mf or a fully
certified 3MF specification implementation.

This file is AI translated to Python from: https://github.com/3MFConsortium/lib3mf/tree/master
The original code is: Copyright (C) 2019 3MF Consortium
The original code is licensed as [BSD 2-Clause "Simplified" License](https://github.com/3MFConsortium/lib3mf/blob/master/LICENSE).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from io import BytesIO
import copy
import hashlib
import math
from pathlib import PurePosixPath
import posixpath
import re
import uuid
from typing import Iterable
import warnings
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED, BadZipFile

__version__ = "0.3.0"
CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
MAT = "http://schemas.microsoft.com/3dmanufacturing/material/2015/02"
PROD = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
PKGREL = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT = "http://schemas.openxmlformats.org/package/2006/content-types"
START_REL = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
MODEL_CONTENT = "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"
TEXTURE_REL = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dtexture"
MODEL_PATH = "3D/3dmodel.model"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
ET.register_namespace("", CORE)
ET.register_namespace("m", MAT)
ET.register_namespace("p", PROD)


class ELib3MFException(Exception):
    """Error reporting compatible in spirit with lib3mf's Python exception."""


class Unsupported3MFError(ELib3MFException):
    """The requested 3MF feature is outside the implemented subset."""


class ModelUnit(IntEnum):
    MicroMeter = 0
    Micron = 0  # alias for convenience
    MilliMeter = 1
    CentiMeter = 2
    Inch = 3
    Foot = 4
    Meter = 5


_UNIT_NAMES = ("micron", "millimeter", "centimeter", "inch", "foot", "meter")


class PropertyType(IntEnum):
    NoPropertyType = 0
    BaseMaterial = 1
    TexCoord = 2
    Colors = 3
    Composite = 4
    Multi = 5


class ObjectType(IntEnum):
    Other = 0
    Model = 1
    Support = 2
    SolidSupport = 3
    Surface = 4


_TYPE_NAMES = {
    ObjectType.Other: "other",
    ObjectType.Model: "model",
    ObjectType.Support: "support",
    ObjectType.Surface: "surface",
    ObjectType.SolidSupport: "solidsupport",
}


def _triplet(seq, converter, label):
    vals = list(seq)
    if len(vals) != 3:
        raise ELib3MFException(f"{label} must have exactly 3 elements")
    return [converter(v) for v in vals]


def _finite(v):
    v = float(v)
    if not math.isfinite(v):
        raise ELib3MFException("Coordinates and transformations must be finite")
    return v


def _int(v):
    if isinstance(v, bool) or int(v) != v:
        raise ELib3MFException("Indices must be integers")
    return int(v)


def _num(v):
    return format(_finite(v), ".9g")


@dataclass
class Position:
    Coordinates: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])

    def __post_init__(self):
        self.Coordinates = _triplet(self.Coordinates, _finite, "Position")


@dataclass
class Triangle:
    Indices: list[int] = field(default_factory=lambda: [0, 0, 0])

    def __post_init__(self):
        self.Indices = _triplet(self.Indices, _int, "Triangle")


@dataclass
class TriangleProperties:
    ResourceID: int = 0
    PropertyIDs: list[int] = field(default_factory=lambda: [0, 0, 0])

    def __post_init__(self):
        self.ResourceID = _int(self.ResourceID)
        self.PropertyIDs = _triplet(self.PropertyIDs, _int, "TriangleProperties")


@dataclass
class Color:
    Red: int = 0
    Green: int = 0
    Blue: int = 0
    Alpha: int = 255

    def __post_init__(self):
        for key in ("Red", "Green", "Blue", "Alpha"):
            n = _int(getattr(self, key))
            if not 0 <= n <= 255:
                raise ELib3MFException("Color channels must be in [0, 255]")
            setattr(self, key, n)


@dataclass
class Tex2Coord:
    Coordinates: list[float] = field(default_factory=lambda: [0.0, 0.0])

    def __post_init__(self):
        if len(self.Coordinates) != 2:
            raise ELib3MFException("Texture UV requires two coordinates")
        self.Coordinates = [_finite(v) for v in self.Coordinates]


@dataclass
class CompositeConstituent:
    PropertyID: int
    MixingRatio: float

    def __post_init__(self):
        self.PropertyID = _int(self.PropertyID)
        self.MixingRatio = _finite(self.MixingRatio)
        if self.PropertyID < 0 or self.MixingRatio < 0:
            raise ELib3MFException("Composite material index/ratio must be nonnegative")


@dataclass
class MultiPropertyLayer:
    ResourceID: int
    BlendMethod: str = "mix"

    def __post_init__(self):
        self.ResourceID = _int(self.ResourceID)
        self.BlendMethod = str(self.BlendMethod).lower()
        if self.BlendMethod not in ("mix", "multiply"):
            raise ELib3MFException("Blend method must be mix or multiply")


@dataclass
class Transform:
    """lib3mf's four rows by three columns; translation is row 3."""

    Fields: list[list[float]] = field(
        default_factory=lambda: [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 0.0],
        ]
    )

    def __post_init__(self):
        if len(self.Fields) != 4:
            raise ELib3MFException("Transform must have 4 rows")
        self.Fields = [_triplet(r, _finite, "Transform row") for r in self.Fields]


@dataclass
class Box:
    MinCoordinate: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    MaxCoordinate: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])


def _pos(value):
    return Position(value.Coordinates if isinstance(value, Position) else value)


def _tri(value):
    return Triangle(value.Indices if isinstance(value, Triangle) else value)


def _prop(value):
    return TriangleProperties(value.ResourceID, value.PropertyIDs)


def _transform(value):
    return Transform(value.Fields if isinstance(value, Transform) else value)


def _xform_str(transform):
    return " ".join(_num(n) for row in transform.Fields for n in row)


def _parse_xform(s):
    if not s:
        return Transform()
    values = list(map(_finite, s.split()))
    if len(values) != 12:
        raise ELib3MFException("3MF transform requires 12 numbers")
    return Transform([values[i : i + 3] for i in range(0, 12, 3)])


def _apply(p, x):
    f = x.Fields
    v = p.Coordinates if isinstance(p, Position) else p
    return Position(
        [v[0] * f[0][i] + v[1] * f[1][i] + v[2] * f[2][i] + f[3][i] for i in range(3)]
    )


def _compose(inner, outer):
    # Apply 'inner', then 'outer': [x y z 1] * inner * outer
    a, b = inner.Fields, outer.Fields
    return Transform(
        [
            [
                sum(a[r][k] * b[k][col] for k in range(3))
                + (b[3][col] if r == 3 else 0)
                for col in range(3)
            ]
            for r in range(4)
        ]
    )


def _local(tag):
    return tag.split("}", 1)[-1]


def _tag(local, ns=CORE):
    return "{" + ns + "}" + local


def _xml_from_bytes(data):
    # ElementTree doesn't expand external entities; rejecting DTDs is safer.
    if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", data, re.I):
        raise ELib3MFException("DTD and entity declarations are not supported")
    try:
        return ET.fromstring(
            data,
            parser=ET.XMLParser(
                target=ET.TreeBuilder(insert_comments=True, insert_pis=True)
            ),
        )
    except ET.ParseError as e:
        raise ELib3MFException(f"Malformed 3MF XML: {e}") from e


def _rgba_hex(color):
    c = color if isinstance(color, Color) else Color(*color)
    return "#{:02X}{:02X}{:02X}{:02X}".format(c.Red, c.Green, c.Blue, c.Alpha)


def _hex_rgba(s):
    if not re.fullmatch(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?", s):
        raise ELib3MFException(f"Invalid 3MF color {s!r}")
    return Color(*bytes.fromhex(s[1:] + ("FF" if len(s) == 7 else "")))


@dataclass
class MetaData:
    namespace: str
    name: str
    value: str
    datatype: str = ""
    preserve: bool = False

    def GetNameSpace(self):
        return self.namespace

    def SetNameSpace(self, v):
        self.namespace = str(v)

    def GetName(self):
        return self.name

    def SetName(self, v):
        self.name = str(v)

    def GetValue(self):
        return self.value

    def SetValue(self, v):
        self.value = str(v)

    def GetType(self):
        return self.datatype

    def SetType(self, v):
        self.datatype = str(v)

    def GetMustPreserve(self):
        return self.preserve

    def SetMustPreserve(self, v):
        self.preserve = bool(v)

    def GetKey(self):
        return self.namespace + self.name


class MetaDataGroup:
    def __init__(self):
        self._items = []

    def GetMetaDataCount(self):
        return len(self._items)

    def GetMetaData(self, n):
        return self._items[n]

    def GetMetaDataByKey(self, ns, name):
        for v in self._items:
            if v.namespace == ns and v.name == name:
                return v
        raise ELib3MFException(f"Metadata not found: {ns}{name}")

    def AddMetaData(self, ns, name, value, datatype="", must_preserve=False):
        m = MetaData(str(ns), str(name), str(value), str(datatype), bool(must_preserve))
        self._items.append(m)
        return m

    def RemoveMetaData(self, item):
        self._items.remove(item)

    def RemoveMetaDataByIndex(self, n):
        del self._items[n]


def _write_metadata(parent, group, grouped=False):
    if not group._items:
        return
    root = ET.SubElement(parent, _tag("metadatagroup")) if grouped else parent
    for m in group._items:
        # With no namespace, use plain name; with namespace, QName to be emitted as prefix.
        key = ET.QName(m.namespace, m.name) if m.namespace else m.name
        attrs = {"name": key}
        if m.datatype:
            attrs["type"] = m.datatype
        if m.preserve:
            attrs["preserve"] = "true"
        el = ET.SubElement(root, _tag("metadata"), attrs)
        el.text = m.value


def _load_metadata(parent, group, grouped=False, namespaces=None):
    holder = parent.find(_tag("metadatagroup")) if grouped else parent
    if holder is None:
        return
    for node in holder.findall(_tag("metadata")):
        n = node.get("name", "")
        if n.startswith("{"):
            ns, name = n[1:].split("}", 1)
        elif ":" in n:
            prefix, name = n.split(":", 1)
            if prefix not in (namespaces or {}):
                raise ELib3MFException(f"Unbound metadata namespace prefix: {prefix}")
            ns = namespaces[prefix]
        else:
            ns, name = "", n
        group.AddMetaData(
            ns,
            name,
            node.text or "",
            node.get("type", ""),
            node.get("preserve", "false").lower() == "true",
        )


class _Iterator:
    def __init__(self, entries, current=-1):
        self._entries = list(entries)
        self._current = current

    def Count(self):
        return len(self._entries)

    def MoveNext(self):
        if self._current + 1 >= len(self._entries):
            self._current = len(self._entries)
            return False
        self._current += 1
        return True

    def MovePrevious(self):
        if self._current - 1 < 0:
            self._current = -1
            return False
        self._current -= 1
        return True

    def GetCurrent(self):
        if not 0 <= self._current < len(self._entries):
            raise ELib3MFException("Iterator not positioned on an element")
        return self._entries[self._current]

    def Clone(self):
        return _Iterator(self._entries, self._current)

    def GetCurrentMeshObject(self):
        return self.GetCurrent()

    def GetCurrentComponentsObject(self):
        return self.GetCurrent()

    def GetCurrentObject(self):
        return self.GetCurrent()

    def GetCurrentBuildItem(self):
        return self.GetCurrent()

    def GetCurrentBaseMaterialGroup(self):
        return self.GetCurrent()

    def GetCurrentColorGroup(self):
        return self.GetCurrent()

    def __iter__(self):
        while self.MoveNext():
            yield self.GetCurrent()


class Resource:
    def __init__(self, model, identifier):
        self._model = model
        self._id = identifier
        # A source .model part has its own local ID namespace.  _id is globally
        # unique inside this Python Model, _local_id is the on-disk resource ID.
        self._local_id = identifier
        self._package_path = model._root_part

    def GetResourceID(self):
        return self._id

    def GetLocalResourceID(self):
        return self._local_id

    def GetPackagePath(self):
        return "/" + self._package_path


class Object(Resource):
    def __init__(self, model, identifier):
        super().__init__(model, identifier)
        self._name, self._partnumber = "", ""
        self._type = ObjectType.Model
        self._metadata = MetaDataGroup()

    def GetName(self):
        return self._name

    def SetName(self, name):
        self._name = str(name)

    def GetPartNumber(self):
        return self._partnumber

    def SetPartNumber(self, number):
        self._partnumber = str(number)

    def GetType(self):
        return self._type

    def SetType(self, object_type):
        if isinstance(object_type, str):
            object_type = next(
                (k for k, v in _TYPE_NAMES.items() if v == object_type), None
            )
        self._type = ObjectType(object_type)

    def GetMetaDataGroup(self):
        return self._metadata

    def IsMeshObject(self):
        return isinstance(self, MeshObject)

    def IsComponentsObject(self):
        return isinstance(self, ComponentsObject)

    def IsLevelSetObject(self):
        return False

    def IsValid(self):
        if self._type == ObjectType.Other:
            return False
        if isinstance(self, MeshObject):
            return (
                self._type in (ObjectType.Surface, ObjectType.Support)
                or self.IsManifoldAndOriented()
            )
        return bool(self._components) and all(
            c.GetObjectResource().IsValid() for c in self._components
        )

    def GetOutbox(self):
        return _object_box(self, Transform(), set())


class MeshObject(Object):
    def __init__(self, model, identifier):
        super().__init__(model, identifier)
        self._vertices = []
        self._triangles = []
        self._object_property = None  # (resource_id, property_id)
        self._tri_props = []

    def GetVertexCount(self):
        return len(self._vertices)

    def GetTriangleCount(self):
        return len(self._triangles)

    def AddVertex(self, position):
        self._vertices.append(_pos(position))
        return len(self._vertices) - 1

    def GetVertex(self, index):
        return copy.deepcopy(self._vertices[index])

    def SetVertex(self, index, value):
        self._vertices[index] = _pos(value)

    def GetVertices(self):
        return copy.deepcopy(self._vertices)

    def _check_tri(self, triangle):
        t = _tri(triangle)
        if any(i < 0 or i >= len(self._vertices) for i in t.Indices):
            raise ELib3MFException("Triangle vertex index out of bounds")
        if len(set(t.Indices)) != 3:
            raise ELib3MFException("Triangle requires 3 distinct vertex indices")
        return t

    def AddTriangle(self, triangle):
        self._triangles.append(self._check_tri(triangle))
        self._tri_props.append(None)
        return len(self._triangles) - 1

    def GetTriangle(self, index):
        return copy.deepcopy(self._triangles[index])

    def SetTriangle(self, index, value):
        self._triangles[index] = self._check_tri(value)

    def GetTriangleIndices(self):
        return copy.deepcopy(self._triangles)

    def SetGeometry(self, vertices, indices):
        vs = [_pos(p) for p in vertices]
        ts = [_tri(t) for t in indices]
        for t in ts:
            if len(set(t.Indices)) != 3 or any(
                i < 0 or i >= len(vs) for i in t.Indices
            ):
                raise ELib3MFException("Invalid mesh triangle indices")
        self._vertices, self._triangles = vs, ts
        self._tri_props = [None] * len(ts)

    def SetObjectLevelProperty(self, res_id, prop_id):
        self._model._check_prop(res_id, prop_id)
        self._object_property = (_int(res_id), _int(prop_id))

    def GetObjectLevelProperty(self):
        if self._object_property is None:
            return (False, 0, 0)
        return (True, *self._object_property)

    def SetTriangleProperties(self, index, properties):
        p = _prop(properties)
        self._model._check_props(p)
        self._tri_props[index] = p
        if self._object_property is None:
            self._object_property = (p.ResourceID, p.PropertyIDs[0])

    def GetTriangleProperties(self, index):
        p = self._tri_props[index]
        if p is None:
            if self._object_property is None:
                return TriangleProperties()
            return TriangleProperties(
                self._object_property[0], [self._object_property[1]] * 3
            )
        return _prop(p)

    def SetAllTriangleProperties(self, properties):
        props = list(properties)
        if len(props) != len(self._triangles):
            raise ELib3MFException("Expected exactly one property per triangle")
        for n, prop in enumerate(props):
            self.SetTriangleProperties(n, prop)

    def GetAllTriangleProperties(self):
        return [self.GetTriangleProperties(i) for i in range(len(self._triangles))]

    def ClearAllProperties(self):
        self._object_property = None
        self._tri_props = [None] * len(self._triangles)

    def ValidateGeometry(
        self, *, epsilon=1e-9, check_self_intersections=False, max_pairs=200000
    ):
        return _validate_mesh(self, epsilon, check_self_intersections, max_pairs)

    def IsManifoldAndOriented(self):
        # Check edges (2 incident with opposite traversal) AND vertex link connectivity.
        edge_faces = {}
        incident = [[] for _ in self._vertices]
        for i, t in enumerate(self._triangles):
            a, b, c = t.Indices
            for v in (a, b, c):
                incident[v].append(i)
            for u, v in ((a, b), (b, c), (c, a)):
                key = (min(u, v), max(u, v))
                edge_faces.setdefault(key, []).append((i, u < v))
        if not self._triangles or any(
            len(faces) != 2 or faces[0][1] == faces[1][1]
            for faces in edge_faces.values()
        ):
            return False
        neighbors = [set() for _ in self._triangles]
        for faces in edge_faces.values():
            x, y = faces[0][0], faces[1][0]
            neighbors[x].add(y)
            neighbors[y].add(x)
        for faces in incident:
            if not faces:
                continue
            region = set(faces)
            seen = {faces[0]}
            pending = [faces[0]]
            while pending:
                for n in (neighbors[pending.pop()] & region) - seen:
                    seen.add(n)
                    pending.append(n)
            if seen != region:
                return False  # pinched/bow-tie non-manifold vertex
        return True


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: str
    message: str
    triangle_indices: tuple[int, ...] = ()


@dataclass
class ValidationReport:
    """Mesh diagnostic summary; validation never modifies the input mesh."""

    vertex_count: int
    triangle_count: int
    issues: list[ValidationIssue] = field(default_factory=list)
    signed_volume: float = 0.0
    surface_area: float = 0.0

    @property
    def ok(self):
        return not any(i.severity == "error" for i in self.issues)

    @property
    def is_printable(self):
        return self.ok

    def by_code(self, code):
        return [i for i in self.issues if i.code == code]

    def to_dict(self):
        return {
            "vertex_count": self.vertex_count,
            "triangle_count": self.triangle_count,
            "signed_volume": self.signed_volume,
            "surface_area": self.surface_area,
            "ok": self.ok,
            "issues": [
                {
                    "code": i.code,
                    "severity": i.severity,
                    "message": i.message,
                    "triangle_indices": list(i.triangle_indices),
                }
                for i in self.issues
            ],
        }


def _sub3(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot3(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross3(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _point_in_triangle(p, a, b, c, eps):
    n = _cross3(_sub3(b, a), _sub3(c, a))
    d = _dot3(n, n)
    if d <= eps * eps:
        return False
    if abs(_dot3(n, _sub3(p, a))) > eps * math.sqrt(d):
        return False
    u = _dot3(_cross3(_sub3(b, a), _sub3(p, a)), n) / d
    v = _dot3(_cross3(_sub3(p, a), _sub3(c, a)), n) / d
    w = 1.0 - u - v
    return min(u, v, w) >= -eps and max(u, v, w) <= 1 + eps


def _segment_hits_triangle(a, b, p, q, r, eps):
    normal = _cross3(_sub3(q, p), _sub3(r, p))
    direction = _sub3(b, a)
    denom = _dot3(normal, direction)
    if abs(denom) <= eps * math.sqrt(max(_dot3(normal, normal), 1e-30)):
        return False
    t = _dot3(normal, _sub3(p, a)) / denom
    if t < -eps or t > 1 + eps:
        return False
    point = tuple(a[i] + t * direction[i] for i in range(3))
    return _point_in_triangle(point, p, q, r, eps)


def _orient2(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _inside2(p, a, b, c, eps):
    vals = [_orient2(a, b, p), _orient2(b, c, p), _orient2(c, a, p)]
    return min(vals) >= -eps or max(vals) <= eps


def _segment_cross2(a, b, c, d, eps):
    ab1 = _orient2(a, b, c)
    ab2 = _orient2(a, b, d)
    cd1 = _orient2(c, d, a)
    cd2 = _orient2(c, d, b)
    return (
        (ab1 >= -eps and ab2 <= eps or ab2 >= -eps and ab1 <= eps)
        and (cd1 >= -eps and cd2 <= eps or cd2 >= -eps and cd1 <= eps)
        and max(min(a[0], b[0]), min(c[0], d[0]))
        <= min(max(a[0], b[0]), max(c[0], d[0])) + eps
        and max(min(a[1], b[1]), min(c[1], d[1]))
        <= min(max(a[1], b[1]), max(c[1], d[1])) + eps
    )


def _triangles_intersect(a, b, eps):
    n1 = _cross3(_sub3(a[1], a[0]), _sub3(a[2], a[0]))
    n2 = _cross3(_sub3(b[1], b[0]), _sub3(b[2], b[0]))
    if _dot3(n1, n1) <= eps * eps or _dot3(n2, n2) <= eps * eps:
        return False
    if all(abs(_dot3(n1, _sub3(q, a[0]))) <= eps * math.sqrt(_dot3(n1, n1)) for q in b):
        ax = max(range(3), key=lambda k: abs(n1[k]))
        idx = [k for k in range(3) if k != ax]
        a2 = [(p[idx[0]], p[idx[1]]) for p in a]
        b2 = [(p[idx[0]], p[idx[1]]) for p in b]
        return (
            any(
                _segment_cross2(a2[i], a2[(i + 1) % 3], b2[j], b2[(j + 1) % 3], eps)
                for i in range(3)
                for j in range(3)
            )
            or _inside2(a2[0], *b2, eps)
            or _inside2(b2[0], *a2, eps)
        )
    return any(
        _segment_hits_triangle(a[i], a[(i + 1) % 3], *b, eps) for i in range(3)
    ) or any(_segment_hits_triangle(b[i], b[(i + 1) % 3], *a, eps) for i in range(3))


def _validate_mesh(mesh, epsilon, check_self_intersections, max_pairs):
    eps = _finite(epsilon)
    if eps <= 0:
        raise ELib3MFException("Geometry tolerance must be positive")
    verts = [v.Coordinates for v in mesh._vertices]
    faces = [tuple(t.Indices) for t in mesh._triangles]
    result = ValidationReport(len(verts), len(faces))

    def warn(code, msg, ind=()):
        result.issues.append(ValidationIssue(code, "warning", msg, tuple(ind)))

    def error(code, msg, ind=()):
        result.issues.append(ValidationIssue(code, "error", msg, tuple(ind)))

    if not faces:
        error("empty_mesh", "Mesh contains no faces")
        return result
    edges = {}
    face_neighbors = [set() for _ in faces]
    incident = [set() for _ in verts]
    cross_norm = []
    seen_faces = {}
    areas = []
    for fi, (i, j, k) in enumerate(faces):
        if any(v < 0 or v >= len(verts) for v in (i, j, k)) or len({i, j, k}) < 3:
            error("invalid_index", "Triangle has invalid indices", (fi,))
            continue
        for v in (i, j, k):
            incident[v].add(fi)
        for u, v in ((i, j), (j, k), (k, i)):
            edges.setdefault((min(u, v), max(u, v)), []).append((fi, u < v))
        a, b, c = verts[i], verts[j], verts[k]
        normal = _cross3(_sub3(b, a), _sub3(c, a))
        mag = math.sqrt(_dot3(normal, normal))
        areas.append(mag * 0.5)
        cross_norm.append(normal)
        if mag <= eps * eps:
            error("zero_area", "Triangle has negligible area", (fi,))
        # Canonical positions catch duplicate triangles with distinct vertex IDs.
        key = tuple(sorted(tuple(verts[v]) for v in (i, j, k)))
        if key in seen_faces:
            error(
                "duplicate_triangle",
                "Coincident triangle geometry",
                (seen_faces[key], fi),
            )
        else:
            seen_faces[key] = fi
    result.surface_area = math.fsum(areas)
    for e, adj in edges.items():
        if len(adj) != 2:
            error(
                "nonmanifold_edge",
                f"Edge {e} belongs to {len(adj)} triangles",
                tuple(f for f, _ in adj),
            )
        elif adj[0][1] == adj[1][1]:
            error(
                "inconsistent_winding",
                f"Edge {e} has same directed winding",
                tuple(f for f, _ in adj),
            )
        if len(adj) == 2:
            f, g = adj[0][0], adj[1][0]
            face_neighbors[f].add(g)
            face_neighbors[g].add(f)
    for v, inc in enumerate(incident):
        if not inc:
            warn("unused_vertex", f"Vertex {v} is not used")
            continue
        seen = {next(iter(inc))}
        stack = list(seen)
        while stack:
            for f in face_neighbors[stack.pop()] & inc - seen:
                seen.add(f)
                stack.append(f)
        if seen != inc:
            error(
                "nonmanifold_vertex",
                f"Vertex {v} has disconnected face fans",
                tuple(sorted(inc)),
            )
    # Signed volume of individual edge-connected shells. Translate coordinates
    # by one vertex to avoid loss of precision on distant geometry.
    unseen = set(range(len(faces)))
    while unseen:
        root = min(unseen)
        stack = [root]
        unseen.remove(root)
        shell = []
        while stack:
            f = stack.pop()
            shell.append(f)
            for other in face_neighbors[f] & unseen:
                unseen.remove(other)
                stack.append(other)
        ref = verts[faces[shell[0]][0]]
        volume = math.fsum(
            _dot3(
                _sub3(verts[faces[f][0]], ref),
                _cross3(_sub3(verts[faces[f][1]], ref), _sub3(verts[faces[f][2]], ref)),
            )
            / 6.0
            for f in shell
        )
        result.signed_volume += volume
        closed = all(
            len(edges[(min(u, v), max(u, v))]) == 2
            for f in shell
            for u, v in (
                (faces[f][0], faces[f][1]),
                (faces[f][1], faces[f][2]),
                (faces[f][2], faces[f][0]),
            )
        )
        if closed:
            if volume < -(eps**3):
                error(
                    "negative_volume",
                    "Closed shell has inward orientation",
                    tuple(sorted(shell)),
                )
            elif abs(volume) <= eps**3:
                warn(
                    "zero_volume",
                    "Closed shell has approximately zero volume",
                    tuple(sorted(shell)),
                )
    if check_self_intersections:
        paircount = len(faces) * (len(faces) - 1) // 2
        if paircount > max_pairs:
            warn(
                "intersection_check_skipped",
                f"{paircount} pairs exceed max_pairs={max_pairs}",
            )
        else:
            bounds = []
            for face in faces:
                v = [verts[i] for i in face]
                bounds.append(
                    (
                        [min(p[k] for p in v) for k in range(3)],
                        [max(p[k] for p in v) for k in range(3)],
                    )
                )
            for i in range(len(faces)):
                for j in range(i + 1, len(faces)):
                    if set(faces[i]) & set(faces[j]):
                        continue
                    bi, bj = bounds[i], bounds[j]
                    if any(
                        bi[1][k] < bj[0][k] - eps or bj[1][k] < bi[0][k] - eps
                        for k in range(3)
                    ):
                        continue
                    if _triangles_intersect(
                        [verts[k] for k in faces[i]], [verts[k] for k in faces[j]], eps
                    ):
                        error(
                            "self_intersection",
                            "Non-adjacent triangles intersect",
                            (i, j),
                        )
    return result


class Component:
    def __init__(self, obj, transform=None):
        self._object = obj
        self._transform = _transform(transform or Transform())

    def GetObjectResource(self):
        return self._object

    def GetObjectResourceID(self):
        return self._object.GetResourceID()

    def HasTransform(self):
        return self._transform.Fields != Transform().Fields

    def GetTransform(self):
        return _transform(self._transform)

    def SetTransform(self, transform):
        self._transform = _transform(transform)


class ComponentsObject(Object):
    def __init__(self, model, identifier):
        super().__init__(model, identifier)
        self._components = []

    def AddComponent(self, obj, transform=None):
        self._model._ensure_object(obj)
        if obj is self or _references(obj, self, set()):
            raise ELib3MFException("Circular component references forbidden")
        c = Component(obj, transform)
        self._components.append(c)
        return c

    def GetComponent(self, index):
        return self._components[index]

    def GetComponentCount(self):
        return len(self._components)


def _references(obj, target, seen):
    if obj is target:
        return True
    if obj in seen or not isinstance(obj, ComponentsObject):
        return False
    seen.add(obj)
    return any(_references(c._object, target, seen) for c in obj._components)


class BaseMaterialGroup(Resource):
    def __init__(self, model, identifier):
        super().__init__(model, identifier)
        self._materials = []

    def GetCount(self):
        return len(self._materials)

    def GetAllPropertyIDs(self):
        return list(range(len(self._materials)))

    def AddMaterial(self, name, color):
        self._materials.append(
            [
                str(name),
                copy.deepcopy(color) if isinstance(color, Color) else Color(*color),
            ]
        )
        return len(self._materials) - 1

    def RemoveMaterial(self, index):
        raise Unsupported3MFError(
            "Removing/reindexing material properties is not implemented"
        )

    def GetName(self, index):
        return self._materials[index][0]

    def SetName(self, index, name):
        self._materials[index][0] = str(name)

    def GetDisplayColor(self, index):
        return copy.deepcopy(self._materials[index][1])

    def SetDisplayColor(self, index, color):
        self._materials[index][1] = (
            copy.deepcopy(color) if isinstance(color, Color) else Color(*color)
        )


class ColorGroup(Resource):
    def __init__(self, model, identifier):
        super().__init__(model, identifier)
        self._colors = []

    def GetCount(self):
        return len(self._colors)

    def GetAllPropertyIDs(self):
        return list(range(len(self._colors)))

    def AddColor(self, color):
        self._colors.append(
            copy.deepcopy(color) if isinstance(color, Color) else Color(*color)
        )
        return len(self._colors) - 1

    def GetColor(self, index):
        return copy.deepcopy(self._colors[index])

    def SetColor(self, index, color):
        self._colors[index] = (
            copy.deepcopy(color) if isinstance(color, Color) else Color(*color)
        )

    def RemoveColor(self, index):
        raise Unsupported3MFError(
            "Removing/reindexing color properties is not implemented"
        )


class Attachment:
    """In-memory OPC attachment; no third-party image or ZIP packages needed."""

    def __init__(self, model, path, relationship_type=TEXTURE_REL):
        self._model = model
        self._path = "/" + _clean_zip_name(path)
        self._relationship_type = relationship_type

    def GetPath(self):
        return self._path

    def GetRelationshipType(self):
        return self._relationship_type

    def ReadFromBuffer(self):
        path = _clean_zip_name(self._path)
        if path in self._model._attachment_data:
            return self._model._attachment_data[path]
        if self._model._original_package is not None:
            with ZipFile(BytesIO(self._model._original_package)) as zf:
                return zf.read(path)
        raise ELib3MFException("Missing attachment bytes: " + path)

    def WriteToBuffer(self, buffer):
        self._model._attachment_data[_clean_zip_name(self._path)] = bytes(buffer)

    def ReadFromFile(self, filename):
        with open(filename, "rb") as f:
            self.WriteToBuffer(f.read())

    def WriteToFile(self, filename):
        with open(filename, "wb") as f:
            f.write(self.ReadFromBuffer())


class Texture2D(Resource):
    def __init__(self, model, identifier):
        super().__init__(model, identifier)
        self._attachment = None
        self._content_type = "image/png"
        self._tile_u = self._tile_v = "wrap"
        self._filter = "auto"

    def GetAttachment(self):
        return self._attachment

    def SetAttachment(self, attachment):
        if (
            not isinstance(attachment, Attachment)
            or attachment._model is not self._model
        ):
            raise ELib3MFException("Texture attachment does not belong to model")
        self._attachment = attachment

    def GetContentType(self):
        return self._content_type

    def SetContentType(self, contenttype):
        if contenttype not in ("image/png", "image/jpeg"):
            raise ELib3MFException(
                "Texture content type must be image/png or image/jpeg"
            )
        self._content_type = contenttype

    def GetTileStyleUV(self):
        return self._tile_u, self._tile_v

    def SetTileStyleUV(self, u, v):
        if u not in ("wrap", "mirror", "clamp", "none") or v not in (
            "wrap",
            "mirror",
            "clamp",
            "none",
        ):
            raise ELib3MFException("Invalid texture tile style")
        self._tile_u, self._tile_v = u, v

    def GetFilter(self):
        return self._filter

    def SetFilter(self, value):
        if value not in ("auto", "linear", "nearest"):
            raise ELib3MFException("Invalid texture filtering style")
        self._filter = value


class Texture2DGroup(Resource):
    def __init__(self, model, identifier):
        super().__init__(model, identifier)
        self._texture = None
        self._coords = []

    def GetTexture2D(self):
        return self._texture

    def GetCount(self):
        return len(self._coords)

    def GetAllPropertyIDs(self):
        return list(range(self.GetCount()))

    def AddTex2Coord(self, coordinate):
        coord = Tex2Coord(
            coordinate.Coordinates if isinstance(coordinate, Tex2Coord) else coordinate
        )
        self._coords.append(coord)
        return len(self._coords) - 1

    def GetTex2Coord(self, index):
        return copy.deepcopy(self._coords[index])

    def RemoveTex2Coord(self, index):
        raise Unsupported3MFError(
            "Removing indexed UVs would invalidate triangle properties"
        )


class CompositeMaterials(Resource):
    def __init__(self, model, identifier):
        super().__init__(model, identifier)
        self._base = None
        self._matindices = []
        self._composites = []

    def GetBaseMaterialGroup(self):
        return self._base

    def GetCount(self):
        return len(self._composites)

    def GetAllPropertyIDs(self):
        return list(range(self.GetCount()))

    def AddComposite(self, constituents):
        pairs = []
        for x in constituents:
            if isinstance(x, CompositeConstituent):
                pairs.append(x)
            else:
                pairs.append(CompositeConstituent(*x))
        if not pairs:
            raise ELib3MFException("Composite must have constituent materials")
        if self._base is None:
            raise ELib3MFException("Composite lacks base material group")
        for x in pairs:
            if x.PropertyID >= self._base.GetCount():
                raise ELib3MFException("Composite references unknown base material")
            if x.PropertyID not in self._matindices:
                self._matindices.append(x.PropertyID)
        values = {x.PropertyID: x.MixingRatio for x in pairs}
        self._composites.append(values)
        return self.GetCount() - 1

    def GetComposite(self, index):
        values = self._composites[index]
        return [CompositeConstituent(k, values.get(k, 0.0)) for k in self._matindices]

    def RemoveComposite(self, index):
        raise Unsupported3MFError(
            "Removing indexed composites would invalidate triangles"
        )


class MultiPropertyGroup(Resource):
    def __init__(self, model, identifier):
        super().__init__(model, identifier)
        self._layers = []  # (resource, blendmethod), 1st blend method ignored
        self._multi = []

    def GetCount(self):
        return len(self._multi)

    def GetAllPropertyIDs(self):
        return list(range(self.GetCount()))

    def GetLayerCount(self):
        return len(self._layers)

    def AddLayer(self, layer):
        layer = (
            layer
            if isinstance(layer, MultiPropertyLayer)
            else MultiPropertyLayer(*layer)
        )
        group = self._model.GetResourceByID(layer.ResourceID)
        if not isinstance(
            group, (BaseMaterialGroup, ColorGroup, CompositeMaterials, Texture2DGroup)
        ):
            raise ELib3MFException("Invalid multiproperty layer group")
        if group._package_path != self._package_path:
            raise ELib3MFException("Multiproperty layer must be in same model part")
        self._layers.append((group, layer.BlendMethod))
        return len(self._layers) - 1

    def GetLayer(self, index):
        group, method = self._layers[index]
        return MultiPropertyLayer(group._id, method)

    def AddMultiProperty(self, indices):
        values = [_int(v) for v in indices]
        if len(values) != len(self._layers):
            raise ELib3MFException("One index required for each multiproperty layer")
        for i, (group, _) in zip(values, self._layers):
            if i < 0 or i >= group.GetCount():
                raise ELib3MFException("Invalid layer property index")
        self._multi.append(values)
        return len(self._multi) - 1

    def GetMultiProperty(self, index):
        return list(self._multi[index])

    def SetMultiProperty(self, index, indices):
        values = [_int(v) for v in indices]
        if len(values) != len(self._layers) or any(
            n < 0 or n >= grp.GetCount() for n, (grp, _) in zip(values, self._layers)
        ):
            raise ELib3MFException("Invalid multiproperty indices")
        self._multi[index] = values

    def RemoveMultiProperty(self, index):
        raise Unsupported3MFError(
            "Removing indexed multiproperties would invalidate triangles"
        )

    def RemoveLayer(self, index):
        raise Unsupported3MFError(
            "Removing multiproperty layers would invalidate properties"
        )


class BuildItem:
    def __init__(self, obj, transform):
        self._object = obj
        self._transform = _transform(transform)
        self._partnumber = ""
        self._metadata = MetaDataGroup()

    def GetObjectResource(self):
        return self._object

    def GetObjectResourceID(self):
        return self._object.GetResourceID()

    def GetObjectTransform(self):
        return _transform(self._transform)

    def SetObjectTransform(self, transform):
        self._transform = _transform(transform)

    def HasObjectTransform(self):
        return self._transform.Fields != Transform().Fields

    def SetPartNumber(self, number):
        self._partnumber = str(number)

    def GetPartNumber(self):
        return self._partnumber

    def GetMetaDataGroup(self):
        return self._metadata

    def GetOutbox(self):
        return _object_box(self._object, self._transform, set())


def _object_box(obj, xform, visiting):
    if obj in visiting:
        raise ELib3MFException("Circular components")
    if isinstance(obj, MeshObject):
        if not obj._vertices:
            return Box()
        ps = [_apply(v, xform).Coordinates for v in obj._vertices]
        return Box(
            [min(v[i] for v in ps) for i in range(3)],
            [max(v[i] for v in ps) for i in range(3)],
        )
    visiting = visiting | {obj}
    boxes = [
        _object_box(c._object, _compose(c._transform, xform), visiting)
        for c in obj._components
    ]
    if not boxes:
        return Box()
    return Box(
        [min(b.MinCoordinate[i] for b in boxes) for i in range(3)],
        [max(b.MaxCoordinate[i] for b in boxes) for i in range(3)],
    )


class Model:
    def __init__(self):
        self._resources = {}  # insertion order (includes material and object IDs)
        self._next_id = 1
        self._build = []
        self._unit = ModelUnit.MilliMeter
        self._language = "und"
        self._metadata = MetaDataGroup()
        self._warnings = []
        self._root_part = MODEL_PATH
        self._original_package = None
        self._attachment_data = {}
        self._original_attachment_states = {}
        self._production_enabled = False
        self._build_uuid = None
        self._original_parts = {}
        self._baseline_state = None
        self._deferred_components = []
        self._deferred_build = []

    def _add(self, cls, id_=None):
        if id_ is None:
            id_ = self._next_id
        id_ = _int(id_)
        if id_ <= 0 or id_ >= 2**31 or id_ in self._resources:
            raise ELib3MFException("Duplicate or invalid resource ID")
        obj = cls(self, id_)
        self._resources[id_] = obj
        self._next_id = max(self._next_id, id_ + 1)
        return obj

    def _ensure_object(self, obj):
        if (
            not isinstance(obj, Object)
            or obj._model is not self
            or self._resources.get(obj._id) is not obj
        ):
            raise ELib3MFException("Object does not belong to this model")

    def _check_prop(self, rid, pid):
        obj = self._resources.get(_int(rid))
        if (
            not isinstance(
                obj,
                (
                    ColorGroup,
                    BaseMaterialGroup,
                    Texture2DGroup,
                    CompositeMaterials,
                    MultiPropertyGroup,
                ),
            )
            or not 0 <= _int(pid) < obj.GetCount()
        ):
            raise ELib3MFException(f"Invalid property reference: {rid}:{pid}")

    def _check_props(self, props):
        for i in props.PropertyIDs:
            self._check_prop(props.ResourceID, i)

    def SetUnit(self, unit):
        if isinstance(unit, str):
            if unit not in _UNIT_NAMES:
                raise ELib3MFException("Unknown 3MF unit")
            unit = _UNIT_NAMES.index(unit)
        self._unit = ModelUnit(unit)

    def GetUnit(self):
        return self._unit

    def SetLanguage(self, lang):
        self._language = str(lang)

    def GetLanguage(self):
        return self._language

    def AddMeshObject(self):
        return self._add(MeshObject)

    def AddComponentsObject(self):
        return self._add(ComponentsObject)

    def AddBaseMaterialGroup(self):
        return self._add(BaseMaterialGroup)

    def AddColorGroup(self):
        return self._add(ColorGroup)

    def AddAttachment(self, uri, relationship_type=TEXTURE_REL):
        return Attachment(self, uri, relationship_type)

    def AddTexture2DFromAttachment(self, attachment):
        if not isinstance(attachment, Attachment) or attachment._model is not self:
            raise ELib3MFException("Attachment is not in model")
        result = self._add(Texture2D)
        result.SetAttachment(attachment)
        result.SetContentType(
            "image/jpeg"
            if attachment.GetPath().lower().endswith((".jpg", ".jpeg"))
            else "image/png"
        )
        return result

    def AddTexture2DGroup(self, texture):
        if not isinstance(texture, Texture2D) or texture._model is not self:
            raise ELib3MFException("Texture is not in model")
        result = self._add(Texture2DGroup)
        result._texture = texture
        return result

    def AddCompositeMaterials(self, base):
        if not isinstance(base, BaseMaterialGroup) or base._model is not self:
            raise ELib3MFException("Base material group is not in model")
        result = self._add(CompositeMaterials)
        result._base = base
        return result

    def AddMultiPropertyGroup(self):
        return self._add(MultiPropertyGroup)

    def EnableProductionExtension(self, enabled=True):
        self._production_enabled = bool(enabled)

    def AssignResourceToPart(self, resource, path):
        """Place a resource in a child model file for a new production package.

        Assign material/texture dependencies to the same part as their mesh.
        Existing imported multi-file models retain their own local IDs.
        """
        if self._resources.get(getattr(resource, "_id", None)) is not resource:
            raise ELib3MFException("Unknown resource")
        path = _clean_zip_name(path)
        if not path.lower().endswith(".model"):
            raise ELib3MFException("Production model part must end with .model")
        if self._original_package is not None and path not in self._original_parts:
            raise Unsupported3MFError(
                "Creating brand-new model part in imported package is not supported"
            )
        resource._package_path = path
        self._production_enabled = self._production_enabled or path != self._root_part
        used = {
            r._local_id
            for r in self._resources.values()
            if r is not resource and r._package_path == path
        }
        if resource._local_id in used:
            resource._local_id = max(used, default=0) + 1

    def GetTexture2DByID(self, n):
        return self._get_typed(n, Texture2D)

    def GetTexture2DGroupByID(self, n):
        return self._get_typed(n, Texture2DGroup)

    def GetCompositeMaterialsByID(self, n):
        return self._get_typed(n, CompositeMaterials)

    def GetMultiPropertyGroupByID(self, n):
        return self._get_typed(n, MultiPropertyGroup)

    def _get_typed(self, n, cls):
        obj = self.GetResourceByID(n)
        if not isinstance(obj, cls):
            raise ELib3MFException("Resource is not a " + cls.__name__)
        return obj

    def GetTexture2Ds(self):
        return _Iterator(
            r for r in self._resources.values() if isinstance(r, Texture2D)
        )

    def GetTexture2DGroups(self):
        return _Iterator(
            r for r in self._resources.values() if isinstance(r, Texture2DGroup)
        )

    def GetCompositeMaterials(self):
        return _Iterator(
            r for r in self._resources.values() if isinstance(r, CompositeMaterials)
        )

    def GetMultiPropertyGroups(self):
        return _Iterator(
            r for r in self._resources.values() if isinstance(r, MultiPropertyGroup)
        )

    def GetResourceByID(self, n):
        if n not in self._resources:
            raise ELib3MFException(f"Unknown resource ID {n}")
        return self._resources[n]

    def GetPropertyTypeByID(self, n):
        obj = self.GetResourceByID(n)
        if isinstance(obj, BaseMaterialGroup):
            return PropertyType.BaseMaterial
        if isinstance(obj, ColorGroup):
            return PropertyType.Colors
        if isinstance(obj, Texture2DGroup):
            return PropertyType.TexCoord
        if isinstance(obj, CompositeMaterials):
            return PropertyType.Composite
        if isinstance(obj, MultiPropertyGroup):
            return PropertyType.Multi
        return PropertyType.NoPropertyType

    def GetMeshObjectByID(self, n):
        obj = self.GetResourceByID(n)
        if not isinstance(obj, MeshObject):
            raise ELib3MFException("Resource is not a mesh")
        return obj

    def GetComponentsObjectByID(self, n):
        obj = self.GetResourceByID(n)
        if not isinstance(obj, ComponentsObject):
            raise ELib3MFException("Resource is not components")
        return obj

    def GetBaseMaterialGroupByID(self, n):
        obj = self.GetResourceByID(n)
        if not isinstance(obj, BaseMaterialGroup):
            raise ELib3MFException("Resource is not base materials")
        return obj

    def GetColorGroupByID(self, n):
        obj = self.GetResourceByID(n)
        if not isinstance(obj, ColorGroup):
            raise ELib3MFException("Resource is not a color group")
        return obj

    def GetResources(self):
        return _Iterator(self._resources.values())

    def GetObjects(self):
        return _Iterator(x for x in self._resources.values() if isinstance(x, Object))

    def GetMeshObjects(self):
        return _Iterator(
            x for x in self._resources.values() if isinstance(x, MeshObject)
        )

    def GetComponentsObjects(self):
        return _Iterator(
            x for x in self._resources.values() if isinstance(x, ComponentsObject)
        )

    def GetBaseMaterialGroups(self):
        return _Iterator(
            x for x in self._resources.values() if isinstance(x, BaseMaterialGroup)
        )

    def GetColorGroups(self):
        return _Iterator(
            x for x in self._resources.values() if isinstance(x, ColorGroup)
        )

    def AddBuildItem(self, obj, transform=None):
        self._ensure_object(obj)
        if obj._type == ObjectType.Other:
            raise ELib3MFException("Cannot build an object of type other")
        b = BuildItem(obj, transform or Transform())
        self._build.append(b)
        return b

    def RemoveBuildItem(self, item):
        self._build.remove(item)

    def GetBuildItems(self):
        return _Iterator(self._build)

    def GetMetaDataGroup(self):
        return self._metadata

    def GetOutbox(self):
        boxes = [item.GetOutbox() for item in self._build]
        if not boxes:
            return Box()
        return Box(
            [min(b.MinCoordinate[i] for b in boxes) for i in range(3)],
            [max(b.MaxCoordinate[i] for b in boxes) for i in range(3)],
        )

    def QueryReader(self, format_):
        if format_.lower() != "3mf":
            raise Unsupported3MFError("Only 3mf input supported")
        return Reader(self)

    def QueryWriter(self, format_):
        if format_.lower() != "3mf":
            raise Unsupported3MFError("Only 3mf output supported")
        return Writer(self)

    def MergeToModel(self):
        """Flatten build items and components to one mesh (geometry only)."""
        merged = Model()
        merged.SetUnit(self._unit)
        merged.SetLanguage(self._language)
        mesh = merged.AddMeshObject()
        mesh.SetName("Merged")

        def add(obj, transform, seen):
            if obj in seen:
                raise ELib3MFException("Circular component reference")
            if isinstance(obj, MeshObject):
                if obj._object_property or any(p for p in obj._tri_props):
                    raise Unsupported3MFError(
                        "MergeToModel with per-face colors/materials not implemented"
                    )
                offset = mesh.GetVertexCount()
                for p in obj._vertices:
                    mesh.AddVertex(_apply(p, transform))
                for t in obj._triangles:
                    mesh.AddTriangle([i + offset for i in t.Indices])
            else:
                for c in obj._components:
                    add(c._object, _compose(c._transform, transform), seen | {obj})

        for b in self._build:
            add(b._object, b._transform, set())
        merged.AddBuildItem(mesh, Transform())
        return merged

    def GetWarnings(self):
        return list(self._warnings)

    def Validate(self, *, check_self_intersections=False, max_pairs=200000):
        return {
            r.GetResourceID(): r.ValidateGeometry(
                check_self_intersections=check_self_intersections, max_pairs=max_pairs
            )
            for r in self._resources.values()
            if isinstance(r, MeshObject)
        }

    def GetOriginalPackagePartNames(self):
        if self._original_package is None:
            return []
        with ZipFile(BytesIO(self._original_package)) as zf:
            return zf.namelist()

    def GetOriginalPackagePart(self, path):
        if self._original_package is None:
            raise ELib3MFException("No original package loaded")
        with ZipFile(BytesIO(self._original_package)) as zf:
            return zf.read(_clean_zip_name(path))


class Wrapper:
    def __init__(self, *_args, **_kwargs):
        # Optional args ignored to ease migration from Wrapper(binary_path).
        pass

    def CreateModel(self):
        return Model()

    def GetLibraryVersion(self):
        return (0, 3, 0)  # our implementation, NOT native lib3mf version

    def GetPrereleaseInformation(self):
        return (False, "")

    def GetBuildInformation(self):
        return (True, "pure-python core + materials/production subset")

    def GetSpecificationVersion(self, url):
        return (
            (True, 1, 3, 0)
            if url
            in (CORE, "http://schemas.microsoft.com/3dmanufacturing/core/2015/02")
            else (False, 0, 0, 0)
        )

    def GetIdentityTransform(self):
        return Transform()

    def GetScaleTransform(self, x, y, z):
        return Transform(
            [
                [_finite(x), 0.0, 0.0],
                [0.0, _finite(y), 0.0],
                [0.0, 0.0, _finite(z)],
                [0.0, 0.0, 0.0],
            ]
        )

    def GetUniformScaleTransform(self, factor):
        return self.GetScaleTransform(factor, factor, factor)

    def GetTranslationTransform(self, x, y, z):
        t = Transform()
        t.Fields[3] = [_finite(x), _finite(y), _finite(z)]
        return t

    def RGBAToColor(self, r, g, b, a):
        return Color(r, g, b, a)

    def FloatRGBAToColor(self, r, g, b, a):
        return Color(*(round(255 * _finite(v)) for v in (r, g, b, a)))

    def ColorToRGBA(self, c):
        return (c.Red, c.Green, c.Blue, c.Alpha)

    def ColorToFloatRGBA(self, c):
        return tuple(v / 255 for v in self.ColorToRGBA(c))


def get_wrapper():
    return Wrapper()


def _verify_model(model):
    for obj in model._resources.values():
        if isinstance(obj, MeshObject):
            for t in obj._triangles:
                obj._check_tri(t)
            if obj._object_property:
                model._check_prop(*obj._object_property)
            for p in obj._tri_props:
                if p is not None:
                    model._check_props(p)
        if isinstance(obj, Texture2D):
            if obj._attachment is None:
                raise ELib3MFException("Texture has no attachment")
            obj._attachment.ReadFromBuffer()  # catches missing images before writing
        if isinstance(obj, Texture2DGroup):
            if obj._texture is None:
                raise ELib3MFException("Texture group has no texture")
            if obj._texture._package_path != obj._package_path:
                raise ELib3MFException(
                    "Texture groups and textures must share a model part"
                )
        if isinstance(obj, CompositeMaterials):
            if obj._base is None or obj._base._package_path != obj._package_path:
                raise ELib3MFException(
                    "Composites and base materials must share a model part"
                )
        if isinstance(obj, MultiPropertyGroup):
            for grp, _ in obj._layers:
                if grp._package_path != obj._package_path:
                    raise ELib3MFException(
                        "Multiproperty layers must share their model part"
                    )
        if isinstance(obj, ComponentsObject):
            for c in obj._components:
                model._ensure_object(c._object)
                if _references(c._object, obj, set()):
                    raise ELib3MFException("Circular component reference")
    for b in model._build:
        model._ensure_object(b._object)


def _resource_emit_order(model):
    """Topological ordering of resources within each model part."""
    output, visited, visiting = [], set(), set()

    def visit(r):
        if r in visited:
            return
        if r in visiting:
            raise ELib3MFException("Circular resource dependencies")
        visiting.add(r)
        deps = []
        if isinstance(r, ComponentsObject):
            deps = [c._object for c in r._components]
        elif isinstance(r, Texture2DGroup):
            deps = [r._texture]
        elif isinstance(r, CompositeMaterials):
            deps = [r._base]
        elif isinstance(r, MultiPropertyGroup):
            deps = [g for g, _ in r._layers]
        elif isinstance(r, MeshObject):
            # Property groups must be declared before the meshes that use them.
            rids = {p.ResourceID for p in r._tri_props if p is not None}
            if r._object_property is not None:
                rids.add(r._object_property[0])
            for rid in sorted(rids):
                dep = model._resources.get(rid)
                if dep is not None and dep._package_path == r._package_path:
                    visit(dep)
        for dep in deps:
            if dep is None:
                raise ELib3MFException("Unresolved resource dependency")
            if dep._package_path == r._package_path:
                visit(dep)
            elif (
                not isinstance(r, ComponentsObject)
                or r._package_path != model._root_part
            ):
                raise ELib3MFException(
                    "Only root model components can refer to other model parts"
                )
        visiting.remove(r)
        visited.add(r)
        output.append(r)

    for r in model._resources.values():
        visit(r)
    return output


def _model_to_xml(model):
    return _new_part_to_xml(model, model._root_part, False)


def _parse_model(data, *, part=MODEL_PATH, defer_external=False, ignore_build=False):
    root = _xml_from_bytes(data)
    namespaces = {
        prefix: uri
        for event, (prefix, uri) in ET.iterparse(BytesIO(data), events=("start-ns",))
    }
    if root.tag != _tag("model"):
        raise ELib3MFException("Not a 3MF core model XML document")
    model = Model()
    model._root_part = part
    model.SetUnit(root.get("unit", "millimeter"))
    model.SetLanguage(root.get(XML_LANG, "und"))
    _load_metadata(root, model._metadata, namespaces=namespaces)
    resources = root.find(_tag("resources"))
    build = root.find(_tag("build"))
    if resources is None or build is None:
        raise ELib3MFException("3MF model requires resources and build")
    deferred_components = []
    deferred_properties = []
    deferred_materials = []
    # Unknown extension resources may own IDs; do not reuse them later.
    reserved = [int(n.get("id")) for n in resources if n.get("id")]
    for node in resources:
        if node.tag == _tag("basematerials"):
            gr = model._add(BaseMaterialGroup, int(node.attrib["id"]))
            for el in node.findall(_tag("base")):
                gr.AddMaterial(el.attrib["name"], _hex_rgba(el.attrib["displaycolor"]))
        elif node.tag == _tag("colorgroup", MAT):
            gr = model._add(ColorGroup, int(node.attrib["id"]))
            for el in node.findall(_tag("color", MAT)):
                gr.AddColor(_hex_rgba(el.attrib["color"]))
        elif node.tag == _tag("texture2d", MAT):
            gr = model._add(Texture2D, int(node.attrib["id"]))
            path = _clean_zip_name(node.attrib["path"])
            if not node.attrib["path"].startswith("/"):
                raise ELib3MFException("Texture path must be package-absolute")
            gr.SetAttachment(model.AddAttachment("/" + path, TEXTURE_REL))
            gr.SetContentType(node.attrib["contenttype"])
            gr.SetTileStyleUV(
                node.get("tilestyleu", "wrap"), node.get("tilestylev", "wrap")
            )
            gr.SetFilter(node.get("filter", "auto"))
        elif node.tag == _tag("texture2dgroup", MAT):
            gr = model._add(Texture2DGroup, int(node.attrib["id"]))
            deferred_materials.append((gr, node))
            for el in node.findall(_tag("tex2coord", MAT)):
                gr.AddTex2Coord((float(el.attrib["u"]), float(el.attrib["v"])))
        elif node.tag == _tag("compositematerials", MAT):
            gr = model._add(CompositeMaterials, int(node.attrib["id"]))
            deferred_materials.append((gr, node))
            gr._matindices = [int(x) for x in node.attrib["matindices"].split()]
            for el in node.findall(_tag("composite", MAT)):
                values = [float(x) for x in el.attrib["values"].split()]
                gr._composites.append(
                    {
                        k: (values[i] if i < len(values) else 0.0)
                        for i, k in enumerate(gr._matindices)
                    }
                )
        elif node.tag == _tag("multiproperties", MAT):
            gr = model._add(MultiPropertyGroup, int(node.attrib["id"]))
            deferred_materials.append((gr, node))
            for el in node.findall(_tag("multi", MAT)):
                gr._multi.append([int(x) for x in el.attrib["pindices"].split()])
        elif node.tag == _tag("object"):
            mesh_el = node.find(_tag("mesh"))
            comp_el = node.find(_tag("components"))
            if (mesh_el is None) == (comp_el is None):
                raise Unsupported3MFError(
                    "Object must contain one supported mesh or components element"
                )
            obj = model._add(
                MeshObject if mesh_el is not None else ComponentsObject,
                int(node.attrib["id"]),
            )
            obj.SetName(node.get("name", ""))
            obj.SetPartNumber(node.get("partnumber", ""))
            obj.SetType(node.get("type", "model"))
            _load_metadata(node, obj._metadata, grouped=True, namespaces=namespaces)
            if mesh_el is not None:
                vertices = mesh_el.find(_tag("vertices"))
                triangles = mesh_el.find(_tag("triangles"))
                if vertices is None or triangles is None:
                    raise ELib3MFException("Mesh requires vertices and triangles")
                vs = [
                    [float(p.attrib[k]) for k in ("x", "y", "z")]
                    for p in vertices.findall(_tag("vertex"))
                ]
                ts = [
                    [int(t.attrib[k]) for k in ("v1", "v2", "v3")]
                    for t in triangles.findall(_tag("triangle"))
                ]
                obj.SetGeometry(vs, ts)
                deferred_properties.append((obj, node, triangles))
            else:
                deferred_components.append((obj, comp_el))
        else:
            model._warnings.append("Unsupported resource ignored: " + node.tag)
    model._next_id = max([model._next_id] + [i + 1 for i in reserved])
    for gr, node in deferred_materials:
        if isinstance(gr, Texture2DGroup):
            tex = model.GetResourceByID(int(node.attrib["texid"]))
            if not isinstance(tex, Texture2D):
                raise ELib3MFException("Invalid texture2dgroup texid")
            gr._texture = tex
        elif isinstance(gr, CompositeMaterials):
            base = model.GetResourceByID(int(node.attrib["matid"]))
            if not isinstance(base, BaseMaterialGroup):
                raise ELib3MFException("Invalid composite matid")
            if any(i < 0 or i >= base.GetCount() for i in gr._matindices):
                raise ELib3MFException("Invalid composite material index")
            gr._base = base
        elif isinstance(gr, MultiPropertyGroup):
            pids = [int(x) for x in node.attrib["pids"].split()]
            blends = node.get("blendmethods", "").split()
            if len(blends) > max(0, len(pids) - 1):
                raise ELib3MFException("Invalid number of blend methods")
            for i, rid in enumerate(pids):
                group = model.GetResourceByID(rid)
                if not isinstance(
                    group,
                    (BaseMaterialGroup, ColorGroup, Texture2DGroup, CompositeMaterials),
                ):
                    raise ELib3MFException("Invalid multiproperty layer reference")
                gr._layers.append(
                    (group, blends[i - 1] if i > 0 and i - 1 < len(blends) else "mix")
                )
            for indices in gr._multi:
                indices[:] = indices[: len(gr._layers)] + [0] * max(
                    0, len(gr._layers) - len(indices)
                )
                if any(
                    i < 0 or i >= g.GetCount() for i, (g, _) in zip(indices, gr._layers)
                ):
                    raise ELib3MFException("Invalid multiproperty index")
    for obj, node, triangles in deferred_properties:
        if "pid" in node.attrib:
            rid, pid = int(node.attrib["pid"]), int(node.get("pindex", 0))
            if isinstance(
                model._resources.get(rid),
                (
                    ColorGroup,
                    BaseMaterialGroup,
                    Texture2DGroup,
                    CompositeMaterials,
                    MultiPropertyGroup,
                ),
            ):
                obj.SetObjectLevelProperty(rid, pid)
            else:
                model._warnings.append(
                    "Opaque object material/property preserved: " + str(rid)
                )
        for i, tri in enumerate(triangles.findall(_tag("triangle"))):
            if "pid" in tri.attrib:
                rid = int(tri.attrib["pid"])
                if isinstance(
                    model._resources.get(rid),
                    (
                        ColorGroup,
                        BaseMaterialGroup,
                        Texture2DGroup,
                        CompositeMaterials,
                        MultiPropertyGroup,
                    ),
                ):
                    p1 = int(tri.get("p1", 0))
                    obj.SetTriangleProperties(
                        i,
                        TriangleProperties(
                            rid, [p1, int(tri.get("p2", p1)), int(tri.get("p3", p1))]
                        ),
                    )
                else:
                    model._warnings.append(
                        "Opaque triangle material/property preserved: " + str(rid)
                    )
    if defer_external:
        model._deferred_components = deferred_components
        model._deferred_build = (
            [] if ignore_build else list(build.findall(_tag("item")))
        )
        model._source_namespaces = namespaces
    else:
        for obj, comp_el in deferred_components:
            for node in comp_el.findall(_tag("component")):
                if node.get(_tag("path", PROD)):
                    raise Unsupported3MFError(
                        "Production path requires reading a 3MF package"
                    )
                target = model.GetResourceByID(int(node.attrib["objectid"]))
                if not isinstance(target, Object):
                    raise ELib3MFException("Component target not object")
                obj.AddComponent(target, _parse_xform(node.get("transform")))
        if not ignore_build:
            for node in build.findall(_tag("item")):
                if node.get(_tag("path", PROD)):
                    raise Unsupported3MFError(
                        "Production path requires reading a 3MF package"
                    )
                target = model.GetResourceByID(int(node.attrib["objectid"]))
                if not isinstance(target, Object):
                    raise ELib3MFException("Build target not an object")
                b = model.AddBuildItem(target, _parse_xform(node.get("transform")))
                b.SetPartNumber(node.get("partnumber", ""))
                _load_metadata(node, b._metadata, grouped=True, namespaces=namespaces)
    # Any unknown extension node/attribute can carry meaningful data; track loss.
    known_tags = {
        _tag(name)
        for name in (
            "model",
            "resources",
            "build",
            "metadata",
            "metadatagroup",
            "basematerials",
            "base",
            "object",
            "mesh",
            "vertices",
            "vertex",
            "triangles",
            "triangle",
            "components",
            "component",
            "item",
        )
    } | {
        _tag(k, MAT)
        for k in (
            "colorgroup",
            "color",
            "texture2d",
            "texture2dgroup",
            "tex2coord",
            "compositematerials",
            "composite",
            "multiproperties",
            "multi",
        )
    }
    supported_attributes = {
        _tag("model"): {
            "unit",
            XML_LANG,
            "requiredextensions",
            "recommendedextensions",
        },
        _tag("resources"): set(),
        _tag("build"): {_tag("UUID", PROD)},
        _tag("metadata"): {"name", "type", "preserve"},
        _tag("metadatagroup"): set(),
        _tag("basematerials"): {"id"},
        _tag("base"): {"name", "displaycolor"},
        _tag("object"): {
            "id",
            "type",
            "name",
            "partnumber",
            "pid",
            "pindex",
            _tag("UUID", PROD),
        },
        _tag("mesh"): set(),
        _tag("vertices"): set(),
        _tag("vertex"): {"x", "y", "z"},
        _tag("triangles"): set(),
        _tag("triangle"): {"v1", "v2", "v3", "pid", "p1", "p2", "p3"},
        _tag("components"): set(),
        _tag("component"): {
            "objectid",
            "transform",
            _tag("path", PROD),
            _tag("UUID", PROD),
        },
        _tag("item"): {
            "objectid",
            "transform",
            "partnumber",
            _tag("path", PROD),
            _tag("UUID", PROD),
        },
        _tag("colorgroup", MAT): {"id"},
        _tag("color", MAT): {"color"},
        _tag("texture2d", MAT): {
            "id",
            "path",
            "contenttype",
            "tilestyleu",
            "tilestylev",
            "filter",
        },
        _tag("texture2dgroup", MAT): {"id", "texid", "displaypropertiesid"},
        _tag("tex2coord", MAT): {"u", "v"},
        _tag("compositematerials", MAT): {
            "id",
            "matid",
            "matindices",
            "displaypropertiesid",
        },
        _tag("composite", MAT): {"values"},
        _tag("multiproperties", MAT): {"id", "pids", "blendmethods"},
        _tag("multi", MAT): {"pindices"},
    }
    unknown = set()
    for node in root.iter():
        if not isinstance(node.tag, str):
            continue  # preserved comment/PI
        if node.tag not in known_tags:
            unknown.add(str(node.tag))
        for key in node.attrib:
            if key not in supported_attributes.get(node.tag, set()):
                unknown.add("attribute " + str(key) + " on " + str(node.tag))
    for item in sorted(unknown):
        model._warnings.append("Opaque XML preserved but not interpreted: " + item)
    return model


def _package_xml(root, namespace):
    # OPC readers (including lib3mf) reject prefixed package parts such as <ns0:Types>.
    prefix = "{" + namespace + "}"
    root = copy.deepcopy(root)
    for el in root.iter():
        if isinstance(el.tag, str) and el.tag.startswith(prefix):
            el.tag = el.tag[len(prefix) :]
    root.set("xmlns", namespace)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _content_types():
    root = ET.Element("{" + CONTENT + "}Types")
    ET.SubElement(
        root,
        "{" + CONTENT + "}Default",
        {
            "Extension": "rels",
            "ContentType": "application/vnd.openxmlformats-package.relationships+xml",
        },
    )
    ET.SubElement(
        root,
        "{" + CONTENT + "}Override",
        {"PartName": "/" + MODEL_PATH, "ContentType": MODEL_CONTENT},
    )
    return _package_xml(root, CONTENT)


def _root_rels_for(part):
    root = ET.Element(_tag("Relationships", PKGREL))
    ET.SubElement(
        root,
        _tag("Relationship", PKGREL),
        {"Target": "/" + part, "Id": "rel0", "Type": START_REL},
    )
    return _package_xml(root, PKGREL)


def _root_rels():
    root = ET.Element("{" + PKGREL + "}Relationships")
    ET.SubElement(
        root,
        "{" + PKGREL + "}Relationship",
        {"Target": "/" + MODEL_PATH, "Id": "rel0", "Type": START_REL},
    )
    return _package_xml(root, PKGREL)


def _clean_zip_name(name):
    # Resolve only package-absolute paths; forbid traversal and URL schemes.
    if "\\" in name or "://" in name or ":" in name:
        raise ELib3MFException("Unsafe 3MF package part reference")
    path = PurePosixPath(name.lstrip("/"))
    if ".." in path.parts or not str(path) or str(path) == ".":
        raise ELib3MFException("Unsafe 3MF package part reference")
    return str(path)


def _find_start_part(zf):
    try:
        rel = _xml_from_bytes(zf.read("_rels/.rels"))
    except KeyError as e:
        raise ELib3MFException("Missing package relationships (_rels/.rels)") from e
    for node in rel:
        if node.tag == "{" + PKGREL + "}Relationship" and node.get("Type") == START_REL:
            if node.get("TargetMode", "Internal") != "Internal":
                raise ELib3MFException("External 3MF start parts are forbidden")
            return _clean_zip_name(node.attrib["Target"])
    raise ELib3MFException("Package has no 3MF StartPart relationship")


# --- Multi-part Production Extension and conservative opaque-content preservation ---


def _relationships_part(part):
    """OPC relationship part corresponding to a model part."""
    directory, base = posixpath.split(part)
    return posixpath.join(directory, "_rels", base + ".rels")


def _relationship_target(source_part, target):
    if not target or "#" in target or "?" in target:
        raise ELib3MFException("Invalid model relationship target")
    if target.startswith("/"):
        return _clean_zip_name(target)
    return _clean_zip_name(
        posixpath.normpath(posixpath.join(posixpath.dirname(source_part), target))
    )


def _model_relationships(zf, source_part):
    rel_part = _relationships_part(source_part)
    if rel_part not in zf.namelist():
        return set()
    rel_xml = _xml_from_bytes(zf.read(rel_part))
    if rel_xml.tag != _tag("Relationships", PKGREL):
        raise ELib3MFException("Invalid model relationships")
    paths = set()
    for rel in rel_xml.findall(_tag("Relationship", PKGREL)):
        if rel.get("Type") != START_REL:
            continue
        if rel.get("TargetMode", "Internal") != "Internal":
            raise ELib3MFException("External model relationships forbidden")
        path = _relationship_target(source_part, rel.get("Target"))
        if path == source_part:
            raise ELib3MFException("A model part cannot reference itself")
        paths.add(path)
    return paths


def _production_path(node, root_part):
    path = node.get(_tag("path", PROD))
    if path is None:
        return root_part
    # The Production Extension specifies package-absolute paths.
    if not path.startswith("/"):
        raise ELib3MFException("Production p:path must be package-absolute")
    return _clean_zip_name(path)


def _load_production(zf, data):
    root_path = _find_start_part(zf)
    if root_path not in zf.namelist():
        raise ELib3MFException("Referenced root model part missing")
    root = _parse_model(zf.read(root_path), part=root_path, defer_external=True)
    rel_paths = _model_relationships(zf, root_path)
    references = set()
    for _, components in root._deferred_components:
        for node in components.findall(_tag("component")):
            references.add(_production_path(node, root_path))
    for node in root._deferred_build:
        references.add(_production_path(node, root_path))
    references.discard(root_path)
    unlinked = references - rel_paths
    if unlinked:
        raise ELib3MFException(
            "Production model part is not linked from root model relationships: "
            + ", ".join(sorted(unlinked))
        )
    parts = {root_path: {id_: obj for id_, obj in root._resources.items()}}
    for path in sorted(references):
        if path not in zf.namelist():
            raise ELib3MFException("Referenced Production model part missing: " + path)
        child = _parse_model(
            zf.read(path), part=path, defer_external=True, ignore_build=True
        )
        if child.GetUnit() != root.GetUnit():
            raise Unsupported3MFError(
                "Production child/root model units differ; unit conversion not implemented"
            )
        # Non-root model parts cannot make cross-file component references.
        child_objects = dict(child._resources)
        for obj, components in child._deferred_components:
            for node in components.findall(_tag("component")):
                if node.get(_tag("path", PROD)) is not None:
                    raise ELib3MFException(
                        "Production child components must reference local objects"
                    )
                target = child_objects.get(int(node.attrib["objectid"]))
                if not isinstance(target, Object):
                    raise ELib3MFException("Invalid child component target")
                comp = obj.AddComponent(target, _parse_xform(node.get("transform")))
                comp._source_index = len(obj._components) - 1
        # Child IDs collide routinely with root IDs. Remap runtime IDs only;
        # preserve each source part's local IDs for subsequent writing.
        id_map = {}
        for local_id, resource in child_objects.items():
            new_id = root._next_id
            root._next_id += 1
            id_map[local_id] = new_id
            resource._id = new_id
            resource._package_path = path
            resource._model = root
            root._resources[new_id] = resource
        for resource in child_objects.values():
            if isinstance(resource, Texture2D) and resource._attachment is not None:
                resource._attachment._model = root
            if isinstance(resource, MeshObject):
                if resource._object_property:
                    r, v = resource._object_property
                    resource._object_property = (id_map[r], v)
                for p in resource._tri_props:
                    if p is not None:
                        p.ResourceID = id_map[p.ResourceID]
        parts[path] = child_objects
        root._warnings.extend(child._warnings)

    # Resolve root object references AFTER importing child resources.
    def lookup(node):
        path = _production_path(node, root_path)
        obj = parts.get(path, {}).get(int(node.attrib["objectid"]))
        if not isinstance(obj, Object):
            raise ELib3MFException(
                f'Unresolved 3MF object reference {path}:{node.get("objectid")}'
            )
        return obj

    for obj, components in root._deferred_components:
        for node in components.findall(_tag("component")):
            comp = obj.AddComponent(lookup(node), _parse_xform(node.get("transform")))
            comp._source_index = len(obj._components) - 1
    for i, node in enumerate(root._deferred_build):
        b = root.AddBuildItem(lookup(node), _parse_xform(node.get("transform")))
        b._source_index = i
        b.SetPartNumber(node.get("partnumber", ""))
        _load_metadata(
            node, b._metadata, grouped=True, namespaces=root._source_namespaces
        )
    root._deferred_components = []
    root._deferred_build = []
    root._original_package = data
    root._production_enabled = bool(references)
    for resource in root._resources.values():
        if isinstance(resource, Texture2D) and resource._attachment is not None:
            resource._attachment._model = root
            path = _clean_zip_name(resource._attachment.GetPath())
            if path not in zf.namelist():
                raise ELib3MFException("Texture image is missing from package: " + path)
            if resource._package_path not in (root_path, *references):
                raise ELib3MFException("Unknown texture source part")
            relpart = _relationships_part(resource._package_path)
            if relpart not in zf.namelist():
                root._warnings.append("Texture relationship part missing: " + relpart)
            else:
                relxml = _xml_from_bytes(zf.read(relpart))
                if not any(
                    node.get("Type") == TEXTURE_REL
                    and node.get("TargetMode", "Internal") == "Internal"
                    and _relationship_target(resource._package_path, node.get("Target"))
                    == path
                    for node in relxml.findall(_tag("Relationship", PKGREL))
                    if node.get("Type") == TEXTURE_REL
                ):
                    root._warnings.append("Texture relationship not found: " + path)
    root._original_attachment_states = {}
    root._original_parts = {
        part: zf.read(part) for part in [root_path, *sorted(references)]
    }
    # Copying bytes of all ZIP parts is unnecessary: untouched parts are copied
    # from the original package in Writer. This avoids large memory overhead.
    root._original_part_states = {
        part: _snapshot_part(root, part) for part in root._original_parts
    }
    extra = set(zf.namelist()) - {
        "[Content_Types].xml",
        "_rels/.rels",
        *root._original_parts,
    }
    if extra:
        root._warnings.append(
            "Opaque ZIP entries preserved: " + ", ".join(sorted(extra)[:12])
        )
    return root


def _metadata_state(group):
    return tuple(
        (m.namespace, m.name, m.value, m.datatype, m.preserve) for m in group._items
    )


def _snapshot_resource(r):
    base = (type(r).__name__, r._id, r._local_id, r._package_path)
    if isinstance(r, Object):
        base += (r._name, r._partnumber, r._type, _metadata_state(r._metadata))
    if isinstance(r, MeshObject):
        base += (
            tuple(tuple(v.Coordinates) for v in r._vertices),
            tuple(tuple(t.Indices) for t in r._triangles),
            r._object_property,
            tuple(
                None if p is None else (p.ResourceID, tuple(p.PropertyIDs))
                for p in r._tri_props
            ),
        )
    elif isinstance(r, ComponentsObject):
        base += (
            tuple(
                (c._object._id, tuple(tuple(f) for f in c._transform.Fields))
                for c in r._components
            ),
        )
    elif isinstance(r, BaseMaterialGroup):
        base += (
            tuple(
                (name, col.Red, col.Green, col.Blue, col.Alpha)
                for name, col in r._materials
            ),
        )
    elif isinstance(r, Texture2D):
        base += (
            r._attachment.GetPath() if r._attachment else None,
            r._content_type,
            r._tile_u,
            r._tile_v,
            r._filter,
        )
    elif isinstance(r, Texture2DGroup):
        base += (
            r._texture._id if r._texture else None,
            tuple(tuple(c.Coordinates) for c in r._coords),
        )
    elif isinstance(r, CompositeMaterials):
        base += (
            r._base._id if r._base else None,
            tuple(r._matindices),
            tuple(tuple(sorted(v.items())) for v in r._composites),
        )
    elif isinstance(r, MultiPropertyGroup):
        base += (
            tuple((g._id, b) for g, b in r._layers),
            tuple(tuple(v) for v in r._multi),
        )
    elif isinstance(r, ColorGroup):
        base += (tuple((c.Red, c.Green, c.Blue, c.Alpha) for c in r._colors),)
    return base


def _snapshot_part(model, part):
    resources = tuple(
        _snapshot_resource(r)
        for r in model._resources.values()
        if r._package_path == part
    )
    if part != model._root_part:
        return resources
    builds = tuple(
        (
            b._object._id,
            tuple(tuple(f) for f in b._transform.Fields),
            b._partnumber,
            _metadata_state(b._metadata),
        )
        for b in model._build
    )
    return (
        resources,
        model._unit,
        model._language,
        _metadata_state(model._metadata),
        builds,
    )


def _ref_attrib(obj, source_part):
    at = {"objectid": str(obj._local_id)}
    if obj._package_path != source_part:
        at[_tag("path", PROD)] = "/" + obj._package_path
    return at


def _prop_local_id(model, resource_id, source_part):
    r = model.GetResourceByID(resource_id)
    if r._package_path != source_part:
        raise Unsupported3MFError(
            "3MF material/property must be in the same model part as its mesh"
        )
    return r._local_id


def _setattr_optional(node, key, value):
    if value is None or value == "":
        node.attrib.pop(key, None)
    else:
        node.set(key, str(value))


def _patch_properties(obj, node, part):
    if obj._object_property is not None:
        rid, index = obj._object_property
        node.set("pid", str(_prop_local_id(obj._model, rid, part)))
        node.set("pindex", str(index))
    else:
        # Leave unknown/opaque pid values intact rather than silently stripping
        # unsupported texture and multiproperty assignments.
        if "pid" in node.attrib and int(node.get("pid", 0)) in (
            r._local_id
            for r in obj._model._resources.values()
            if r._package_path == part
            and isinstance(
                r,
                (
                    BaseMaterialGroup,
                    ColorGroup,
                    Texture2DGroup,
                    CompositeMaterials,
                    MultiPropertyGroup,
                ),
            )
        ):
            node.attrib.pop("pid", None)
            node.attrib.pop("pindex", None)


def _replace_known_children(parent, tag, values, update, *, allow_lossy=False):
    old = parent.findall(tag)
    if len(old) != len(values):
        allowed = {
            "vertex": {"x", "y", "z"},
            "triangle": {"v1", "v2", "v3", "pid", "p1", "p2", "p3"},
            "tex2coord": {"u", "v"},
            "composite": {"values"},
            "multi": {"pindices"},
        }.get(_local(tag), set())
        for el in old:
            # Any extension hanging from an indexed element becomes ambiguous
            # when its index is changed; require explicit override.
            if (set(el.attrib) - allowed) or list(el):
                if not allow_lossy:
                    raise Unsupported3MFError(
                        "Changing indexed mesh geometry risks orphaning "
                        "unknown per-vertex or per-triangle data"
                    )
        for el in old:
            parent.remove(el)
        for value in values:
            update(ET.SubElement(parent, tag), value)
    else:
        for el, value in zip(old, values):
            update(el, value)


def _update_mesh(obj, node, part, allow_lossy):
    mesh = node.find(_tag("mesh"))
    if mesh is None:
        mesh = ET.SubElement(node, _tag("mesh"))
    vertices = mesh.find(_tag("vertices"))
    if vertices is None:
        vertices = ET.SubElement(mesh, _tag("vertices"))
    triangles = mesh.find(_tag("triangles"))
    if triangles is None:
        triangles = ET.SubElement(mesh, _tag("triangles"))

    def vertex_fn(el, v):
        for k, x in zip(("x", "y", "z"), v.Coordinates):
            el.set(k, _num(x))

    def triangle_fn(i, el, t):
        for k, v in zip(("v1", "v2", "v3"), t.Indices):
            el.set(k, str(v))
        prop = obj._tri_props[i]
        if prop is not None:
            el.set("pid", str(_prop_local_id(obj._model, prop.ResourceID, part)))
            for k, v in zip(("p1", "p2", "p3"), prop.PropertyIDs):
                el.set(k, str(v))
        else:
            # Preserve unknown/opaque material attributes. Remove recognized
            # properties only when they have been explicitly cleared.
            pid = el.get("pid")
            if pid is not None and any(
                r._local_id == int(pid)
                and r._package_path == part
                and isinstance(
                    r,
                    (
                        ColorGroup,
                        BaseMaterialGroup,
                        Texture2DGroup,
                        CompositeMaterials,
                        MultiPropertyGroup,
                    ),
                )
                for r in obj._model._resources.values()
            ):
                for k in ("pid", "p1", "p2", "p3"):
                    el.attrib.pop(k, None)

    _replace_known_children(
        vertices, _tag("vertex"), obj._vertices, vertex_fn, allow_lossy=allow_lossy
    )
    old = triangles.findall(_tag("triangle"))
    if len(old) != len(obj._triangles):
        # Reindexing opaque per-face property references cannot be done safely.
        if not allow_lossy and any(
            t.get("pid")
            and not any(
                r._local_id == int(t.get("pid"))
                and r._package_path == part
                and isinstance(
                    r,
                    (
                        BaseMaterialGroup,
                        ColorGroup,
                        Texture2DGroup,
                        CompositeMaterials,
                        MultiPropertyGroup,
                    ),
                )
                for r in obj._model._resources.values()
            )
            for t in old
        ):
            raise Unsupported3MFError(
                "Reordering face count with opaque triangle properties "
                "requires AllowLossyWrite(True)"
            )
    _replace_known_children(
        triangles,
        _tag("triangle"),
        list(enumerate(obj._triangles)),
        lambda el, it: triangle_fn(it[0], el, it[1]),
        allow_lossy=allow_lossy,
    )


def _stable_uuid(obj):
    identifier = getattr(obj, "_production_uuid", None)
    if identifier is None:
        identifier = str(uuid.uuid4())
        obj._production_uuid = identifier
    return identifier


def _create_resource(parent, r, part, production=False):
    attrs = {"id": str(r._local_id)}
    if isinstance(r, BaseMaterialGroup):
        el = ET.SubElement(parent, _tag("basematerials"), attrs)
        for n, c in r._materials:
            ET.SubElement(el, _tag("base"), {"name": n, "displaycolor": _rgba_hex(c)})
    elif isinstance(r, ColorGroup):
        el = ET.SubElement(parent, _tag("colorgroup", MAT), attrs)
        for c in r._colors:
            ET.SubElement(el, _tag("color", MAT), {"color": _rgba_hex(c)})
    elif isinstance(r, Texture2D):
        if r._attachment is None:
            raise ELib3MFException("Texture has no attachment")
        attrs.update(
            {
                "path": r._attachment.GetPath(),
                "contenttype": r._content_type,
                "tilestyleu": r._tile_u,
                "tilestylev": r._tile_v,
                "filter": r._filter,
            }
        )
        el = ET.SubElement(parent, _tag("texture2d", MAT), attrs)
    elif isinstance(r, Texture2DGroup):
        attrs["texid"] = str(_prop_local_id(r._model, r._texture._id, part))
        el = ET.SubElement(parent, _tag("texture2dgroup", MAT), attrs)
        for uv in r._coords:
            ET.SubElement(
                el,
                _tag("tex2coord", MAT),
                {"u": _num(uv.Coordinates[0]), "v": _num(uv.Coordinates[1])},
            )
    elif isinstance(r, CompositeMaterials):
        attrs["matid"] = str(_prop_local_id(r._model, r._base._id, part))
        attrs["matindices"] = " ".join(map(str, r._matindices))
        el = ET.SubElement(parent, _tag("compositematerials", MAT), attrs)
        for values in r._composites:
            ET.SubElement(
                el,
                _tag("composite", MAT),
                {"values": " ".join(_num(values.get(i, 0)) for i in r._matindices)},
            )
    elif isinstance(r, MultiPropertyGroup):
        attrs["pids"] = " ".join(
            str(_prop_local_id(r._model, g._id, part)) for g, _ in r._layers
        )
        if len(r._layers) > 1:
            attrs["blendmethods"] = " ".join(b for _, b in r._layers[1:])
        el = ET.SubElement(parent, _tag("multiproperties", MAT), attrs)
        for indices in r._multi:
            ET.SubElement(
                el, _tag("multi", MAT), {"pindices": " ".join(map(str, indices))}
            )
    elif isinstance(r, Object):
        attrs["type"] = _TYPE_NAMES[r._type]
        if production:
            attrs[_tag("UUID", PROD)] = _stable_uuid(r)
        if r._name:
            attrs["name"] = r._name
        if r._partnumber:
            attrs["partnumber"] = r._partnumber
        el = ET.SubElement(parent, _tag("object"), attrs)
        _write_metadata(el, r._metadata, grouped=True)
        if isinstance(r, MeshObject):
            _patch_properties(r, el, part)
            _update_mesh(r, el, part, allow_lossy=False)
        else:
            container = ET.SubElement(el, _tag("components"))
            for c in r._components:
                at = _ref_attrib(c._object, part)
                if c.HasTransform():
                    at["transform"] = _xform_str(c._transform)
                if production:
                    at[_tag("UUID", PROD)] = _stable_uuid(c)
                ET.SubElement(container, _tag("component"), at)
    else:
        raise Unsupported3MFError("Resource type cannot be serialized")
    return el


def _new_part_to_xml(model, part, production=False):
    _verify_model(model)
    attrs = {"unit": _UNIT_NAMES[int(model._unit)], XML_LANG: model._language}
    material = any(
        isinstance(
            r,
            (
                ColorGroup,
                Texture2D,
                Texture2DGroup,
                CompositeMaterials,
                MultiPropertyGroup,
            ),
        )
        and r._package_path == part
        for r in model._resources.values()
    )
    if production:
        attrs["requiredextensions"] = "m p" if material else "p"
    elif material:
        attrs["requiredextensions"] = "m"
    root = ET.Element(_tag("model"), attrs)
    if part == model._root_part:
        _write_metadata(root, model._metadata)
    resources = ET.SubElement(root, _tag("resources"))
    for r in _resource_emit_order(model):
        if r._package_path == part:
            _create_resource(resources, r, part, production)
    build = ET.SubElement(root, _tag("build"))
    if production and part == model._root_part:
        if model._build_uuid is None:
            model._build_uuid = str(uuid.uuid4())
        build.set(_tag("UUID", PROD), model._build_uuid)
    if part == model._root_part:
        for b in model._build:
            at = _ref_attrib(b._object, part)
            if b.HasObjectTransform():
                at["transform"] = _xform_str(b._transform)
            if b._partnumber:
                at["partnumber"] = b._partnumber
            if production:
                at[_tag("UUID", PROD)] = _stable_uuid(b)
            el = ET.SubElement(build, _tag("item"), at)
            _write_metadata(el, b._metadata, grouped=True)
    # Make sure namespace prefixes used in requiredextensions are bound.
    if material and not any(
        isinstance(el.tag, str) and el.tag.startswith("{" + MAT + "}")
        for el in root.iter()
    ):
        root.set("xmlns:m", MAT)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _sync_metadata(parent, group, *, grouped=False):
    holder = parent.find(_tag("metadatagroup")) if grouped else parent
    if holder is None:
        if not group._items:
            return
        holder = ET.Element(_tag("metadatagroup"))
        parent.insert(0, holder)
    old = holder.findall(_tag("metadata"))
    for idx, m in enumerate(group._items):
        if idx < len(old):
            node = old[idx]
        else:
            node = ET.SubElement(holder, _tag("metadata"))
        node.set("name", ET.QName(m.namespace, m.name) if m.namespace else m.name)
        _setattr_optional(node, "type", m.datatype)
        _setattr_optional(node, "preserve", "true" if m.preserve else None)
        node.text = m.value
    for node in old[len(group._items) :]:
        holder.remove(node)
    if grouped and not group._items and not list(holder):
        parent.remove(holder)


def _patch_resource(r, node, part, allow_lossy, production=False):
    if isinstance(r, Object):
        node.set("type", _TYPE_NAMES[r._type])
        _setattr_optional(node, "name", r._name)
        _setattr_optional(node, "partnumber", r._partnumber)
        _sync_metadata(node, r._metadata, grouped=True)
    if isinstance(r, MeshObject):
        _patch_properties(r, node, part)
        _update_mesh(r, node, part, allow_lossy)
    elif isinstance(r, ComponentsObject):
        holder = node.find(_tag("components"))
        if holder is None:
            holder = ET.SubElement(node, _tag("components"))
        old = holder.findall(_tag("component"))
        for i, component in enumerate(r._components):
            index = getattr(component, "_source_index", None)
            new = index is None or index >= len(old)
            el = ET.SubElement(holder, _tag("component")) if new else old[index]
            if new and production:
                el.set(_tag("UUID", PROD), _stable_uuid(component))
            at = _ref_attrib(component._object, part)
            el.set("objectid", at["objectid"])
            _setattr_optional(el, _tag("path", PROD), at.get(_tag("path", PROD)))
            _setattr_optional(
                el,
                "transform",
                _xform_str(component._transform) if component.HasTransform() else None,
            )
        used = {getattr(c, "_source_index", -1) for c in r._components}
        for i, el in enumerate(old):
            if i not in used:
                holder.remove(el)
    elif isinstance(r, BaseMaterialGroup):
        old = node.findall(_tag("base"))
        if len(old) != len(r._materials):
            if not allow_lossy and any(
                (set(el.attrib) - {"name", "displaycolor"} or list(el)) for el in old
            ):
                raise Unsupported3MFError("Resizing materials with opaque data")
            for el in old:
                node.remove(el)
            old = [ET.SubElement(node, _tag("base")) for _ in r._materials]
        for el, (name, col) in zip(old, r._materials):
            el.set("name", name)
            el.set("displaycolor", _rgba_hex(col))
    elif isinstance(r, Texture2D):
        if not r._attachment:
            raise ELib3MFException("Texture attachment missing")
        node.set("path", r._attachment.GetPath())
        node.set("contenttype", r._content_type)
        node.set("tilestyleu", r._tile_u)
        node.set("tilestylev", r._tile_v)
        node.set("filter", r._filter)
    elif isinstance(r, Texture2DGroup):
        node.set("texid", str(_prop_local_id(r._model, r._texture._id, part)))
        _replace_known_children(
            node,
            _tag("tex2coord", MAT),
            r._coords,
            lambda el, uv: (
                el.set("u", _num(uv.Coordinates[0])),
                el.set("v", _num(uv.Coordinates[1])),
            ),
            allow_lossy=allow_lossy,
        )
    elif isinstance(r, CompositeMaterials):
        node.set("matid", str(_prop_local_id(r._model, r._base._id, part)))
        node.set("matindices", " ".join(map(str, r._matindices)))
        _replace_known_children(
            node,
            _tag("composite", MAT),
            r._composites,
            lambda el, v: el.set(
                "values", " ".join(_num(v.get(i, 0)) for i in r._matindices)
            ),
            allow_lossy=allow_lossy,
        )
    elif isinstance(r, MultiPropertyGroup):
        node.set(
            "pids",
            " ".join(str(_prop_local_id(r._model, g._id, part)) for g, _ in r._layers),
        )
        _setattr_optional(node, "blendmethods", " ".join(b for _, b in r._layers[1:]))
        _replace_known_children(
            node,
            _tag("multi", MAT),
            r._multi,
            lambda el, v: el.set("pindices", " ".join(map(str, v))),
            allow_lossy=allow_lossy,
        )
    elif isinstance(r, ColorGroup):
        old = node.findall(_tag("color", MAT))
        if len(old) != len(r._colors):
            if not allow_lossy and any(
                (set(el.attrib) - {"color"} or list(el)) for el in old
            ):
                raise Unsupported3MFError("Resizing colorgroup with opaque data")
            for el in old:
                node.remove(el)
            old = [ET.SubElement(node, _tag("color", MAT)) for _ in r._colors]
        for el, col in zip(old, r._colors):
            el.set("color", _rgba_hex(col))


def _patch_part_xml(model, part, original, allow_lossy):
    xml = _xml_from_bytes(original)
    # Keep the original namespace prefixes used by requiredextensions and
    # lexical QName values, which ElementTree otherwise can silently unbind.
    namespace_map = dict(
        (prefix, uri)
        for _, (prefix, uri) in ET.iterparse(BytesIO(original), events=("start-ns",))
    )
    for prefix, uri in namespace_map.items():
        if prefix and prefix not in ("xml", "xmlns") and not prefix.startswith("ns"):
            ET.register_namespace(prefix, uri)
    used_uris = {
        tag.split("}", 1)[0][1:]
        for node in xml.iter()
        for tag in (node.tag, *node.attrib)
        if isinstance(tag, str) and tag.startswith("{")
    }
    for prefix, uri in namespace_map.items():
        if prefix and uri not in used_uris and prefix not in ("xml", "xmlns"):
            xml.set("xmlns:" + prefix, uri)
    production = PROD in namespace_map.values()
    if part == model._root_part:
        xml.set("unit", _UNIT_NAMES[int(model._unit)])
        xml.set(XML_LANG, model._language)
        _sync_metadata(xml, model._metadata)
    resources = xml.find(_tag("resources"))
    if resources is None:
        raise ELib3MFException("Missing resources in original model part")
    indexed = {(el.tag, int(el.get("id"))): el for el in resources if el.get("id")}

    def key(r):
        return (
            (
                _tag("object")
                if isinstance(r, Object)
                else (
                    _tag("basematerials")
                    if isinstance(r, BaseMaterialGroup)
                    else (
                        _tag("colorgroup", MAT)
                        if isinstance(r, ColorGroup)
                        else (
                            _tag("texture2d", MAT)
                            if isinstance(r, Texture2D)
                            else (
                                _tag("texture2dgroup", MAT)
                                if isinstance(r, Texture2DGroup)
                                else (
                                    _tag("compositematerials", MAT)
                                    if isinstance(r, CompositeMaterials)
                                    else _tag("multiproperties", MAT)
                                )
                            )
                        )
                    )
                )
            ),
            r._local_id,
        )

    ordered = [r for r in _resource_emit_order(model) if r._package_path == part]
    for position, r in enumerate(ordered):
        el = indexed.get(key(r))
        if el is None:
            el = _create_resource(resources, r, part, production)
            # 3MF needs component targets earlier than the component object.
            # Insert before the next resource already on disk, if there is one.
            for later in ordered[position + 1 :]:
                target = indexed.get(key(later))
                if target is not None:
                    resources.remove(el)
                    resources.insert(list(resources).index(target), el)
                    break
            indexed[key(r)] = el
        else:
            _patch_resource(r, el, part, allow_lossy, production)
    if part == model._root_part:
        build = xml.find(_tag("build"))
        if build is None:
            raise ELib3MFException("Missing build in original root")
        old = build.findall(_tag("item"))
        for b in model._build:
            idx = getattr(b, "_source_index", None)
            new = idx is None or idx >= len(old)
            el = ET.SubElement(build, _tag("item")) if new else old[idx]
            if new and production:
                el.set(_tag("UUID", PROD), _stable_uuid(b))
            attrs = _ref_attrib(b._object, part)
            el.set("objectid", attrs["objectid"])
            _setattr_optional(el, _tag("path", PROD), attrs.get(_tag("path", PROD)))
            _setattr_optional(el, "partnumber", b._partnumber)
            _setattr_optional(
                el,
                "transform",
                _xform_str(b._transform) if b.HasObjectTransform() else None,
            )
            _sync_metadata(el, b._metadata, grouped=True)
        used = {getattr(b, "_source_index", -1) for b in model._build}
        for i, el in enumerate(old):
            if i not in used:
                build.remove(el)
    return ET.tostring(xml, encoding="utf-8", xml_declaration=True)


def _required_relationships(model, part, model_parts):
    required = []
    if part == model._root_part:
        for path in sorted(model_parts - {part}):
            required.append((START_REL, path))
    for r in model._resources.values():
        if (
            isinstance(r, Texture2D)
            and r._package_path == part
            and r._attachment is not None
        ):
            required.append((TEXTURE_REL, _clean_zip_name(r._attachment.GetPath())))
    return required


def _merge_relationships(previous, requirements, source_part):
    root = (
        _xml_from_bytes(previous)
        if previous
        else ET.Element(_tag("Relationships", PKGREL))
    )
    if root.tag != _tag("Relationships", PKGREL):
        raise ELib3MFException("Invalid model relationships XML")
    existing = set()
    usedids = set()
    for node in root.findall(_tag("Relationship", PKGREL)):
        usedids.add(node.get("Id"))
        if node.get("TargetMode", "Internal") == "Internal":
            existing.add(
                (
                    node.get("Type"),
                    _relationship_target(source_part, node.get("Target")),
                )
            )
    added = False
    for typ, path in requirements:
        if (typ, path) in existing:
            continue
        index = 1
        while "rId" + str(index) in usedids:
            index += 1
        rid = "rId" + str(index)
        usedids.add(rid)
        ET.SubElement(
            root,
            _tag("Relationship", PKGREL),
            {"Id": rid, "Type": typ, "Target": "/" + path},
        )
        added = True
    return _package_xml(root, PKGREL) if added or not previous else previous


def _update_content_types(original, parts, textures):
    root = _xml_from_bytes(original) if original else ET.Element(_tag("Types", CONTENT))
    if root.tag != _tag("Types", CONTENT):
        raise ELib3MFException("Invalid content types part")
    dirty = False
    defaults = {
        (n.get("Extension"), n.get("ContentType"))
        for n in root.findall(_tag("Default", CONTENT))
    }
    reltype = ("rels", "application/vnd.openxmlformats-package.relationships+xml")
    if reltype not in defaults:
        ET.SubElement(
            root,
            _tag("Default", CONTENT),
            {"Extension": reltype[0], "ContentType": reltype[1]},
        )
        dirty = True
    overrides = {n.get("PartName"): n for n in root.findall(_tag("Override", CONTENT))}
    for path, contenttype in [(k, MODEL_CONTENT) for k in sorted(parts)] + sorted(
        textures.items()
    ):
        key = "/" + path
        if key in overrides:
            if overrides[key].get("ContentType") != contenttype:
                overrides[key].set("ContentType", contenttype)
                dirty = True
        else:
            ET.SubElement(
                root,
                _tag("Override", CONTENT),
                {"PartName": key, "ContentType": contenttype},
            )
            dirty = True
    return _package_xml(root, CONTENT) if dirty or not original else original


def _material_paths(model):
    textures = {}
    for r in model._resources.values():
        if isinstance(r, Texture2D):
            if not r._attachment:
                raise ELib3MFException("Texture has no attachment")
            path = _clean_zip_name(r._attachment.GetPath())
            if path in textures and textures[path] != r._content_type:
                raise ELib3MFException("Conflicting texture content types for " + path)
            textures[path] = r._content_type
    return textures


def _model_parts(model):
    parts = {model._root_part} | {r._package_path for r in model._resources.values()}
    if any(not p.endswith(".model") for p in parts):
        raise ELib3MFException("Invalid model part path")
    ids = {}
    for r in model._resources.values():
        key = (r._package_path, r._local_id)
        if key in ids:
            raise ELib3MFException("Duplicate local resource ID in " + r._package_path)
        ids[key] = r
    for r in model._resources.values():
        if isinstance(r, MeshObject):
            if r._object_property:
                _prop_local_id(model, r._object_property[0], r._package_path)
            for prop in r._tri_props:
                if prop:
                    _prop_local_id(model, prop.ResourceID, r._package_path)
    _resource_emit_order(model)  # check cross-part component references
    return parts


@dataclass
class PackageValidationReport:
    """Structural OPC checks plus separate per-mesh geometric diagnostics."""

    issues: list[ValidationIssue] = field(default_factory=list)
    meshes: dict[int, ValidationReport] = field(default_factory=dict)

    @property
    def ok(self):
        return all(i.severity != "error" for i in self.issues) and all(
            m.ok for m in self.meshes.values()
        )

    def to_dict(self):
        return {
            "ok": self.ok,
            "issues": [
                {"code": i.code, "severity": i.severity, "message": i.message}
                for i in self.issues
            ],
            "meshes": {str(k): v.to_dict() for k, v in self.meshes.items()},
        }


def Check3MFPackage(
    data, *, geometry=True, check_self_intersections=False, max_pairs=200000
):
    """Inspect archive integrity and supported Core/Production/Materials features.

    This is deliberately *not* complete ISO/XSD or native-lib3mf certification.
    Unknown vendor extensions are retained but not verified semantically.
    """
    report = PackageValidationReport()

    def error(code, msg):
        report.issues.append(ValidationIssue(code, "error", msg))

    def warning(code, msg):
        report.issues.append(ValidationIssue(code, "warning", msg))

    try:
        with ZipFile(BytesIO(data)) as z:
            parts = set(z.namelist())
            if not z.testzip() is None:
                error("zip_crc", "Invalid ZIP CRC")
            for required in ("[Content_Types].xml", "_rels/.rels"):
                if required not in parts:
                    error("missing_package_part", "Missing " + required)
            if "[Content_Types].xml" in parts:
                try:
                    content = _xml_from_bytes(z.read("[Content_Types].xml"))
                    overrides = {
                        n.get("PartName"): n.get("ContentType")
                        for n in content.findall(_tag("Override", CONTENT))
                    }
                    defaults = {
                        n.get("Extension"): n.get("ContentType")
                        for n in content.findall(_tag("Default", CONTENT))
                    }
                    for name in parts:
                        if not name.endswith(".model"):
                            continue
                        if (
                            overrides.get("/" + name, defaults.get("model"))
                            != MODEL_CONTENT
                        ):
                            error(
                                "missing_model_content_type",
                                name + " lacks model content type",
                            )
                except ELib3MFException as ex:
                    error("content_types", str(ex))
            root = _find_start_part(z)
            for part in parts:
                if not part.endswith(".rels"):
                    continue
                rels = _xml_from_bytes(z.read(part))
                if rels.tag != _tag("Relationships", PKGREL):
                    error("relationship_xml", "Wrong root in " + part)
                    continue
                if part == "_rels/.rels":
                    src = "/"
                else:
                    dirname, name = posixpath.split(part)
                    if posixpath.basename(dirname) != "_rels":
                        error("relationship_location", "Invalid location " + part)
                        continue
                    src = posixpath.join(posixpath.dirname(dirname), name[:-5])
                for item in rels.findall(_tag("Relationship", PKGREL)):
                    if item.get("TargetMode", "Internal") != "Internal":
                        continue
                    try:
                        path = (
                            _relationship_target(src, item.get("Target"))
                            if src != "/"
                            else _clean_zip_name(item.get("Target"))
                        )
                        if path not in parts:
                            error("dangling_relationship", part + " -> " + path)
                    except ELib3MFException as ex:
                        error("invalid_relationship", str(ex))
            try:
                model = _load_production(z, bytes(data))
                if geometry:
                    report.meshes = model.Validate(
                        check_self_intersections=check_self_intersections,
                        max_pairs=max_pairs,
                    )
                for msg in model._warnings:
                    if msg.startswith("Texture relationship "):
                        error("missing_texture_relationship", msg)
                    elif msg.startswith("Unsupported resource"):
                        warning("unsupported_extension", msg)
            except (ELib3MFException, KeyError, ValueError) as ex:
                error("model_parse", str(ex))
    except (BadZipFile, KeyError, ET.ParseError, ValueError) as ex:
        error("archive", str(ex))
    return report


class Reader:
    def __init__(self, model):
        self._model = model
        self._strict = False

    def SetStrictModeActive(self, enabled):
        self._strict = bool(enabled)

    def GetStrictModeActive(self):
        return self._strict

    def GetWarningCount(self):
        return len(self._model._warnings)

    def GetWarning(self, index):
        return (self._model._warnings[index], 0)

    def ReadFromBuffer(self, data):
        try:
            with ZipFile(BytesIO(data), "r") as zf:
                names = zf.namelist()
                if len(names) != len(set(names)):
                    raise ELib3MFException("Duplicate 3MF ZIP part names are ambiguous")
                parsed = _load_production(zf, data)
                if self._strict and parsed._warnings:
                    raise Unsupported3MFError(
                        "Strict read: " + "; ".join(parsed._warnings)
                    )
        except (BadZipFile, KeyError) as e:
            raise ELib3MFException("Invalid 3MF ZIP container: " + str(e)) from e
        self._model.__dict__.update(parsed.__dict__)
        for resource in self._model._resources.values():
            resource._model = self._model
            if isinstance(resource, Texture2D) and resource._attachment is not None:
                resource._attachment._model = self._model

    def ReadFromFile(self, filename):
        with open(filename, "rb") as f:
            self.ReadFromBuffer(f.read())


class Writer:
    def __init__(self, model):
        self._model = model
        self._compress = ZIP_DEFLATED
        self._allow_lossy = False
        self._strict = False

    def SetStrictModeActive(self, enabled):
        self._strict = bool(enabled)

    def GetStrictModeActive(self):
        return self._strict

    def GetWarningCount(self):
        return len(self._model._warnings)

    def GetWarning(self, index):
        return (self._model._warnings[index], 0)

    def GetStreamSize(self):
        return len(self.WriteToBuffer())

    def AllowLossyWrite(self, enabled=True):
        """Allow explicitly risky modifications to opaque indexed extensions.

        Unrecognized package parts are still retained. Original digital
        signatures are never silently invalidated.
        """
        self._allow_lossy = bool(enabled)

    def SetCompression(self, level):
        if not 0 <= int(level) <= 9:
            raise ELib3MFException("Compression level must be 0..9")
        self._compress = ZIP_STORED if int(level) == 0 else ZIP_DEFLATED

    def WriteToBuffer(self):
        if self._strict:
            if any(
                not obj.IsValid()
                for obj in self._model._resources.values()
                if isinstance(obj, Object)
            ):
                raise ELib3MFException("Strict write: invalid mesh or component object")
            for obj in self._model._resources.values():
                if isinstance(obj, MeshObject) and obj.GetType() == ObjectType.Model:
                    report = obj.ValidateGeometry()
                    if not report.ok:
                        raise ELib3MFException(
                            "Strict write: mesh validation failed: "
                            + ", ".join(
                                sorted(
                                    {
                                        e.code
                                        for e in report.issues
                                        if e.severity == "error"
                                    }
                                )
                            )
                        )
        model = self._model
        _verify_model(model)
        parts = _model_parts(model)
        textures = _material_paths(model)
        if model._original_package is None:
            production = model._production_enabled or len(parts) > 1
            newparts = {}
            for part in sorted(parts):
                newparts[part] = _new_part_to_xml(model, part, production)
            newparts["_rels/.rels"] = (
                _root_rels()
                if model._root_part == MODEL_PATH
                else _root_rels_for(model._root_part)
            )
            for part in sorted(parts):
                requirements = _required_relationships(model, part, parts)
                if requirements:
                    newparts[_relationships_part(part)] = _merge_relationships(
                        None, requirements, part
                    )
            for path in textures:
                r = next(
                    r
                    for r in model._resources.values()
                    if isinstance(r, Texture2D)
                    and _clean_zip_name(r.GetAttachment().GetPath()) == path
                )
                newparts[path] = r._attachment.ReadFromBuffer()
            newparts["[Content_Types].xml"] = _update_content_types(
                None, parts, textures
            )
            buf = BytesIO()
            with ZipFile(buf, "w", compression=self._compress, allowZip64=True) as zf:
                for part, payload in newparts.items():
                    zf.writestr(part, payload)
            return buf.getvalue()
        # Preserve all original ZIP members, adding only required relationships,
        # material/texture entries and changed .model XML files.
        dirty = {
            p
            for p, before in model._original_part_states.items()
            if _snapshot_part(model, p) != before
        }
        with ZipFile(BytesIO(model._original_package), "r") as src:
            existing = set(src.namelist())
            if not dirty and all(
                path in existing and src.read(path) == payload
                for path, payload in model._attachment_data.items()
            ):
                return model._original_package
            if any(part not in model._original_parts for part in parts):
                raise Unsupported3MFError(
                    "Adding new model parts to an imported package is not supported"
                )
            writes = {}
            for path, payload in model._attachment_data.items():
                if path not in existing or src.read(path) != payload:
                    writes[path] = payload
            for path in dirty:
                writes[path] = _patch_part_xml(
                    model, path, model._original_parts[path], self._allow_lossy
                )
            # Add referenced textures/relationships absent from old packages.
            for part in sorted(parts):
                req = _required_relationships(model, part, parts)
                if req:
                    relpart = _relationships_part(part)
                    previous = src.read(relpart) if relpart in existing else None
                    merged = _merge_relationships(previous, req, part)
                    if previous != merged:
                        writes[relpart] = merged
            previous = (
                src.read("[Content_Types].xml")
                if "[Content_Types].xml" in existing
                else None
            )
            content = _update_content_types(previous, parts, textures)
            if content != previous:
                writes["[Content_Types].xml"] = content
            if not writes:
                return model._original_package
            if any(
                n.startswith("_xmlsignatures/") or n.startswith("origin.sigs")
                for n in existing
            ):
                raise Unsupported3MFError(
                    "Editing signed 3MF packages invalidates digital signatures"
                )
            buf = BytesIO()
            with ZipFile(buf, "w", allowZip64=True) as dst:
                dst.comment = src.comment
                for info in src.infolist():
                    dst.writestr(
                        info,
                        (
                            b""
                            if info.is_dir()
                            else writes.pop(info.filename, src.read(info.filename))
                        ),
                    )
                for path, payload in writes.items():
                    dst.writestr(path, payload, compress_type=self._compress)
            return buf.getvalue()

    def WriteToFile(self, filename):
        data = self.WriteToBuffer()
        with open(filename, "wb") as f:
            f.write(data)


__all__ = [
    "get_wrapper",
    "Wrapper",
    "Model",
    "ModelUnit",
    "ObjectType",
    "PropertyType",
    "Position",
    "Triangle",
    "TriangleProperties",
    "Transform",
    "Color",
    "Box",
    "MetaData",
    "MetaDataGroup",
    "Resource",
    "Object",
    "MeshObject",
    "ComponentsObject",
    "Component",
    "BuildItem",
    "BaseMaterialGroup",
    "ColorGroup",
    "Attachment",
    "Texture2D",
    "Texture2DGroup",
    "CompositeMaterials",
    "MultiPropertyGroup",
    "Tex2Coord",
    "CompositeConstituent",
    "MultiPropertyLayer",
    "ValidationIssue",
    "ValidationReport",
    "PackageValidationReport",
    "Check3MFPackage",
    "Reader",
    "Writer",
    "ELib3MFException",
    "Unsupported3MFError",
]
