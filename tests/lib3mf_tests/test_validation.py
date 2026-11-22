"""Printability and package structural validation, pure Python."""
import io
import unittest
import zipfile
import lib3mf
from test_materials_production import build_complete_model

TETRA_VERTICES=[(0,0,0),(1,0,0),(0,1,0),(0,0,1)]
TETRA_FACES=[(0,2,1),(0,1,3),(0,3,2),(1,2,3)]

def make_mesh(vertices, faces):
    m=lib3mf.get_wrapper().CreateModel()
    mesh=m.AddMeshObject(); mesh.SetGeometry(vertices,faces);m.AddBuildItem(mesh)
    return m,mesh

class GeometryValidationTests(unittest.TestCase):
    def test_positive_tetra_and_negative_tetra(self):
        m,mesh=make_mesh(TETRA_VERTICES,TETRA_FACES)
        rep=mesh.ValidateGeometry(check_self_intersections=True)
        self.assertTrue(rep.ok,rep.to_dict())
        self.assertAlmostEqual(rep.signed_volume,1/6)
        for k in range(len(TETRA_FACES)):
            a,b,c=TETRA_FACES[k]
            mesh.SetTriangle(k,(c,b,a))
        rep=mesh.ValidateGeometry()
        self.assertFalse(rep.ok)
        self.assertEqual(len(rep.by_code('negative_volume')),1)
        writer=m.QueryWriter('3mf');writer.SetStrictModeActive(True)
        with self.assertRaises(lib3mf.ELib3MFException): writer.WriteToBuffer()

    def test_zero_area_by_coincident_coordinates(self):
        _,mesh=make_mesh([(0,0,0),(1,0,0),(2,0,0)],[(0,1,2)])
        self.assertTrue(mesh.ValidateGeometry().by_code('zero_area'))

    def test_duplicate_geometry_even_with_distinct_ids(self):
        _,mesh=make_mesh([(0,0,0),(1,0,0),(0,1,0),(0,0,0),(1,0,0),(0,1,0)],
                         [(0,1,2),(3,4,5)])
        self.assertTrue(mesh.ValidateGeometry().by_code('duplicate_triangle'))

    def test_touching_tetrahedra_nonmanifold_vertex(self):
        second=[(1+x,1+y,1+z) for x,y,z in TETRA_VERTICES[1:]]
        vertices=TETRA_VERTICES+second
        faces=TETRA_FACES+[tuple(0 if i==0 else i+3 for i in face) for face in TETRA_FACES]
        _,mesh=make_mesh(vertices,faces)
        self.assertTrue(mesh.ValidateGeometry().by_code('nonmanifold_vertex'))

    def test_intersection_of_two_disjoint_triangles(self):
        vertices=[(-1,-1,0),(1,-1,0),(0,1,0),
                  (0,0,-1),(0,0,1),(0,2,0)]
        _,mesh=make_mesh(vertices,[(0,1,2),(3,4,5)])
        report=mesh.ValidateGeometry(check_self_intersections=True)
        self.assertTrue(report.by_code('self_intersection'),report.to_dict())

    def test_pair_limit_warns_when_skipping(self):
        _,mesh=make_mesh(TETRA_VERTICES,TETRA_FACES)
        report=mesh.ValidateGeometry(check_self_intersections=True,max_pairs=1)
        self.assertTrue(report.by_code('intersection_check_skipped'))

    def test_archive_check_valid_and_bad_relationship(self):
        m=build_complete_model()
        good=m.QueryWriter('3mf').WriteToBuffer()
        report=lib3mf.Check3MFPackage(good)
        self.assertTrue(report.ok,report.to_dict())
        parts={}
        with zipfile.ZipFile(io.BytesIO(good)) as z:
            parts={name:z.read(name) for name in z.namelist()}
        del parts['3D/Objects/textured.model']
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            for k,v in parts.items():z.writestr(k,v)
        report=lib3mf.Check3MFPackage(out.getvalue())
        self.assertFalse(report.ok)
        self.assertTrue(any(i.code=='dangling_relationship' for i in report.issues))

    def test_optional_selfintersections_is_bounded(self):
        m,mesh=make_mesh(TETRA_VERTICES,TETRA_FACES)
        self.assertTrue(lib3mf.Check3MFPackage(m.QueryWriter('3mf').WriteToBuffer()).ok)

if __name__=='__main__':unittest.main()
