from osgeo import gdal,ogr,osr
from struct import unpack
from array import array
import os
import numpy as np
from vtk import *
import glob
from road_txt_reader import *


def sameSide(p1,p2, a,b):
    cp1 = np.cross(b-a, p1-a)
    cp2 = np.cross(b-a, p2-a)
    return (cp1*cp2 >= 0)
def insideTriangle(p,a,b,c):
    return sameSide(p,a,b,c) and sameSide(p,b,a,c) and sameSide(p,c,a,b)

def insideRectangle(p, a,b,c,d):
    return insideTriangle(p,a,b,c) or insideTriangle(p,c,d,a)

		
#ds = gdal.Open('Z_71_21.TIF')


def geotiff2vtp(gtifName,crop=None):
    #If crop is desired, provide 4 cordinates of corners
    #v0=np.array([171.322525,-43.174225])
    #v1=np.array([173.012207,-42.958572])
    #v2=np.array([173.283966,-44.013733])
    #v3=np.array([171.565277,-44.233200])
    #then call geotiff2vtp with crop=[v0,v1,v2,v3]
    if crop is not None:
	assert len(crop) == 4
	v0,v1,v2,v3 = crop 
	
    points = vtkPoints()
    zvalues = vtkFloatArray()
    vertices = vtkCellArray()
    zvalues.SetName('Elevation')
	
    print gtifName
    ds = gdal.Open(gtifName)
    baseName = gtifName.strip('.tif')
	
    dsA=ds.ReadAsArray()
    gt=ds.GetGeoTransform()
    print("gt",gt)
    print("dsA",dsA)
    print("ds",ds)
   
    y_counter = 0
    for y in range(len(dsA)):
	x_counter = 0
	
        for x in range(len(dsA[y])):
            xx =  gt[0]+gt[1]*x
            yy =  gt[3]+gt[5]*y
            z= dsA[y][x]
	
            if z== -32768:
                z=-0.1
                zz=-0.001
            else:
		       zz = z * 10
		#print("z",z)#32000. is a bit too flat
	    if y_counter % 10 == 0 and x_counter % 10 == 0:
		if crop is None or (xx>=v0[0] and xx<=v2[0] and yy>= v3[1] and yy<= v1[1] and insideRectangle(np.array([xx,yy]), v0,v1,v2,v3)):
		    id = points.InsertNextPoint(xx,yy,0.)
		    vertex = vtkVertex()
		    vertex.GetPointIds().InsertNextId(id)
		    vertices.InsertNextCell(vertex)
		    zvalues.InsertNextValue(zz)
	    x_counter += 1
	y_counter += 1
    
    print("original x is ", x_counter)
    print("original y is ", y_counter)

    polyData = vtkPolyData()
    polyData.SetPoints(points)
    polyData.SetVerts(vertices)
    polyData.GetPointData().SetScalars(zvalues)
    return polyData

def create_sea():
    """take four corners of two tif files and create a imaginary sea"""
    points = vtkPoints()
    zvalues = vtkFloatArray()
    vertices = vtkCellArray()
    zvalues.SetName('Elevation')

    ul = [174.9995839, -45.0004164]
    ur = [180.0004173, -45.0004164]
    lr = [180.0004173, -50.0004165]
    ll = [175.0004172, -50.0004165]
    x_gap = max((ur[0]-ul[0]),(lr[0]-ll[0]))/500.
    y_gap = (ul[1]-ll[1])/500.

    for x in range(501):
        for y in range(501):
            id = points.InsertNextPoint(ul[0], ul[1], 0.)
            vertex = vtkVertex()
            vertex.GetPointIds().InsertNextId(id)
            vertices.InsertNextCell(vertex)
            zvalues.InsertNextValue(-0.001)
            ul[1] -= y_gap
        ul[0] += x_gap
        ul[1] = -45.0004164
    print("ul",ul)

    polyData = vtkPolyData()
    polyData.SetPoints(points)
    polyData.SetVerts(vertices)
    polyData.GetPointData().SetScalars(zvalues)
    return polyData

# from osgeo import gdal
# ds = gdal.Open('path/to/file')
# width = ds.RasterXSize
# height = ds.RasterYSize
# gt = ds.GetGeoTransform()
# minx = gt[0]
# miny = gt[3] + width*gt[4] + height*gt[5]
# maxx = gt[0] + width*gt[1] + height*gt[2]
# maxy = gt[3]

def read_poly_data(vtpName):
    """read a vtp file to get poly data for creating warp_surface"""

    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(vtpName)
    reader.Update()
    poly_data = reader.GetOutput()

    return poly_data


def create_delaunay(poly_data):
    """create 2D delunay"""

    print("starting delaunay")
    delaunay = vtk.vtkDelaunay2D()
    print("ending delaunay")
    delaunay.SetInputData(poly_data)
    delaunay.Update()

    return delaunay


def create_probe_filter(source_delaunay, input_poly_data):
    """return a vtk probe filter for amplitude warp scalar.
    Source_delaunay is the data set that will be probed at the input points.
    The Input gives the geometry (the points and cells) for the output,
    while the Source is probed (interpolated) to generate the scalars
    for the output points based on the point locations."""

    probe_filter = vtk.vtkProbeFilter()
    probe_filter.SetSourceConnection(source_delaunay.GetOutputPort())
    probe_filter.SetInputData(input_poly_data)
    probe_filter.Update()

    return probe_filter


def create_warp_scalar(probe_filter):
    """take a probe_filter and generate a warp scalar for warp delaunay"""

    warp_scalar = vtk.vtkWarpScalar()
    warp_scalar.SetInputConnection(probe_filter.GetOutputPort())
    warp_scalar.Update()

    return warp_scalar


def set_scalar_data(input_scalar, poly_data):
    """set the dalaunay as scalar data"""

    warp_delaunay = vtk.vtkDelaunay2D()
    warp_delaunay.SetInputConnection(input_scalar.GetOutputPort())
    warp_delaunay.GetPolyDataInput(0).GetPointData().SetScalars(
        poly_data.GetPointData().GetScalars())  # set the amplitude as scalar data
    warp_delaunay.Update()  # gets elevation color+elevation surface

    return warp_delaunay


def warp_delaunay_writer(warp_delaunay, out_name):
    """write the delaunay to a vtp file.
       Note the difference with the poly writer.
       Here we require a pipline connection"""

    warp_delaunay_writer = vtk.vtkXMLPolyDataWriter()
    warp_delaunay_writer.SetFileName(out_name)
    warp_delaunay_writer.SetInputConnection(warp_delaunay.GetOutputPort())
    warp_delaunay_writer.Write()


# def create_elevation_surfaces(binaryNamePrefix, total, faults_sum):
#     """create 4 types of elevation surfaces:
#        1. an elevation surface of the terrain for applying texture;
#        2. an elevation surface of terrain-warped boundary;
#        3. 12 elevation surfaces of terrain-warped faults
#        4. an elevation surface of terrain-warped amplitude."""
#
#     # elevates terrain
#     elevationPolyData = read_poly_data(FLAT_TERRAIN_NAME)
#     elevationDelaunay = create_delaunay(elevationPolyData)
#     elevation_scalar = create_warp_scalar(elevationDelaunay)
#     warp_delaunay_writer(elevation_scalar, ElEVATED_TERRAIN_NAME)


def main():
    appender = vtk.vtkAppendPolyData()
    appender.AddInputData(create_sea())
    appender.Update()
    polydata = read_poly_data("south_w_north.vtp")
    appender.AddInputData(polydata)
    appender.Update()
    # gtifs = glob.glob('xsrtn*.tif')
    # appender.AddInputData(create_sea())
    # appender.Update()
    # for gtifName in gtifs:
    #     print(gtifName)
    #     polyData = geotiff2vtp(gtifName, crop=None)
    #     appender.AddInputData(polyData)
    #     appender.Update()
    #
    appendData = appender.GetOutput()
    write_poly(appendData, "map_for_road.vtp")
    # polydata = read_poly_data("testsea.vtp")
    # elevationDelaunay = create_delaunay(polydata)
    # elevation_scalar = create_warp_scalar(elevationDelaunay)
    # warp_delaunay_writer(elevation_scalar, "elevated_sea.vtp")

    # polydata2 = read_poly_data("south_w_north.vtp")
    # # appender.AddInputData(polydata)
    # # appender.Update()
    # # appendData = appender.GetOutput()
    # elevationDelaunay = create_delaunay(polydata)
    # elevation_scalar = create_warp_scalar(elevationDelaunay)
    # warp_delaunay_writer(elevation_scalar, "elevated_sea.vtp")

	
    
    
if __name__ == "__main__":
    main()
    #geotiff2vtp("merc5_70_21.tif",crop=None)
    #geotiff2vtp("srtm_70_21.tif",crop=None)
    