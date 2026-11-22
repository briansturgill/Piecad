"""Regression tests for standard-library Production writer and Materials extension."""
import io
import unittest
import zipfile
import xml.etree.ElementTree as ET
import base64
import lib3mf

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLJ0AAAAABJRU5ErkJggg==')


def build_complete_model():
    m = lib3mf.get_wrapper().CreateModel()
    m.EnableProductionExtension()
    a = m.AddAttachment('/3D/Textures/checker.png', lib3mf.TEXTURE_REL)
    a.WriteToBuffer(PNG)
    tex = m.AddTexture2DFromAttachment(a)
    tex.SetFilter('nearest')
    uv = m.AddTexture2DGroup(tex)
    for pair in ((0,0),(1,0),(0,1)): uv.AddTex2Coord(pair)
    base = m.AddBaseMaterialGroup()
    base.AddMaterial('PLA red', (255,0,0,255))
    base.AddMaterial('PLA blue', (0,0,255,255))
    comp = m.AddCompositeMaterials(base)
    comp.AddComposite([(0,0.3),(1,0.7)])
    multi = m.AddMultiPropertyGroup()
    multi.AddLayer(lib3mf.MultiPropertyLayer(base.GetResourceID(),'mix'))
    multi.AddLayer(lib3mf.MultiPropertyLayer(uv.GetResourceID(),'multiply'))
    multi.AddMultiProperty((0,1))
    mesh = m.AddMeshObject()
    mesh.SetName('Textured')
    mesh.SetGeometry([(0,0,0),(10,0,0),(0,10,0),(0,0,10)],
                     [(0,2,1),(0,1,3),(0,3,2),(1,2,3)])
    mesh.SetTriangleProperties(0,lib3mf.TriangleProperties(uv.GetResourceID(),[0,1,2]))
    mesh.SetTriangleProperties(1,lib3mf.TriangleProperties(comp.GetResourceID(),[0,0,0]))
    mesh.SetTriangleProperties(2,lib3mf.TriangleProperties(multi.GetResourceID(),[0,0,0]))
    for r in (base,tex,uv,comp,multi,mesh):
        m.AssignResourceToPart(r, '/3D/Objects/textured.model')
    assembly=m.AddComponentsObject()
    assembly.SetName('Assembly')
    assembly.AddComponent(mesh)
    m.AddBuildItem(assembly)
    m.AddBuildItem(mesh)
    return m


class MaterialProductionTests(unittest.TestCase):
    def test_writer_creates_valid_multi_file_package(self):
        model=build_complete_model()
        payload=model.QueryWriter('3mf').WriteToBuffer()
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            names=set(z.namelist())
            self.assertIn('3D/3dmodel.model',names)
            self.assertIn('3D/Objects/textured.model',names)
            self.assertIn('3D/_rels/3dmodel.model.rels',names)
            self.assertIn('3D/Objects/_rels/textured.model.rels',names)
            self.assertEqual(z.read('3D/Textures/checker.png'),PNG)
            root=ET.fromstring(z.read('3D/3dmodel.model'))
            self.assertTrue(root.find(f'.//{{{lib3mf.CORE}}}build').get(f'{{{lib3mf.PROD}}}UUID'))
            self.assertEqual(len(root.findall(f'.//{{{lib3mf.CORE}}}item')),2)
            child=z.read('3D/Objects/textured.model')
            self.assertIn(b'texture2dgroup',child)
            self.assertIn(b'compositematerials',child)
            self.assertIn(b'multiproperties',child)
        loaded=lib3mf.get_wrapper().CreateModel()
        loaded.QueryReader('3mf').ReadFromBuffer(payload)
        self.assertEqual(len(list(loaded.GetMeshObjects())),1)
        self.assertEqual(loaded.GetBuildItems().Count(),2)
        self.assertEqual(loaded.GetTexture2Ds().Count(),1)
        self.assertEqual(loaded.GetTexture2DGroups().Count(),1)
        self.assertEqual(loaded.GetCompositeMaterials().Count(),1)
        self.assertEqual(loaded.GetMultiPropertyGroups().Count(),1)
        self.assertEqual(next(iter(loaded.GetTexture2Ds())).GetAttachment().ReadFromBuffer(),PNG)
        mesh=next(iter(loaded.GetMeshObjects()))
        self.assertEqual(mesh.GetTriangleProperties(0).PropertyIDs,[0,1,2])
        self.assertEqual(mesh.GetTriangleProperties(1).PropertyIDs,[0,0,0])
        self.assertEqual(mesh.GetTriangleProperties(2).PropertyIDs,[0,0,0])
        self.assertEqual(loaded.QueryWriter('3mf').WriteToBuffer(),payload)
        mesh.SetVertex(0,(0,0,2))
        altered=loaded.QueryWriter('3mf').WriteToBuffer()
        with zipfile.ZipFile(io.BytesIO(altered)) as z:
            self.assertEqual(z.read('3D/Textures/checker.png'),PNG)
        loaded2=lib3mf.get_wrapper().CreateModel()
        loaded2.QueryReader('3mf').ReadFromBuffer(altered)
        self.assertEqual(next(iter(loaded2.GetMeshObjects())).GetVertex(0).Coordinates,[0,0,2])

    def test_production_uuids_stable_across_writes(self):
        m=build_complete_model()
        a=m.QueryWriter('3mf').WriteToBuffer()
        b=m.QueryWriter('3mf').WriteToBuffer()
        self.assertEqual(a,b,'UUIDs should persist on same Model instance')

    def test_edit_material_groups_without_losing_image(self):
        m=build_complete_model()
        original=m.QueryWriter('3mf').WriteToBuffer()
        loaded=lib3mf.get_wrapper().CreateModel()
        loaded.QueryReader('3mf').ReadFromBuffer(original)
        group=next(iter(loaded.GetTexture2DGroups()))
        group.AddTex2Coord((0.5,0.5))
        composite=next(iter(loaded.GetCompositeMaterials()))
        composite.AddComposite(((0,0.8),(1,0.2)))
        multi=next(iter(loaded.GetMultiPropertyGroups()))
        multi.AddMultiProperty((1,3))
        modified=loaded.QueryWriter('3mf').WriteToBuffer()
        again=lib3mf.get_wrapper().CreateModel()
        again.QueryReader('3mf').ReadFromBuffer(modified)
        self.assertEqual(next(iter(again.GetTexture2DGroups())).GetCount(),4)
        self.assertEqual(next(iter(again.GetCompositeMaterials())).GetCount(),2)
        self.assertEqual(next(iter(again.GetMultiPropertyGroups())).GetCount(),2)

    def test_simple_fresh_color_and_materials_roundtrip(self):
        m=lib3mf.get_wrapper().CreateModel()
        base=m.AddBaseMaterialGroup(); base.AddMaterial('orange',(255,102,0,255))
        mesh=m.AddMeshObject(); mesh.SetGeometry([(0,0,0),(1,0,0),(0,1,0)],[(0,1,2)])
        mesh.SetObjectLevelProperty(base.GetResourceID(),0)
        m.AddBuildItem(mesh)
        payload=m.QueryWriter('3mf').WriteToBuffer()
        m2=lib3mf.get_wrapper().CreateModel(); m2.QueryReader('3mf').ReadFromBuffer(payload)
        self.assertEqual(m2.GetBaseMaterialGroups().Count(),1)
        self.assertEqual(m2.GetMeshObjects().Count(),1)

    def test_cross_part_materials_are_rejected(self):
        m=lib3mf.get_wrapper().CreateModel()
        b=m.AddBaseMaterialGroup(); b.AddMaterial('a',(0,0,0,255))
        mesh=m.AddMeshObject(); mesh.SetGeometry([(0,0,0),(1,0,0),(0,1,0)],[(0,1,2)])
        mesh.SetObjectLevelProperty(b.GetResourceID(),0)
        m.AddBuildItem(mesh)
        m.AssignResourceToPart(mesh,'3D/Child.model')
        with self.assertRaises((lib3mf.ELib3MFException,lib3mf.Unsupported3MFError)):
            m.QueryWriter('3mf').WriteToBuffer()

    def test_texture_edit_preserves_unknown_parts(self):
        m=build_complete_model()
        original=m.QueryWriter('3mf').WriteToBuffer()
        newparts={}
        with zipfile.ZipFile(io.BytesIO(original)) as z:
            for n in z.namelist(): newparts[n]=z.read(n)
        newparts['Metadata/vendor.json']=b'{"custom":true}'
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
            for k,v in newparts.items(): z.writestr(k,v)
        loaded=lib3mf.get_wrapper().CreateModel()
        loaded.QueryReader('3mf').ReadFromBuffer(buf.getvalue())
        tex=next(iter(loaded.GetTexture2Ds()))
        tex.GetAttachment().WriteToBuffer(PNG+b'\x01')
        altered=loaded.QueryWriter('3mf').WriteToBuffer()
        with zipfile.ZipFile(io.BytesIO(altered)) as z:
            self.assertEqual(z.read('Metadata/vendor.json'),b'{"custom":true}')
            self.assertEqual(z.read('3D/Textures/checker.png'),PNG+b'\x01')


if __name__=='__main__': unittest.main()
