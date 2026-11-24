import io
import zipfile
from xml.etree import ElementTree as ET

import lib3mf
import pytest
import test_3mf_conformance


def _package():
    model = lib3mf.Wrapper().CreateModel()
    mesh = model.AddMeshObject()
    mesh.SetGeometry(
        [(0.0000000001, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)],
        [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)],
    )
    model.AddBuildItem(mesh)
    with zipfile.ZipFile(io.BytesIO(model.QueryWriter("3mf").WriteToBuffer())) as z:
        return {name: z.read(name) for name in z.namelist()}


def _archive(parts):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)
    return output.getvalue()


def _read(data):
    model = lib3mf.Wrapper().CreateModel()
    model.QueryReader("3mf").ReadFromBuffer(data)
    return model


def test_rewrite_preserves_namespaced_metadata_and_coordinate_precision():
    parts = _package()
    xml = parts["3D/3dmodel.model"]
    xml = xml.replace(b"<model ", b'<model xmlns:v="urn:vendor" ', 1)
    xml = xml.replace(
        b"<resources>", b'<metadata name="v:title">value</metadata><resources>'
    )
    parts["3D/3dmodel.model"] = xml
    model = _read(_archive(parts))
    model.GetMetaDataGroup().AddMetaData("", "Description", "edited")

    rewritten = model.QueryWriter("3mf").WriteToBuffer()
    with zipfile.ZipFile(io.BytesIO(rewritten)) as z:
        ET.fromstring(z.read("3D/3dmodel.model"))
    loaded = _read(rewritten)
    assert (
        loaded.GetMetaDataGroup().GetMetaDataByKey("urn:vendor", "title").GetValue()
        == "value"
    )
    assert (
        next(iter(loaded.GetMeshObjects())).GetVertex(0).Coordinates[0] == 0.0000000001
    )


def test_rewrite_preserves_required_extension_namespace_alias():
    parts = _package()
    xml = parts["3D/3dmodel.model"].replace(
        b"<model ",
        f'<model xmlns:m="{lib3mf.MAT}" xmlns:v="{lib3mf.MAT}" '
        'requiredextensions="m" '.encode(),
        1,
    )
    parts["3D/3dmodel.model"] = xml.replace(
        b"<resources>", b'<metadata name="v:title">value</metadata><resources>'
    )
    model = _read(_archive(parts))
    model.GetMetaDataGroup().AddMetaData("", "Description", "edited")
    rewritten = model.QueryWriter("3mf").WriteToBuffer()
    loaded = _read(rewritten)
    assert (
        loaded.GetMetaDataGroup().GetMetaDataByKey(lib3mf.MAT, "title").GetValue()
        == "value"
    )
    fresh = lib3mf.Wrapper().CreateModel()
    colors = fresh.AddColorGroup()
    colors.AddColor(lib3mf.Color(255, 0, 0, 255))
    _read(fresh.QueryWriter("3mf").WriteToBuffer())


@pytest.mark.parametrize("part", ["3D/3dmodel", "3D/3dmodel.part"])
def test_rewrite_model_part_without_model_extension(part):
    parts = _package()
    parts[part] = parts.pop("3D/3dmodel.model")
    parts["_rels/.rels"] = parts["_rels/.rels"].replace(
        b"3D/3dmodel.model", part.encode()
    )
    parts["[Content_Types].xml"] = parts["[Content_Types].xml"].replace(
        b"3D/3dmodel.model", part.upper().encode()
    )
    model = _read(_archive(parts))
    model.GetMetaDataGroup().AddMetaData("", "Description", "edited")
    result = model.QueryWriter("3mf").WriteToBuffer()
    assert lib3mf.Check3MFPackage(result, geometry=False).ok
    assert next(iter(_read(result).GetMeshObjects())).GetTriangleCount() == 4


def test_checker_validates_content_type_for_extensionless_start_part():
    parts = _package()
    parts["3D/3dmodel"] = parts.pop("3D/3dmodel.model")
    parts["_rels/.rels"] = parts["_rels/.rels"].replace(
        b"3D/3dmodel.model", b"3D/3dmodel"
    )
    parts["[Content_Types].xml"] = parts["[Content_Types].xml"].replace(
        lib3mf.MODEL_CONTENT.encode(), b"application/invalid"
    )
    report = lib3mf.Check3MFPackage(_archive(parts), geometry=False)
    assert any(issue.code == "missing_model_content_type" for issue in report.issues)


def test_mirrored_merge_preserves_mesh_orientation():
    model = _read(_archive(_package()))
    build = next(iter(model.GetBuildItems()))
    build.SetObjectTransform(
        lib3mf.Transform([[-1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0]])
    )
    merged = model.MergeToModel()
    report = next(iter(merged.GetMeshObjects())).ValidateGeometry()
    assert report.ok, report.to_dict()
    assert report.signed_volume > 0


def test_required_unknown_extension_is_rejected():
    parts = _package()
    parts["3D/3dmodel.model"] = parts["3D/3dmodel.model"].replace(
        b"<model ", b'<model xmlns:v="urn:unknown" requiredextensions="v" ', 1
    )
    with pytest.raises(lib3mf.Unsupported3MFError, match="required extension"):
        _read(_archive(parts))


def test_harness_checks_negative_unknown_required_extension(tmp_path, capsys):
    parts = _package()
    parts["3D/3dmodel.model"] = parts["3D/3dmodel.model"].replace(
        b"<model ", b'<model xmlns:v="urn:unknown" requiredextensions="v" ', 1
    )
    case = tmp_path / "negative_test_cases" / "unknown.3mf"
    case.parent.mkdir()
    case.write_bytes(_archive(parts))
    assert test_3mf_conformance.main([str(case.parent), "--roundtrip", "none"]) == 0
    assert "1 /     0 /     0" in capsys.readouterr().out


def test_harness_rewrite_marker_uses_namespaced_metadata():
    model = _read(_archive(_package()))
    test_3mf_conformance._force_serialization(model)
    loaded = _read(model.QueryWriter("3mf").WriteToBuffer())
    marker = loaded.GetMetaDataGroup().GetMetaDataByKey(
        test_3mf_conformance.METADATA_NAMESPACE,
        test_3mf_conformance.METADATA_MARKER,
    )
    assert marker.GetValue() == "roundtrip"


@pytest.mark.parametrize("encoding", ["utf-8", "utf-16"])
def test_doctype_is_rejected(encoding):
    parts = _package()
    xml = parts["3D/3dmodel.model"].decode("utf-8")
    xml = xml.replace("encoding='utf-8'", f"encoding='{encoding}'")
    xml = xml.replace("<model ", "<!DOCTYPE model><model ", 1)
    parts["3D/3dmodel.model"] = xml.encode(encoding)
    with pytest.raises(lib3mf.ELib3MFException, match="DTD"):
        _read(_archive(parts))


@pytest.mark.parametrize("change", ["duplicate", "empty", "wrong_rels"])
def test_invalid_content_type_declarations_are_reported(change):
    parts = _package()
    root = ET.fromstring(parts["[Content_Types].xml"])
    if change == "duplicate":
        entry = root.find(f"{{{lib3mf.CONTENT}}}Override")
        root.append(ET.fromstring(ET.tostring(entry)))
    elif change == "empty":
        ET.SubElement(
            root, f"{{{lib3mf.CONTENT}}}Default", Extension="", ContentType="image/png"
        )
    else:
        root.find(f"{{{lib3mf.CONTENT}}}Default").set(
            "ContentType", "application/invalid"
        )
    parts["[Content_Types].xml"] = ET.tostring(root)
    assert not lib3mf.Check3MFPackage(_archive(parts), geometry=False).ok


def test_cmyk_jpeg_thumbnail_is_reported():
    parts = _package()
    root = ET.fromstring(parts["_rels/.rels"])
    ET.SubElement(
        root,
        f"{{{lib3mf.PKGREL}}}Relationship",
        Id="thumbnail",
        Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail",
        Target="/thumbnail.jpg",
    )
    parts["_rels/.rels"] = ET.tostring(root)
    root = ET.fromstring(parts["[Content_Types].xml"])
    ET.SubElement(
        root, f"{{{lib3mf.CONTENT}}}Default", Extension="jpg", ContentType="image/jpeg"
    )
    parts["[Content_Types].xml"] = ET.tostring(root)
    parts["thumbnail.jpg"] = b"\xff\xd8\xff\xc0\x00\x08\x08\x00\x01\x00\x01\x04\xff\xd9"
    report = lib3mf.Check3MFPackage(_archive(parts), geometry=False)
    assert any(issue.code == "thumbnail_cmyk" for issue in report.issues)


@pytest.mark.parametrize(
    "change",
    [
        "dot_path",
        "two_start_parts",
        "numeric_id",
        "external_thumbnail",
        "orphan_relationships",
    ],
)
def test_invalid_relationships_are_reported(change):
    parts = _package()
    root = ET.fromstring(parts["_rels/.rels"])
    relationship = root[0]
    if change == "dot_path":
        relationship.set("Target", "/3D/./3dmodel.model")
    elif change == "two_start_parts":
        duplicate = ET.fromstring(ET.tostring(relationship))
        duplicate.set("Id", "other")
        root.append(duplicate)
    elif change == "numeric_id":
        relationship.set("Id", "1bad")
    elif change == "external_thumbnail":
        ET.SubElement(
            root,
            f"{{{lib3mf.PKGREL}}}Relationship",
            Id="thumbnail",
            Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail",
            Target="https://example.invalid/a.png",
            TargetMode="External",
        )
    else:
        parts["3D/_rels/missing.model.rels"] = ET.tostring(
            ET.Element(f"{{{lib3mf.PKGREL}}}Relationships")
        )
    parts["_rels/.rels"] = ET.tostring(root)
    assert not lib3mf.Check3MFPackage(_archive(parts), geometry=False).ok


@pytest.mark.parametrize(
    "change", ["xml_space", "duplicate_metadata", "component_property"]
)
def test_invalid_model_markup_is_rejected(change):
    parts = _package()
    root = ET.fromstring(parts["3D/3dmodel.model"])
    if change == "xml_space":
        root.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    elif change == "duplicate_metadata":
        for value in ("one", "two"):
            metadata = ET.Element(f"{{{lib3mf.CORE}}}metadata", name="Title")
            metadata.text = value
            root.insert(0, metadata)
    else:
        resources = root.find(f"{{{lib3mf.CORE}}}resources")
        obj = ET.SubElement(resources, f"{{{lib3mf.CORE}}}object", id="99", pid="1")
        ET.SubElement(obj, f"{{{lib3mf.CORE}}}components")
    parts["3D/3dmodel.model"] = ET.tostring(root)
    with pytest.raises(lib3mf.ELib3MFException):
        _read(_archive(parts))
