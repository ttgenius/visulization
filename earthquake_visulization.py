"""
   A full application for earthquake visualization with Paraview.  This app takes:
   (1) earthquake-data binary files  (2) geo-info tif files  (3) faults-data txt files
   and produces the following files needed for Paraview:
   (1) single file: elevated_terrain.vtp            (2) single file: pushed_boundary_warp_terrain.vtp
   (3) group file: pushed_amplitudeWarpSurface*.vtp (4) group file: pushed_fault_warp_terrain*.vtp

   Author: QuakeCoRE
   Date: 08/02/2017
"""

import glob
from struct import unpack
import numpy as np
import vtk
import os
from osgeo import gdal
from math import *

BIG_ENDIAN_FORMAT = '>fff'
LITTLE_ENDIAN_FORMAT = '<fff'
BINARY_PREFIX_FORMAT = '{}{:04d}'
CONVERTED_FILE_FORMAT = '{}_zvalues_{:04d}.vtp'
FLAT_TERRAIN_NAME = 'flat_terrain.vtp'
ElEVATED_TERRAIN_NAME = 'elevated_terrain.vtp'
BOUNDARY_FILENAME = 'boundary.vtp'
BOUNDARY_W_TERRAIN = 'boundary_warp_terrain.vtp'
AMP_WARP_FORMAT = 'amplitudeWarpSurface_{:04d}.vtp'
FAULT_DATA_FORMAT = 'fault_rapture_data_{:04d}.vtp'
FAULT_WARP_FORMAT = 'fault_warp_terrain_{:04d}.vtp'
ZZ_DIVISION_FACTOR = 25000.    # reduce elevation of the terrain
IN_SEA = -32768.
COUNTER_FACTOR = 10            # reduce resolution of the terrain
SCALAR_DIVISION_FACTOR = 700.  # reduce elevation of moving mountains
FILL_FAULTS_FACTOR = 2  # increase the number of points within the faults surface so that all the elevations can be seen


# ===================================================================================================================
# STEP 1: Convert binary files to vtp for further processing

def file_counter(file_path, extension):
    """return the total number of files
       given a file path and an extension"""

    total = len(glob.glob1(file_path, '*' + extension))

    return total


def extract_xyz(binaryName, endianess):
    """read a binary file, extract x, y, z of every point,
       return a list of points with x, y, z"""

    point_list = []
    bf = open(binaryName, 'rb')

    while bf.tell() < os.fstat(bf.fileno()).st_size:
        line = bf.read(12)  # read 12 bytes of data (skip spaces)

        if endianess == 'little':
            num_format = LITTLE_ENDIAN_FORMAT
        else:
            num_format = BIG_ENDIAN_FORMAT

        lx, ly, lz = unpack(num_format, line)
        point_list.append((lx, ly, lz))

    bf.close()

    return point_list


def create_poly():
    """create 3 arrrays to store data"""
    points = vtk.vtkPoints()
    vertices = vtk.vtkCellArray()
    zvalues = vtk.vtkFloatArray()
    return points, vertices, zvalues


def insert_value(points, vertices, zvalues, x, y, z):
    """pumping up the 3 arrays"""
    id = points.InsertNextPoint(x, y, 0.)
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


def read_points(binaryName, endianess):
    """convert binary points to vtk points"""

    points, vertices, zvalues = create_poly()
    point_list = extract_xyz(binaryName, endianess)

    for p in point_list:
        lx, ly, lz = p
        insert_value(points, vertices, zvalues, lx, ly, lz)

    print("points read")

    return (points, vertices, zvalues)


def convert_binary_to_vtp(binaryNamePrefix, endianess, extension, total):
    """convert binary files to vtp files """

    for i in range(total):
        binaryName = (BINARY_PREFIX_FORMAT + extension).format(binaryNamePrefix, i)
        vtpName = CONVERTED_FILE_FORMAT.format(binaryNamePrefix, i)
        points, vertices, zvalues = read_points(binaryName, endianess)
        polyData = set_poly(points, vertices, zvalues)
        write_poly(polyData, vtpName)
        print(vtpName + " converted")


# ===================================================================================================================
# STEP 2: Merge all tiff files together to form a flat terrain

def sameSide(p1, p2, a, b):
    """check if 2 points are at the same side of line ab"""
    cp1 = np.cross(b - a, p1 - a)
    cp2 = np.cross(b - a, p2 - a)
    return (cp1 * cp2 >= 0)


def insideTriangle(p, a, b, c):
    """check if a point p is inside the triangle abc"""
    return sameSide(p, a, b, c) and sameSide(p, b, a, c) and sameSide(p, c, a, b)


def insideRectangle(p, a, b, c, d):
    """check if a point p is inside the rectangle abcd"""
    return insideTriangle(p, a, b, c) or insideTriangle(p, c, d, a)


def geotiff2vtp(gtifName, crop=None):
    """convert tiff file to vtp file every 10 points"""

    # If crop is desired, provide 4 cordinates of corners
    # v0=np.array([171.322525,-43.174225])
    # v1=np.array([173.012207,-42.958572])
    # v2=np.array([173.283966,-44.013733])
    # v3=np.array([171.565277,-44.233200])
    # then call geotiff2vtp with crop=[v0,v1,v2,v3]

    if crop is not None:
        assert len(crop) == 4
        v0, v1, v2, v3 = crop

    points, vertices, zvalues = create_poly()
    zvalues.SetName('Elevation')

    ds = gdal.Open(gtifName)
    dsA = ds.ReadAsArray()
    gt = ds.GetGeoTransform()

    y_counter = 0
    for y in range(len(dsA)):
        x_counter = 0
        for x in range(len(dsA[y])):
            xx = gt[0] + gt[1] * x      # g[0] is xOrigin, gt[1] is pixelWidth
            yy = gt[3] + gt[5] * y      # g[3] is yOrigin, gt[5] is pixelHeight
            z = dsA[y][x]
            if z == IN_SEA:
                z = -0.1
                zz = -0.001
            else:
                zz = z / ZZ_DIVISION_FACTOR

            # reduce resolution to 1/100, otherwise too much computation
            if y_counter % COUNTER_FACTOR == 0 and x_counter % COUNTER_FACTOR == 0:

                if crop is None or (v0[0] <= xx <= v2[0] and v3[1] <= yy <= v1[1] and insideRectangle(
                        np.array([xx, yy]), v0, v1, v2, v3)):
                    insert_value(points, vertices, zvalues, xx, yy, zz)
            x_counter += 1
        y_counter += 1

    polyData = set_poly(points, vertices, zvalues)
    return polyData


def append_vtps(tifiles):
    """append vtp files converted from geotiff
       together to show the merged flat terrain"""

    appender = vtk.vtkAppendPolyData()
    gtifs = glob.glob(tifiles)
    for gtifName in gtifs:
        print(gtifName)
        polyData = geotiff2vtp(gtifName, crop=None)
        appender.AddInputData(polyData)
        appender.Update()
    appendData = appender.GetOutput()
    write_poly(appendData, FLAT_TERRAIN_NAME)


# ===================================================================================================================
# STEP 3: Form the boundary of the region extracted from our earthquake data

def find_boundary(point_list):
    """take a point list, return the four boundary points.
       x is the longitude, y is the latitude"""

    sorted_x = sorted(point_list)
    sorted_y = sorted(point_list, key=lambda x: x[1])

    x_min = (sorted_x[0])
    x_max = (sorted_x[-1])
    y_min = (sorted_y[0])
    y_max = (sorted_y[-1])

    print(x_min, x_max, y_min, y_max)
    return x_min, x_max, y_min, y_max


def approx_drawing_distance(a, b):
    """calc distance between point a and b"""
    dis = sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)
    return dis


def calc_points(start, end, number_of_points):
    """Take start and end points of a line, write the start point up to but
       not include the end point as polydata according to number_of_points"""

    gaps = number_of_points - 1
    if gaps == 0 or gaps == -1:
        gaps = 3
    print("number of gaps", gaps)

    lon_gap = abs(float(start[0] - end[0]) / gaps)
    lat_gap = abs(float(start[1] - end[1]) / gaps)

    if start[1] > end[1]:  # to ensure the direction of a line is correct
        lat_gap = -lat_gap
    if start[0] > end[0]:
        lon_gap = -lon_gap
    print("long gap", lon_gap, "lat gap", lat_gap)

    appender = vtk.vtkAppendPolyData()
    points, vertices, zvalues = create_poly()

    i = 0
    while i < (number_of_points - 1):
        x, y = start
        insert_value(points, vertices, zvalues, x, y, 0.)
        start = (start[0] + lon_gap, start[1] + lat_gap)
        i += 1
    poly_data = set_poly(points, vertices, zvalues)
    appender.AddInputData(poly_data)
    appender.Update()
    appender_data = appender.GetOutput()

    return appender_data


def form_boundary(point_list, number_of_points, out_name=None):
    """take a point list, return points along the boundaries as polydata"""

    x_min, x_max, y_min, y_max = find_boundary(point_list)
    print("four cornoer is", x_min, x_max, y_min, y_max)

    # approximate distance between connected boundary points.
    # For accuracy you may want to use https://en.wikipedia.org/wiki/Geographical_distance
    dis_xmin_ymax = approx_drawing_distance(x_min[:2], y_max[:2])
    dis_xmax_ymax = approx_drawing_distance(y_max[:2], x_max[:2])
    dis_xmax_ymin = approx_drawing_distance(x_max[:2], y_min[:2])
    dis_ymin_xmin = approx_drawing_distance(y_min[:2], x_min[:2])

    print(dis_xmin_ymax, dis_xmax_ymax, dis_xmax_ymin, dis_ymin_xmin)

    factor_1 = float(dis_xmax_ymax / dis_xmin_ymax)
    factor_2 = float(dis_xmax_ymin / dis_xmin_ymax)
    factor_3 = float(dis_ymin_xmin / dis_xmin_ymax)

    n1 = round(number_of_points * factor_1)
    n2 = round(number_of_points * factor_2)
    n3 = round(number_of_points * factor_3)

    appender = vtk.vtkAppendPolyData()
    poly_data1 = calc_points(x_min[:2], y_max[:2], number_of_points)
    print(number_of_points)
    appender.AddInputData(poly_data1)
    appender.Update()

    poly_data2 = calc_points(y_max[:2], x_max[:2], n1)
    appender.AddInputData(poly_data2)
    appender.Update()

    poly_data3 = calc_points(x_max[:2], y_min[:2], n2)
    appender.AddInputData(poly_data3)
    appender.Update()

    poly_data4 = calc_points(y_min[:2], x_min[:2], n3)
    appender.AddInputData(poly_data4)
    appender.Update()

    appender_data = appender.GetOutput()
    if out_name is not None:
        write_poly(appender_data, out_name)

    return poly_data1, poly_data2, poly_data3, poly_data4, appender_data  # to compute filled faults


# ===================================================================================================================
# STEP 4: Form the faults that raptures during the earthquake

def form_planes(fault_data_txt, number_of_points):
    """Read a fault-data txt, extract planes/faults'boundarie points,
       Then fill the planes/faults with points and write out as vtp files"""

    with open(fault_data_txt, 'r') as f:
        plane_info = f.readlines()[2:]  # skip the first two line as info are about the hypercentre
        i = 0         # trace line
        count = 0     # trace plane
        while i <= len(plane_info):
            if i % 5 != 0:
                lon, lat = plane_info[i].split()
                lon = float(lon)
                lat = float(lat)
                point = (lon, lat)
                print("xyis", lon, lat)
                plane_boundary.append(point)

            elif i == 0:
                plane_boundary = []

            else:
                appender = vtk.vtkAppendPolyData()
                poly_data1, poly_data2, poly_data3, poly_data4, whole_data = form_boundary(plane_boundary,
                                                                                           number_of_points)
                print("write rect boundary")
                # add boundary lines first.
                # Alternatively you could add the four boundary points to avoid repeated insertion of start points in the loop below.
                appender.AddInputData(whole_data)
                appender.Update()

                points1 = poly_data1.GetPoints()
                points2 = poly_data2.GetPoints()
                points3 = poly_data3.GetPoints()
                points4 = poly_data4.GetPoints()

                total1 = points1.GetNumberOfPoints()
                total2 = points2.GetNumberOfPoints()
                total3 = points3.GetNumberOfPoints()
                total4 = points4.GetNumberOfPoints()

                # fill a rectangle by computing lines between opposite points on the boundary
                for j in range(1, int(min(total1, total3))):
                    print("total 1", total1, "total 3", total3)
                    start = points1.GetPoint(j)
                    print("line 1 pos ", j)
                    print("sssssssstart", start)
                    end = points3.GetPoint(int(min(total1, total3) - j))
                    print("line 3 pos  ", (int(min(total1, total3) - j)))
                    print("eeeeeeeeeend", end)
                    lines_num = min(total2, total4)
                    if lines_num == 0:
                        print("lines_num == 0000000000000000000000000000000000000000000000")
                        lines_num = 4
                    line = calc_points(start[:2], end[:2], FILL_FAULTS_FACTOR * lines_num)
                    print("rectangle", count, "plot line from ", start, "to ", end, "number of points is", (FILL_FAULTS_FACTOR * lines_num))
                    appender.AddInputData(line)
                    appender.Update()

                plane_boundary = []
                appender_data = appender.GetOutput()
                write_poly(appender_data, FAULT_DATA_FORMAT.format(count))
                count += 1
            i += 1
            print("count is", count - 1)


# ===================================================================================================================
# STEP 5: create elevated surfaces

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


def create_elevation_surfaces(binaryNamePrefix, total, faults_sum):
    """create 4 types of elevation surfaces:
       1. an elevation surface of the terrain for applying texture;
       2. an elevation surface of terrain-warped boundary;
       3. 12 elevation surfaces of terrain-warped faults
       4. an elevation surface of terrain-warped amplitude."""

    # elevates terrain
    elevationPolyData = read_poly_data(FLAT_TERRAIN_NAME)
    elevationDelaunay = create_delaunay(elevationPolyData)
    elevation_scalar = create_warp_scalar(elevationDelaunay)
    warp_delaunay_writer(elevation_scalar, ElEVATED_TERRAIN_NAME)

    # warp terrain and boundary
    boundaryPolyData = read_poly_data(BOUNDARY_FILENAME)
    boundary_probe_filter = create_probe_filter(elevationDelaunay, boundaryPolyData)
    boundary_warp_terrain_scalar = create_warp_scalar(boundary_probe_filter)
    boundary_warp_terrain_dealuny = set_scalar_data(boundary_warp_terrain_scalar, boundaryPolyData)
    warp_delaunay_writer(boundary_warp_terrain_dealuny, BOUNDARY_W_TERRAIN)

    # warp terrain and fault
    for j in range(faults_sum):
        faultPolyData = read_poly_data(FAULT_DATA_FORMAT.format(j))
        fault_probe_filter = create_probe_filter(elevationDelaunay, faultPolyData)
        fault_warp_terrain_scalar = create_warp_scalar(fault_probe_filter)
        fault_warp_terrain_dealuny = set_scalar_data(fault_warp_terrain_scalar, faultPolyData)
        warp_delaunay_writer(fault_warp_terrain_dealuny, FAULT_WARP_FORMAT.format(j))
        print("wrote " + FAULT_WARP_FORMAT.format(j))

    # warp terrain and amplitude
    for i in range(total):
        filename = CONVERTED_FILE_FORMAT.format(binaryNamePrefix, i)
        print("Processing {} now".format(filename))
        amplitudePolyData = read_poly_data(filename)
        amp_probe_filter = create_probe_filter(elevationDelaunay, amplitudePolyData)
        amp_warp_scalar = create_warp_scalar(amp_probe_filter)
        amplitudeWarpDelaunay = set_scalar_data(amp_warp_scalar, amplitudePolyData)
        out_name = AMP_WARP_FORMAT.format(i)
        warp_delaunay_writer(amplitudeWarpDelaunay, out_name)


# ===================================================================================================================
# STEP 6: push surfaces in z-direction

def push_warp_surface_up(push_value, total, in_format, scalar_shown=False):
    """push the warp_surface z-ed wise up by some value so that we can see it in a more-3D pespective"""

    for j in range(total):
        poly_data = read_poly_data(in_format.format(j))
        points = poly_data.GetPoints()
        print("read " + in_format.format(j))

        for i in range(points.GetNumberOfPoints()):
            x, y, z = points.GetPoint(i)
            z += push_value
            if scalar_shown:
                scalar_value = poly_data.GetPointData().GetScalars().GetValue(i)
                z += scalar_value / SCALAR_DIVISION_FACTOR
            points.SetPoint(i, x, y, z)
        pushed_vtp_file = ('pushed_' + in_format).format(j)
        write_poly(poly_data, pushed_vtp_file)
        print("wrote " + in_format.format(j))
    print("end pushing")


def push_surfaces(faults_push_value, amp_total, faults_sum, scalar_shown):
    """push 3 types of surfaces up"""

    # push boundary_warp_terrain
    push_warp_surface_up(faults_push_value + 0.015, 1, BOUNDARY_W_TERRAIN)

    # pushe amplitude_warp_surface
    push_warp_surface_up(faults_push_value + 0.01, amp_total, AMP_WARP_FORMAT, scalar_shown)

    # push fault_warp_terrain
    push_warp_surface_up(faults_push_value, faults_sum, FAULT_WARP_FORMAT)


# ===================================================================================================================

def main():
    # change these hard codes when applying different data.
    # Make sure all data files and this py are in the same directory.

    # start of hard codes
    # path leading to the directory containing the raw binary files you want to process
    file_path = '/home/yzh231/New_Kaikoura_earthquake'

    # extension of the raw binary files
    extension = '.0'

    # binary prefix of the raw binary files
    binaryNamePrefix = '2016Nov13_Ian02_s103245_VMCant_Amberly_200m-h0p200_EMODv3p0p4_161221_ts'

    # endianess of the binary files, type either 'little' or 'big'
    endianess = 'big'

    # tif file pattern of the tif files waiting to be converted and merged.
    tifiles = 'csrt*.tif'

    # fault rapture data filename
    fault_data_file = 'Ian2.txt'
    
    # the value you want to push the faults surface z-ed wise up.
    faults_push_value = 0.01

    # number_of_points displayed on the line xmin_ymax.
    # Any number of points shown on other 3 lines are calculated based on this
    number_of_points = 40

    # want to show the scalar as elevation or not
    scalar_shown = True

    # end of hard codes

    print("hhahahahaahha counting files")
    total = file_counter(file_path, extension)
    print("total is " + str(total))

    # extract points from just one file for forming boundary
    print("hahahaha extracting points")
    point_list = extract_xyz((BINARY_PREFIX_FORMAT + extension).format(binaryNamePrefix, 0), endianess)

    print("hahahahahahah step 1")
    convert_binary_to_vtp(binaryNamePrefix, endianess, extension, total)

    print("hahahahahahah step 2")
    append_vtps(tifiles)

    print("hahahahahahah step 3")
    form_boundary(point_list, number_of_points, BOUNDARY_FILENAME)

    print("hahahahahahah step 4")
    form_planes(fault_data_file, number_of_points)
    faults_sum = file_counter(file_path, 'rapture_data*.vtp')
    print("number of faults is " + str(faults_sum))

    print("hahahahahahah step 5")
    create_elevation_surfaces(binaryNamePrefix, total, faults_sum)

    print("hahahahahahah step 6")
    push_surfaces(faults_push_value, total, faults_sum, scalar_shown)

    print("all done")

    # for renaming. Eg:
    # for filename in os.listdir("."):
        # if filename.startswith("pushed_filled"):
            # os.rename(filename, filename[:7]+'fault'+filename[23:])


if __name__ == '__main__':
    main()

