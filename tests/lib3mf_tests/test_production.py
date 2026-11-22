"""Production Extension and opaque 3MF project-content preservation regression tests."""
import io
import unittest
import zipfile
from xml.etree import ElementTree as ET

import lib3mf

C = lib3mf.CORE
P = lib3mf.PROD
REL = lib3mf.PKGREL
MODELREL = lib3mf.START_REL
MAIN = '3D/main.model'
CHILD = '3D/Objects/mesh.model'


def production_fixture(extra_triangle_attr=False, invalid_child=False):
    root = f'''<?xml version="1.0"?>
<model xmlns="{C}" xmlns:p="{P}" xmlns:v="urn:myvendor:project"
  requiredextensions="p" unit="millimeter" xml:lang="en-US">
<metadata name="Application">Slicer Pro</metadata>
<resources>
<object id="1" name="Assembly" type="model" p:UUID="01234567-1111-2222-3333-444444444444" v:flag="keep-me">
  <components>
    <component objectid="2" p:path="/{CHILD}" p:UUID="01234567-1111-2222-3333-555555555555"
      transform="1 0 0 0 1 0 0 0 1 20 0 0"/>
  </components>
  <v:opaque>Keep even when renamed</v:opaque>
</object>
</resources>
<build p:UUID="01234567-1111-2222-3333-777777777777">
  <item objectid="1" p:UUID="01234567-1111-2222-3333-888888888888" v:setting="42"/>
  <item objectid="1" p:path="/{CHILD}" p:UUID="01234567-1111-2222-3333-999999999999"
     transform="1 0 0 0 1 0 0 0 1 5 0 0"/>
</build>
</model>'''.encode()
    attr = ' v:flag="triangle-metadata"' if extra_triangle_attr else ''
    child = f'''<?xml version="1.0"?>
<model xmlns="{C}" xmlns:p="{P}" xmlns:v="urn:myvendor:project" unit="millimeter">
<resources>
<basematerials id="3"><base name="PETG" displaycolor="#FF0000FF"/></basematerials>
<object id="1" type="model" name="ChildMesh" pid="3" pindex="0">
 <mesh><vertices>
  <vertex x="0" y="0" z="0"/><vertex x="1" y="0" z="0"/>
  <vertex x="0" y="1" z="0"/>
 </vertices><triangles><triangle v1="0" v2="1" v3="2"{attr}/></triangles></mesh>
</object>
<object id="2" type="model" name="ChildGroup"><components>
<component objectid="1" transform="1 0 0 0 1 0 0 0 1 0 1 0"{(' p:path="/'+MAIN+'"') if invalid_child else ''}/>
</components></object>
</resources><build/>
</model>'''.encode()
    relroot = f'''<Relationships xmlns="{REL}">
     <Relationship Id="r0" Type="{MODELREL}" Target="/{MAIN}"/>
    </Relationships>'''.encode()
    relchild = f'''<Relationships xmlns="{REL}">
     <Relationship Id="r1" Type="{MODELREL}" Target="/{CHILD}"/>
    </Relationships>'''.encode()
    parts = {
        '[Content_Types].xml': f'''<Types xmlns="{lib3mf.CONTENT}">
         <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
         <Override PartName="/{MAIN}" ContentType="{lib3mf.MODEL_CONTENT}"/>
         <Override PartName="/{CHILD}" ContentType="{lib3mf.MODEL_CONTENT}"/>
        </Types>'''.encode(),
        '_rels/.rels': relroot,
        MAIN: root,
        '3D/_rels/main.model.rels': relchild,
        CHILD: child,
        'Metadata/thumbnail.png': b'\x89PNG\r\n\x1a\nraw-png',
        'Metadata/slicer-config.json': b'{"layer_height":0.2}',
        'Metadata/object-settings.xml': b'<obj><x value="20"/></obj>',
    }
    return parts


def archive(parts, comment=b'original-zip-comment'):
    out = io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as zf:
        zf.comment = comment
        for key, value in parts.items(): zf.writestr(key,value)
    return out.getvalue()


def unpack(data):
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return {key:zf.read(key) for key in zf.namelist()}


class ProductionTests(unittest.TestCase):
    def read(self, parts=None):
        data = archive(parts or production_fixture())
        model = lib3mf.get_wrapper().CreateModel()
        model.QueryReader('3mf').ReadFromBuffer(data)
        return model, data

    def test_import_cross_part_and_colliding_ids(self):
        m, data = self.read()
        self.assertEqual(m.GetObjects().Count(), 3)
        assembly = next(x for x in m.GetComponentsObjects() if x.GetName() == 'Assembly')
        child_group = next(x for x in m.GetComponentsObjects() if x.GetName() == 'ChildGroup')
        mesh = next(iter(m.GetMeshObjects()))
        self.assertEqual(assembly.GetResourceID(), 1)
        self.assertNotEqual(mesh.GetResourceID(), 1)
        self.assertEqual(mesh.GetLocalResourceID(), 1)
        self.assertEqual(mesh.GetPackagePath(), '/' + CHILD)
        self.assertEqual(mesh.GetTriangleCount(), 1)
        self.assertEqual(mesh.GetObjectLevelProperty()[0], True)
        rid = mesh.GetObjectLevelProperty()[1]
        self.assertEqual(m.GetResourceByID(rid).GetName(0), 'PETG')
        self.assertIs(assembly.GetComponent(0).GetObjectResource(), child_group)
        self.assertIs(child_group.GetComponent(0).GetObjectResource(), mesh)
        self.assertEqual(m.GetBuildItems().Count(), 2)
        self.assertEqual(m.GetOutbox().MinCoordinate, [5, 0, 0])
        self.assertEqual(m.GetOutbox().MaxCoordinate, [21, 2, 0])

    def test_unchanged_byte_identical(self):
        m, data = self.read()
        self.assertEqual(m.QueryWriter('3mf').WriteToBuffer(), data)

    def test_changed_child_geometry_preserves_root_and_zip_parts(self):
        m, data = self.read()
        mesh = next(iter(m.GetMeshObjects()))
        mesh.SetVertex(1, (4, 0, 0))
        revised = m.QueryWriter('3mf').WriteToBuffer()
        a, b = unpack(data), unpack(revised)
        self.assertEqual(set(a), set(b))
        for key in a:
            if key != CHILD: self.assertEqual(a[key], b[key], key)
        self.assertNotEqual(a[CHILD], b[CHILD])
        self.assertIn(b'name="PETG"', b[CHILD])
        with zipfile.ZipFile(io.BytesIO(revised)) as z:
            self.assertEqual(z.comment, b'original-zip-comment')
        loaded = lib3mf.get_wrapper().CreateModel()
        loaded.QueryReader('3mf').ReadFromBuffer(revised)
        self.assertEqual(next(iter(loaded.GetMeshObjects())).GetVertex(1).Coordinates, [4,0,0])
        self.assertEqual(loaded.GetBuildItems().Count(), 2)

    def test_modified_root_preserves_extension_nodes_uuid_and_paths(self):
        m, data = self.read()
        assembly = next(x for x in m.GetComponentsObjects() if x.GetName() == 'Assembly')
        assembly.SetName('Updated assembly')
        item = next(iter(m.GetBuildItems()))
        item.SetObjectTransform(lib3mf.get_wrapper().GetTranslationTransform(7,8,9))
        changed = unpack(m.QueryWriter('3mf').WriteToBuffer())
        self.assertEqual(changed[CHILD], unpack(data)[CHILD])
        xml = ET.fromstring(changed[MAIN])
        obj = xml.find(f'.//{{{C}}}object')
        self.assertEqual(obj.get('name'), 'Updated assembly')
        self.assertEqual(obj.get('{urn:myvendor:project}flag'), 'keep-me')
        self.assertEqual(obj.find('{urn:myvendor:project}opaque').text, 'Keep even when renamed')
        comp = xml.find(f'.//{{{C}}}component')
        self.assertEqual(comp.get(f'{{{P}}}path'), '/' + CHILD)
        self.assertIsNotNone(comp.get(f'{{{P}}}UUID'))
        self.assertIn(b'requiredextensions="p"', changed[MAIN])
        self.assertIn(b'xmlns:p=', changed[MAIN])
        self.assertEqual(xml.find(f'.//{{{C}}}item').get('{urn:myvendor:project}setting'), '42')

    def test_new_mesh_and_build_item_in_existing_production_package(self):
        m, _ = self.read()
        mesh = m.AddMeshObject()
        mesh.SetGeometry([(0,0,0),(2,0,0),(0,2,0)],[(0,1,2)])
        m.AddBuildItem(mesh)
        changed = m.QueryWriter('3mf').WriteToBuffer()
        xml = ET.fromstring(unpack(changed)[MAIN])
        objects = xml.findall(f'.//{{{C}}}object')
        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[-1].get(f'{{{P}}}UUID') is not None, True)
        items = xml.findall(f'.//{{{C}}}item')
        self.assertEqual(len(items),3)
        self.assertIsNotNone(items[-1].get(f'{{{P}}}UUID'))
        m2 = lib3mf.get_wrapper().CreateModel()
        m2.QueryReader('3mf').ReadFromBuffer(changed)
        self.assertEqual(m2.GetBuildItems().Count(), 3)

    def test_unrelated_xml_opaque_property_preservation(self):
        parts = production_fixture()
        child = parts[CHILD].replace(b'<basematerials id="3">',
                      b'<texture2dgroup id="4" texid="123"/>\n<basematerials id="3">')
        child = child.replace(b'<triangle v1="0"', b'<triangle pid="4" p1="0" p2="0" p3="0" v1="0"')
        parts[CHILD] = child
        m, _ = self.read(parts)
        mesh = next(iter(m.GetMeshObjects()))
        mesh.SetVertex(1,(3,0,0))
        after = unpack(m.QueryWriter('3mf').WriteToBuffer())[CHILD]
        self.assertIn(b'texture2dgroup',after)
        el = ET.fromstring(after).find(f'.//{{{C}}}triangle')
        self.assertEqual(el.get('pid'),'4')
        self.assertEqual(el.get('p1'),'0')

    def test_extra_per_triangle_data_blocks_topology_change(self):
        m, _ = self.read(production_fixture(extra_triangle_attr=True))
        mesh = next(iter(m.GetMeshObjects()))
        mesh.AddTriangle((2,1,0))
        with self.assertRaises(lib3mf.Unsupported3MFError):
            m.QueryWriter('3mf').WriteToBuffer()

    def test_unlinked_reference_rejected(self):
        parts = production_fixture()
        del parts['3D/_rels/main.model.rels']
        with self.assertRaisesRegex(lib3mf.ELib3MFException,'not linked'):
            self.read(parts)

    def test_invalid_child_reference_rejected(self):
        with self.assertRaisesRegex(lib3mf.ELib3MFException,'child components'):
            self.read(production_fixture(invalid_child=True))

    def test_bad_production_path_rejected(self):
        parts = production_fixture()
        parts[MAIN] = parts[MAIN].replace(('/'+CHILD).encode(), b'/3D/../secret.model')
        with self.assertRaises(lib3mf.ELib3MFException): self.read(parts)

    def test_editing_signed_package_rejected(self):
        parts = production_fixture()
        parts['_xmlsignatures/sig1.xml'] = b'<Signature/>'
        m, original = self.read(parts)
        self.assertEqual(m.QueryWriter('3mf').WriteToBuffer(), original)
        next(iter(m.GetMeshObjects())).SetVertex(1, (3,0,0))
        with self.assertRaisesRegex(lib3mf.Unsupported3MFError,'signatures'):
            m.QueryWriter('3mf').WriteToBuffer()


if __name__ == '__main__': unittest.main()

class PreservationExtraTests(unittest.TestCase):
    def test_relative_child_relationship(self):
        parts = production_fixture()
        parts['3D/_rels/main.model.rels'] = parts['3D/_rels/main.model.rels'].replace(
            b'Target="/3D/Objects/mesh.model"', b'Target="Objects/mesh.model"')
        loaded = lib3mf.get_wrapper().CreateModel()
        data = archive(parts)
        loaded.QueryReader('3mf').ReadFromBuffer(data)
        self.assertEqual(loaded.QueryWriter('3mf').WriteToBuffer(), data)

    def test_new_target_precedes_existing_assembly(self):
        model = lib3mf.get_wrapper().CreateModel()
        model.QueryReader('3mf').ReadFromBuffer(archive(production_fixture()))
        assembly = next(x for x in model.GetComponentsObjects() if x.GetName() == 'Assembly')
        mesh = model.AddMeshObject()
        mesh.SetGeometry([(0,0,0),(1,0,0),(0,1,0)],[(0,1,2)])
        assembly.AddComponent(mesh)
        xml = ET.fromstring(unpack(model.QueryWriter('3mf').WriteToBuffer())[MAIN])
        resources = xml.find(f'{{{C}}}resources')
        items = [e for e in resources if e.tag == f'{{{C}}}object']
        self.assertEqual([e.get('id') for e in items], [str(mesh.GetResourceID()), '1'])
        comps = items[-1].find(f'{{{C}}}components').findall(f'{{{C}}}component')
        self.assertEqual(comps[-1].get('objectid'),str(mesh.GetResourceID()))
        self.assertIsNotNone(comps[-1].get(f'{{{P}}}UUID'))

    def test_retains_comments_and_processing_instructions_when_editing(self):
        parts = production_fixture()
        parts[MAIN] = parts[MAIN].replace(b'<resources>',
                        b'<!-- Keep author note --><?tool custom="yes"?><resources>')
        m = lib3mf.get_wrapper().CreateModel()
        m.QueryReader('3mf').ReadFromBuffer(archive(parts))
        m.SetLanguage('de-DE')
        edited = unpack(m.QueryWriter('3mf').WriteToBuffer())[MAIN]
        self.assertIn(b'Keep author note', edited)
        self.assertIn(b'<?tool custom="yes"?>', edited)

    def test_unknown_resource_id_not_reused(self):
        parts = production_fixture()
        parts[MAIN] = parts[MAIN].replace(b'<resources>',
                    b'<resources><v:opaqueResource id="300"/>')
        m = lib3mf.get_wrapper().CreateModel()
        m.QueryReader('3mf').ReadFromBuffer(archive(parts))
        self.assertGreater(m.AddMeshObject().GetResourceID(), 300)

    def test_optional_get_original_part(self):
        data = archive(production_fixture())
        m = lib3mf.get_wrapper().CreateModel()
        m.QueryReader('3mf').ReadFromBuffer(data)
        self.assertIn('Metadata/slicer-config.json', m.GetOriginalPackagePartNames())
        self.assertEqual(m.GetOriginalPackagePart('/Metadata/slicer-config.json'),
                         b'{"layer_height":0.2}')
