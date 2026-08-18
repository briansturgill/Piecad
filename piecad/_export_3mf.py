from piecad import Config
import manifold3d as m
import lib3mf.Lib3MF as lib3mf
from datetime import datetime as dt

def export_3mf(filename, mo, color_map):
    try:
        # Create a new 3MF model
        wrapper = lib3mf.Wrapper()
        model = wrapper.CreateModel()
        units = Config.get_default_units()
        if units == "mm":
            model.SetUnit(lib3mf.ModelUnit.MilliMeter)
        elif units == "cm":
            model.SetUnit(lib3mf.ModelUnit.CentiMeter)
        elif units == "in":
            model.SetUnit(lib3mf.ModelUnit.Inch)



        #title="3MF Model", desc='A 3MF Model created by Piecad.', copyright= None, license = None):
        #mdg = model.GetMetaDataGroup()
        #url = "http://LikeIknow.xyz/what/to/put/here"
        #mdg.AddMetaData(url, 'Title', title, "xs:string", False)
        #mdg.AddMetaData(url,'Designer', 'Piecad', "xs:string", False)
        #mdg.AddMetaData(url, 'Description', desc, "xs:string", False)
        #mdg.AddMetaData(url, 'Copyright', copyright if copyright != None else f'Copyright {dt.now().year}', "xs:string", False)
        #mdg.AddMetaData(url, 'LicenseTerms', license if license != None else 'CC-BY-4.0', "xs:string", False)

        # Create a mesh object
        mesh = model.AddMeshObject()
        mesh.SetName("Mesh")
        m_mesh = mo.to_mesh()

        # Define cube vertices
        if m_mesh.vert_properties.shape[1] > 3:
            vertices = m_mesh.vert_properties[:, :3]
        else:
            vertices = m_mesh.vert_properties
        verts = []
        for v in vertices:
            pos = lib3mf.Position((v[0], v[1], v[2]))
            verts.append(pos)
            mesh.AddVertex(pos)

        # Define cube faces (triangles)
        triangles = m_mesh.tri_verts
        tris = []
        for t in triangles:
            tri = lib3mf.Triangle((t[0], t[1], t[2]))
            tris.append(tri)
            mesh.AddTriangle(tri)

        mesh.SetGeometry(verts, tris) # Why is this necessary?

        # Create a ColorGroup resource
        color_group = model.AddColorGroup()
        tan = color_group.AddColor(lib3mf.Color(210, 180, 140, 255))
        mesh.SetObjectLevelProperty(color_group.GetResourceID(), tan)
        
        for i in range(0, len(m_mesh.run_index) - 1):
            for j in range(m_mesh.run_index[i] // 3, m_mesh.run_index[i + 1] // 3):
                id = m_mesh.run_original_id[i]
                if id == -1 or id not in color_map:
                    color = (210, 180, 140)
                else:
                    color = color_map[id]
                cid = color_group.AddColor(lib3mf.Color(color[0], color[1], color[2], 255))
                mesh.SetTriangleProperties(j, lib3mf.TriangleProperties(color_group.GetResourceID(), (cid, cid, cid)))

        # Add mesh to build
        model.AddBuildItem(mesh, wrapper.GetIdentityTransform())

        # Write to file
        writer = model.QueryWriter("3mf")
        writer.WriteToFile(filename)

    except lib3mf.ELib3MFException as e:
        print(f"Lib3MF Error: {e}")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    mo = m.Manifold.cube((40,40,40))
    mo2 = m.Manifold.cube((40,40,40)).translate((4,4,4))
    mo = mo + mo2
    export_3mf("/home/brian/Downloads/t.3mf", mo, {})
