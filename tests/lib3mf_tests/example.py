"""Example using the pure-Python lib3mf-compatible API; creates example_cube.3mf."""
import lib3mf

wrapper = lib3mf.get_wrapper()
model = wrapper.CreateModel()
model.SetUnit(lib3mf.ModelUnit.MilliMeter)
mesh = model.AddMeshObject()
mesh.SetName('Box')

vertices = [
    (0, 0, 0), (10, 0, 0), (10, 20, 0), (0, 20, 0),
    (0, 0, 30), (10, 0, 30), (10, 20, 30), (0, 20, 30),
]
triangles = [
    (2, 1, 0), (0, 3, 2), (4, 5, 6), (6, 7, 4),
    (0, 1, 5), (5, 4, 0), (2, 3, 7), (7, 6, 2),
    (1, 2, 6), (6, 5, 1), (3, 0, 4), (4, 7, 3),
]
# Plain Python lists of native numbers are accepted. No numpy or native library.
mesh.SetGeometry(vertices, triangles)
assert mesh.IsManifoldAndOriented()

colors = model.AddBaseMaterialGroup()
red = colors.AddMaterial('Red', wrapper.RGBAToColor(255, 50, 50, 255))
mesh.SetObjectLevelProperty(colors.GetResourceID(), red)

model.AddBuildItem(mesh, wrapper.GetIdentityTransform())
model.GetMetaDataGroup().AddMetaData('', 'Application', 'pure_lib3mf')
model.QueryWriter('3mf').WriteToFile('example_cube.3mf')

read_back = wrapper.CreateModel()
read_back.QueryReader('3mf').ReadFromFile('example_cube.3mf')
for item in read_back.GetBuildItems():
    obj = item.GetObjectResource()
    print(obj.GetName(), 'vertices=', obj.GetVertexCount(),
          'triangles=', obj.GetTriangleCount())
