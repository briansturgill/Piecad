"""Create a multi-file, textured 3MF using the Python standard library only."""
import base64
from pathlib import Path
import lib3mf

# Tiny 1x1 RGBA PNG for an entirely self-contained example.
PNG = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLJ0AAAAABJRU5ErkJggg==')


def main():
    wrapper = lib3mf.get_wrapper()
    model = wrapper.CreateModel()
    model.EnableProductionExtension(True)

    image = model.AddAttachment('/3D/Textures/white.png', lib3mf.TEXTURE_REL)
    image.WriteToBuffer(PNG)
    texture = model.AddTexture2DFromAttachment(image)
    uv = model.AddTexture2DGroup(texture)
    for xy in ((0,0),(1,0),(0,1)):
        uv.AddTex2Coord(xy)

    materials = model.AddBaseMaterialGroup()
    materials.AddMaterial('PLA', wrapper.RGBAToColor(255,255,255,255))

    mesh = model.AddMeshObject()
    mesh.SetName('Textured tetrahedron')
    mesh.SetGeometry(
        [(0,0,0),(20,0,0),(0,20,0),(0,0,20)],
        [(0,2,1),(0,1,3),(0,3,2),(1,2,3)])
    mesh.SetTriangleProperties(0, lib3mf.TriangleProperties(uv.GetResourceID(),[0,1,2]))
    for resource in (texture,uv,materials,mesh):
        model.AssignResourceToPart(resource,'/3D/Objects/tetrahedron.model')

    model.AddBuildItem(mesh,wrapper.GetIdentityTransform())
    output=Path(__file__).with_name('example_materials_production.3mf')
    model.QueryWriter('3mf').WriteToFile(output)
    inspection=lib3mf.Check3MFPackage(output.read_bytes())
    print('File:',output.name, 'valid:',inspection.ok)
    assert inspection.ok,inspection.to_dict()


if __name__=='__main__': main()
