"""Run with: python -m unittest -v test_lib3mf (standard library only)."""
import io
import unittest
import zipfile
from xml.etree import ElementTree as ET

import lib3mf


CUBE_VERTICES = [
    (0,0,0), (2,0,0), (2,3,0), (0,3,0),
    (0,0,4), (2,0,4), (2,3,4), (0,3,4)
]
CUBE_TRIANGLES = [
    (2,1,0), (0,3,2), (4,5,6), (6,7,4),
    (0,1,5), (5,4,0), (2,3,7), (7,6,2),
    (1,2,6), (6,5,1), (3,0,4), (4,7,3)
]


class Pure3MFTests(unittest.TestCase):
    def setUp(self):
        self.wrapper = lib3mf.get_wrapper()
        self.model = self.wrapper.CreateModel()

    def cube(self):
        obj = self.model.AddMeshObject()
        obj.SetName('Box')
        obj.SetGeometry(CUBE_VERTICES, CUBE_TRIANGLES)
        return obj

    def roundtrip(self):
        data = self.model.QueryWriter('3mf').WriteToBuffer()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            self.assertIn('3D/3dmodel.model', zf.namelist())
            self.assertIn('[Content_Types].xml', zf.namelist())
            self.assertIn('_rels/.rels', zf.namelist())
            ET.fromstring(zf.read('3D/3dmodel.model'))
        loaded = self.wrapper.CreateModel()
        loaded.QueryReader('3mf').ReadFromBuffer(data)
        return loaded

    def test_geometry_and_api(self):
        m = self.cube()
        self.assertEqual(m.GetVertexCount(), 8)
        self.assertEqual(m.GetTriangleCount(), 12)
        self.assertTrue(m.IsManifoldAndOriented())
        self.assertEqual(m.GetVertex(3).Coordinates, [0,3,0])
        self.assertEqual(m.GetTriangle(0).Indices, [2,1,0])
        m.SetVertex(3, (0,3,0))
        m.SetTriangle(0, (2,1,0))
        self.assertEqual(m.GetVertices()[0].Coordinates, [0,0,0])
        self.assertEqual(m.GetTriangleIndices()[-1].Indices, [4,7,3])
        self.assertEqual(m.GetOutbox().MaxCoordinate, [2,3,4])
        self.model.AddBuildItem(m, self.wrapper.GetIdentityTransform())
        self.assertEqual(self.roundtrip().GetMeshObjects().Count(), 1)

    def test_composition_and_transforms(self):
        mesh = self.cube()
        group = self.model.AddComponentsObject()
        t = self.wrapper.GetTranslationTransform(11, 0, -2)
        group.AddComponent(mesh, t)
        build = self.model.AddBuildItem(group, self.wrapper.GetScaleTransform(2,2,2))
        self.assertEqual(build.GetOutbox().MinCoordinate, [22,0,-4])
        self.assertEqual(build.GetOutbox().MaxCoordinate, [26,6,4])
        restored = self.roundtrip()
        self.assertEqual(restored.GetBuildItems().Count(), 1)
        merged = restored.MergeToModel()
        v = merged.GetMeshObjects()._entries[0].GetVertex(0)
        self.assertEqual(v.Coordinates, [22,0,-4])

    def test_colorgroup_and_properties(self):
        mat = self.model.AddBaseMaterialGroup()
        matid = mat.AddMaterial('Red PLA', self.wrapper.RGBAToColor(255,0,0,255))
        color_group = self.model.AddColorGroup()
        blue = color_group.AddColor(lib3mf.Color(0, 0, 255, 128))
        mesh = self.cube()
        mesh.SetObjectLevelProperty(mat.GetResourceID(), matid)
        mesh.SetTriangleProperties(0, lib3mf.TriangleProperties(color_group.GetResourceID(), [blue]*3))
        self.model.AddBuildItem(mesh)
        restored = self.roundtrip()
        loaded = restored.GetMeshObjects()._entries[0]
        self.assertEqual(loaded.GetObjectLevelProperty(), (True,mat.GetResourceID(),matid))
        self.assertEqual(loaded.GetTriangleProperties(0).ResourceID, color_group.GetResourceID())
        self.assertEqual(loaded.GetTriangleProperties(0).PropertyIDs, [blue]*3)
        self.assertEqual(restored.GetColorGroupByID(color_group.GetResourceID()).GetColor(0).Alpha, 128)
        self.assertEqual(restored.GetBaseMaterialGroupByID(mat.GetResourceID()).GetName(0), 'Red PLA')

    def test_metadata_and_units(self):
        mesh = self.cube()
        self.model.SetUnit(lib3mf.ModelUnit.Inch)
        self.model.SetLanguage('en-US')
        self.model.GetMetaDataGroup().AddMetaData('', 'Application', 'Pure3MF', '', True)
        mesh.GetMetaDataGroup().AddMetaData('', 'Title', 'The Box')
        item = self.model.AddBuildItem(mesh)
        item.SetPartNumber('XX-100')
        restored = self.roundtrip()
        self.assertEqual(restored.GetUnit(), lib3mf.ModelUnit.Inch)
        self.assertEqual(restored.GetLanguage(), 'en-US')
        self.assertEqual(restored.GetMetaDataGroup().GetMetaDataByKey('', 'Application').GetValue(), 'Pure3MF')
        self.assertEqual(restored.GetMeshObjects()._entries[0].GetMetaDataGroup().GetMetaData(0).GetValue(), 'The Box')
        self.assertEqual(restored.GetBuildItems()._entries[0].GetPartNumber(), 'XX-100')

    def test_iterators(self):
        self.cube()
        it = self.model.GetMeshObjects()
        self.assertEqual(it.Count(), 1)
        with self.assertRaises(lib3mf.ELib3MFException): it.GetCurrent()
        self.assertTrue(it.MoveNext())
        self.assertEqual(it.GetCurrentMeshObject().GetName(), 'Box')
        self.assertFalse(it.MoveNext())
        self.assertTrue(it.MovePrevious())

    def test_invalid_geometry(self):
        mesh = self.model.AddMeshObject()
        mesh.AddVertex((0,0,0))
        mesh.AddVertex((0,1,0))
        mesh.AddVertex((1,0,0))
        self.assertEqual(mesh.AddTriangle((0,1,2)), 0)
        self.assertFalse(mesh.IsManifoldAndOriented())
        with self.assertRaises(lib3mf.ELib3MFException): mesh.AddTriangle((0,0,1))
        with self.assertRaises(lib3mf.ELib3MFException): mesh.AddTriangle((0,1,3))
        with self.assertRaises(lib3mf.ELib3MFException): mesh.SetGeometry([(0,0,0)], [(0,1,2)])
        self.assertEqual(mesh.GetVertexCount(), 3)

    def test_cycle(self):
        a = self.model.AddComponentsObject()
        b = self.model.AddComponentsObject()
        a.AddComponent(b)
        with self.assertRaises(lib3mf.ELib3MFException): b.AddComponent(a)

    def test_untrusted_relationship(self):
        mesh = self.cube()
        self.model.AddBuildItem(mesh)
        original = self.model.QueryWriter('3mf').WriteToBuffer()
        with zipfile.ZipFile(io.BytesIO(original)) as zf:
            parts = {n: zf.read(n) for n in zf.namelist()}
        parts['_rels/.rels'] = parts['_rels/.rels'].replace(b'/3D/3dmodel.model', b'/../bad.model')
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w') as zf:
            for k,v in parts.items(): zf.writestr(k,v)
        with self.assertRaises(lib3mf.ELib3MFException):
            self.model.QueryReader('3mf').ReadFromBuffer(out.getvalue())

    def test_single_triangle_roundtrip(self):
        m = self.model.AddMeshObject()
        for p in ((0,0,0),(1,0,0),(0,1,0)): m.AddVertex(p)
        m.AddTriangle([0,1,2])
        self.model.AddBuildItem(m)
        self.assertEqual(self.roundtrip().GetMeshObjects()._entries[0].GetTriangleCount(), 1)


if __name__ == '__main__': unittest.main()

class CompatibilityExtraTests(unittest.TestCase):
    def test_component_is_serialized_after_target(self):
        m = lib3mf.get_wrapper().CreateModel()
        assembly = m.AddComponentsObject()
        mesh = m.AddMeshObject()
        mesh.SetGeometry([(0,0,0),(1,0,0),(0,1,0)],[(0,1,2)])
        assembly.AddComponent(mesh)
        m.AddBuildItem(assembly)
        with zipfile.ZipFile(io.BytesIO(m.QueryWriter('3mf').WriteToBuffer())) as z:
            r = ET.fromstring(z.read('3D/3dmodel.model'))
        ns = {'t':lib3mf.CORE}
        objects = r.findall('.//t:object', ns)
        self.assertEqual([int(o.get('id')) for o in objects], [mesh.GetResourceID(), assembly.GetResourceID()])

    def test_namespaced_metadata_round_trip(self):
        m = lib3mf.get_wrapper().CreateModel()
        mesh = m.AddMeshObject()
        mesh.SetGeometry([(0,0,0),(1,0,0),(0,1,0)],[(0,1,2)])
        m.AddBuildItem(mesh)
        m.GetMetaDataGroup().AddMetaData('urn:company','custom','yes')
        data = m.QueryWriter('3mf').WriteToBuffer()
        m2 = lib3mf.get_wrapper().CreateModel()
        m2.QueryReader('3mf').ReadFromBuffer(data)
        self.assertEqual(m2.GetMetaDataGroup().GetMetaDataByKey('urn:company','custom').GetValue(),'yes')

    def test_unknown_parts_readable_but_safe_write(self):
        m = lib3mf.get_wrapper().CreateModel()
        mesh = m.AddMeshObject()
        mesh.SetGeometry([(0,0,0),(1,0,0),(0,1,0)],[(0,1,2)])
        m.AddBuildItem(mesh)
        data = m.QueryWriter('3mf').WriteToBuffer()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            parts = {n: z.read(n) for n in z.namelist()}
        parts['Metadata/settings.json'] = b'{}'
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w') as z:
            for name, contents in parts.items(): z.writestr(name, contents)
        m2 = lib3mf.get_wrapper().CreateModel()
        reader = m2.QueryReader('3mf')
        reader.ReadFromBuffer(out.getvalue())
        self.assertEqual(reader.GetWarningCount(), 1)
        self.assertEqual(m2.QueryWriter('3mf').WriteToBuffer(), out.getvalue())
        m2.GetMeshObjects()._entries[0].SetVertex(0, (9, 0, 0))
        changed = m2.QueryWriter('3mf').WriteToBuffer()
        with zipfile.ZipFile(io.BytesIO(changed)) as z:
            self.assertEqual(z.read('Metadata/settings.json'), b'{}')
        strictmodel = lib3mf.get_wrapper().CreateModel()
        strictreader = strictmodel.QueryReader('3mf')
        strictreader.SetStrictModeActive(True)
        with self.assertRaises(lib3mf.Unsupported3MFError): strictreader.ReadFromBuffer(out.getvalue())

class ExtensionSafetyTests(unittest.TestCase):
    def test_production_namespace_is_not_silently_stripped(self):
        model = lib3mf.get_wrapper().CreateModel()
        mesh = model.AddMeshObject()
        mesh.SetGeometry([(0,0,0),(1,0,0),(0,1,0)],[(0,1,2)])
        model.AddBuildItem(mesh)
        data = model.QueryWriter('3mf').WriteToBuffer()
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            parts = {name:archive.read(name) for name in archive.namelist()}
        parts['3D/3dmodel.model'] = parts['3D/3dmodel.model'].replace(
            b'unit="millimeter"', ('xmlns:p="' + lib3mf.PROD + '" requiredextensions="p" unit="millimeter"').encode())
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as archive:
            for name,data in parts.items(): archive.writestr(name,data)
        parsed = lib3mf.get_wrapper().CreateModel()
        parsed.QueryReader('3mf').ReadFromBuffer(buf.getvalue())
        self.assertEqual(parsed.QueryWriter('3mf').WriteToBuffer(), buf.getvalue())
        parsed.GetMeshObjects()._entries[0].SetVertex(0, (9, 0, 0))
        with zipfile.ZipFile(io.BytesIO(parsed.QueryWriter('3mf').WriteToBuffer())) as z:
            model_xml = z.read('3D/3dmodel.model')
            self.assertIn(b'requiredextensions="p"', model_xml)
            self.assertIn(b'xmlns:p=', model_xml)
