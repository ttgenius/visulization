"""Draw airlines in Paraview"""
from math import *
from pylab import *
import vtk


def create_poly():
    """create 3 arrrays to store data"""
    points = vtk.vtkPoints()
    vertices = vtk.vtkCellArray()
    zvalues = vtk.vtkFloatArray()
    return (points, vertices, zvalues)


def insert_value(points, vertices, zvalues, x, y, z):
    """pumping up the 3 arrays"""
    id = points.InsertNextPoint(x, y, z)
    vertex = vtk.vtkVertex()
    vertex.GetPointIds().InsertNextId(id)
    vertices.InsertNextCell(vertex)
    zvalues.InsertNextValue(z)


def set_poly(points, vertices, zvalues):
    """set 3 arrays"""
    polyData = vtk.vtkPolyData()
    polyData.SetPoints(points)
    polyData.SetVerts(vertices)
    polyData.GetPointData().SetScalars(zvalues)
    return polyData


def write_poly(polyData, vtpName):
    """write polyData to a vtp file"""
    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(vtpName)
    writer.SetInputData(polyData)
    writer.Write()


def read_poly_data(vtpName):
    """read a vtp file to get poly data for creating warp_surface"""

    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(vtpName)
    reader.Update()
    poly_data = reader.GetOutput()

    return poly_data


def draw_arc(startlon, startlat, endlon, endlat, n, upper,outname):
    """take the longitude and latitude of two end points, drawn a dotted arc between the two points;
       n is the number of points along the arc;
       upper=True/False decides whether the upper or lower half of the ellipse will be drawn as the arc;
       outname is the route name of the output vtp file"""

    n = float(n)
    u = sqrt((endlon-startlon)**2 + (endlat-startlat)**2)/2    #distance between 2 end points (2a of an ellipse)
    #print("uuuuuuuuuuuuuuu",u)
    v = u/2.5 #2b of an ellipse
    dt = u/n
    theta = atan((endlat-startlat)/(endlon-startlon))  #angle between x-axis and line u
    center_x = (endlon + startlon) / 2.
    center_y = (endlat + startlat) / 2.
    #print("center_x,center_y", center_x, center_y)
    pts = []
    X=[]  #to visualize the points in python
    Y=[]
    points, vertices, zvalues = create_poly()
    insert_value(points, vertices, zvalues,startlon, startlat, 0.11446)
    for i in range(0,int(n)):
        t = dt * i/u
        if upper == False:
            t = -t
        #print("t",t)
        x = cos(theta) * u * cos(pi*t) - sin(theta)* v *sin(pi*t)   #x is the offset between new_x center_X
        y = sin(theta) * u * cos(pi*t) + cos(theta)* v *sin(pi*t)
        #print("x,y", x, y)
        new_lon = center_x + x
        new_lat = center_y + y
        pts.append((new_lon,new_lat))
        X.append(new_lon)
        Y.append(new_lat)
        #print("appended",(new_lon,new_lat))
        insert_value(points, vertices, zvalues, new_lon, new_lat, 0.11446)
    insert_value(points, vertices, zvalues, endlon, endlat, 0.11446)
    poly_data = set_poly(points, vertices, zvalues)
    write_poly(poly_data, "airlines/{}.vtp".format(outname))
    plot(X, Y)
    scatter(X, Y)
    scatter([center_x], [center_y], color='r', s=100)
    axis('equal')
    show()


# =======uncomment to draw airlines=====================================================================================
# draw_arc(172.639847,-43.525650,174.776217, -41.28648,70,False,"air_chch_welly2")
# draw_arc(172.639847,-43.525650,173.9528,-41.51603,50,True,"air_chch_blenheim")
# draw_arc(174.776217, -41.28648,173.9528,-41.51603,20,False,"air_welly_blenheim")
draw_arc(174.776217, -41.28648,174.045,-41.28472,20,True,"air_welly_picton")
# draw_arc(172.639847,-43.525650,173.70222,-42.42500,20,False,"air_chch_kaikoura")
#draw_arc(174.0528,-41.51603, 173.70222, -42.36500, 20, False, "air_blenheim_kaikoura")
#draw_arc(174.776217, -41.28648, 173.70222,-42.36500, 20, False,"air_welly_kaikoura")
