import vtk
import glob
import os
from functionsbyViktor import *

LEFT = 169.9995838
RIGHT = 175.0004172
TOP = -39.9995831
BOTTOM = -45.0004164

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



def read_z_road_gmt(gmt_file):
    """take a normal gmt file, read into different vtp files according to different los values"""

    input_file = open('road_data_files/{}'.format(gmt_file),'r')
    flag=False
    points, vertices, zvalues = create_poly()
    i = 0
    lines = input_file.read()
    #print(len(lines.splitlines()))
    splitted_lines = lines.splitlines()
    for line in splitted_lines:
        i+=1
        #print("llllllllllllllllllllllllllllllllllllllllllllllllllll",line,i)
        if line.startswith("#"):
            if line.startswith("# @D"):   #if a new route
                print("current line is {}".format(line))
                if flag:
                    poly_data=set_poly(points,vertices,zvalues)
                    filename = "road_vtp_files/{}_{}_road.vtp".format(gmt_file[:-4],z)
                    if os.path.isfile(filename):
                        appender = vtk.vtkAppendPolyData()
                        previous = read_poly_data(filename)
                        appender.AddInputData(previous)
                        appender.Update()
                        appender.AddInputData(poly_data)
                        appender.Update()
                        poly_data = appender.GetOutput()
                    write_poly(poly_data,filename)
                    points, vertices, zvalues = create_poly()
                line=line.split("|")
                # if line[1]=="":
                #     filename=" ".join(line[3:])
                # else:
                #     filename=line[1]
                z=float(line[2])
                print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",z)
                flag=True
                #print("flag is true")

        elif line.startswith(">"):   #still the same route
            continue

        else:
            x,y=line.split(" ")
            insert_value(points,vertices,zvalues,float(x),float(y),(z+0.1445)/10)  #otherwise the route would appear much above the terrain
            if i == len(splitted_lines):
                poly_data = set_poly(points, vertices, zvalues)
                filename = "road_vtp_files/{}_{}_road.vtp".format(gmt_file[:-4], z)
                if os.path.isfile(filename):
                    appender = vtk.vtkAppendPolyData()
                    previous = read_poly_data(filename)
                    appender.AddInputData(previous)
                    appender.Update()
                    appender.AddInputData(poly_data)
                    appender.Update()
                    poly_data = appender.GetOutput()
                print("end of file,filename is {}".format(filename))
                write_poly(poly_data, filename)


def dense_road_gmt_v2(gmt_file):
    """take an orginal normal road txt gmt file, read into a txt gmt files with denser road"""

    input_file = open('road_data_files/{}'.format(gmt_file),'r')
    flag=False
    # points, vertices, zvalues = create_poly()
    i = 0
    pts=[]
    lines = input_file.read()
    #print(len(lines.splitlines()))
    splitted_lines = lines.splitlines()
    for line in splitted_lines:
        i+=1
        #print("llllllllllllllllllllllllllllllllllllllllllllllllllll",line,i)
        if line.startswith("#"):
            if line.startswith("# @D"):   #if a new route
                #header += 1
                #print("current line is {}".format(line))
                if flag:
                    #poly_data=set_poly(points,vertices,zvalues)
                    path_from_corners(corners=pts,output="road_txt_files/{}_{:.2f}.txt".format(gmt_file,float(z)),min_edge_points=400,close=False)
                    #print("filename",filename)
                    #filename = "road_densed_files/{}_{}_{}.txt".format(gmt_file, i, filename)
                    #print("filename is {}".format(filename))
                    #write_poly(poly_data,filename)
                    # points, vertices, zvalues = create_poly()
                line=line.split("|")
                # if line[1]=="":
                #      filename=" ".join(line[3:])
                # else:
                #      filename=line[1]
                z=line[2]
                print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",z)
                flag=True
                pts = []
                #print("flag is true")

        elif line.startswith(">"):   #still the same route
            continue

        else:
            x,y=line.split(" ")
            x = float(x)
            y = float(y)

            pts.append((x,y))
            #insert_value(points,vertices,zvalues,float(x),float(y),(z+0.1445)/10)  #otherwise the route would appear much above the terrain
            if i == len(splitted_lines):
                path_from_corners(corners=pts, output="road_txt_files/{}_{:.2f}.txt".format(gmt_file,float(z)).format(gmt_file,z),min_edge_points=400, close=False)
                #poly_data = set_poly(points, vertices, zvalues)
                #filename = "road_densed_files/{}_{}_{}.txt".format(gmt_file,i, filename)
                print("end of file,filename",z)
                #write_poly(poly_data, filename


def read_densed_points(gmt_file):
    """take a gmt txt file with densed point,
        output it in vtp format.
    """
    for txtfile in glob.glob1('road_txt_files/', "{}*.txt".format(gmt_file[:-4])):
        print(txtfile)
        file = open('road_txt_files/{}'.format(txtfile), 'r')
        lines = file.read().splitlines()
        points, vertices, zvalues = create_poly()
        z = float(txtfile[-8:-4])
        for line in lines:
            x, y = line.split(" ")
            x = float(x)
            y = float(y)
             if x >= LEFT and x <= RIGHT and y <= TOP and y > BOTTOM:
                insert_value(points, vertices, zvalues, x, y, (z + 0.1445) / 10)
        poly_data = set_poly(points, vertices, zvalues)
        write_poly(poly_data, "road_vtp_files/{}.vtp".format(txtfile[:-4]))


def read_ferry_gmt(gmt_file):
    """take a ferry gmt file, read into different vtp files according to different routes
       arapawa island harbour: -41.21068840, 174.31732178"""
    input_file = open('ferry_data_files/{}'.format(gmt_file),'r')
    flag=False
    points, vertices, zvalues = create_poly()
    i = 0
    similar_count = 0
    head_count = 0
    lines = input_file.read()
    #print(len(lines.splitlines()))
    splitted_lines = lines.splitlines()
    for line in splitted_lines:
        i+=1
        #print("llllllllllllllllllllllllllllllllllllllllllllllllllll",line,i)
        if line.startswith("#"):
            if line.startswith("# @D"):   #if a new route
                head_count += 1
                print("current line is {}".format(line))
                if flag:
                    poly_data=set_poly(points,vertices,zvalues)
                    filename = "ferry_vtp_files/{}_{}_{}.vtp".format(gmt_file, i, filename)
                    print("filename is {}".format(filename))
                    write_poly(poly_data,filename)
                    points, vertices, zvalues = create_poly()
                line=line.split("|")
                filename=line[0]+str(i)
                z=float(line[-1])
                print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",z)
                flag=True
                #print("flag is true")

        elif line.startswith(">"):   #still the same route
            continue

        else:
            x,y=line.split(" ")
            x= float(x)
            y=float(y)
            if x >=174.31732178 and y<=-41.21068840 and head_count != 2: #decrease density of points in the first route after Arapawa island harbour
                similar_count += 1
                if similar_count % 50 == 0:
                    insert_value(points, vertices, zvalues, x, y, (z + 0.1445) / 10)
            else:
                insert_value(points,vertices,zvalues, x, y,(z+0.1445)/10)  #otherwise the route would appear much above the terrain
            if i == len(splitted_lines):
                poly_data = set_poly(points, vertices, zvalues)
                filename = "ferry_vtp_files/{}_{}_{}_ferry.vtp".format(gmt_file,i, filename)
                print("end of file,filename is {}".format(filename))
                write_poly(poly_data, filename)


def read_rail_gmt(gmt_file):
    """take a rail gmt file, read into different vtp files according to different z"""

    input_file = open('rail_data_files/{}'.format(gmt_file), 'r')
    flag = False
    points, vertices, zvalues = create_poly()
    i = 0
    lines = input_file.read()
    # print(len(lines.splitlines()))
    splitted_lines = lines.splitlines()
    for line in splitted_lines:
        i += 1
        # print("llllllllllllllllllllllllllllllllllllllllllllllllllll",line,i)
        if line.startswith("#"):
            if line.startswith("# @D"):  # if a new route
                print("current line is {}".format(line))
                if flag:
                    poly_data = set_poly(points, vertices, zvalues)
                    filename = "rail_vtp_files/{}_{}_rail.vtp".format(gmt_file[:-4], z)
                    if os.path.isfile(filename):
                        print("file exits")
                        appender = vtk.vtkAppendPolyData()
                        previous = read_poly_data(filename)
                        appender.AddInputData(previous)
                        appender.Update()
                        appender.AddInputData(poly_data)
                        appender.Update()
                        poly_data = appender.GetOutput()
                    #print("filename is {}".format(filename))
                    write_poly(poly_data, filename)
                    points, vertices, zvalues = create_poly()
                line = line.split("|")
                # if line[1] == "":
                #     filename = " ".join(line[:-1])
                # else:
                #     filename = line[1]
                z = float(line[-1])
                print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz", z)
                flag = True
                # print("flag is true")

        elif line.startswith(">"):  # still the same route
            continue

        else:
            x, y = line.split(" ")
            x = float(x)
            y = float(y)
            if x >= LEFT and x <= RIGHT and y <= TOP and y > BOTTOM:
                print("zzz",z)
                if float(z)!=1.0:
                    x +=0.1
                insert_value(points, vertices, zvalues, x, y,(z + 0.1445) / 10)  # otherwise the route would appear much above the terrain

            if i == len(splitted_lines):
                poly_data = set_poly(points, vertices, zvalues)
                filename = "rail_vtp_files/{}_{}_rail.vtp".format(gmt_file[:-4], z)
                if os.path.isfile(filename):
                    appender = vtk.vtkAppendPolyData()
                    previous = read_poly_data(filename)
                    appender.AddInputData(previous)
                    appender.Update()
                    appender.AddInputData(poly_data)
                    appender.Update()
                    poly_data = appender.GetOutput()
                print("end of file,filename is {}".format(filename))

                write_poly(poly_data, filename)



#===================previous tries=====================================================================================
#==================read a gmt file into a whole vtp file===============================================================
def read_road_gmt_whole(gmt_file):
    """take a gmt file, read into a whole vtp file regardless of different routes"""

    input = open('road_data_files/{}'.format(gmt_file),'r')
    lines = input.read().splitlines()
    points, vertices, zvalues = create_poly()
    #print(lines)
    i = 0
    #count = 0
    pointss = []
    point_count = 0
    while i < len(lines):
        if lines[i].startswith("# @D"): #read header
            #count +=1
            #print("current line is",lines[i])
            line = lines[i].split('|')
            # if line[1]== '':
            #     rd = line[0]
            # else:
            #     rd = line[1:5]
            #print("rd             ",rd)
            #z =float(line[-2])
            i+=1
            x,y = (lines[i].split(' '))
            x = float(x)
            y = float(y)
            if x >= LEFT and x <= RIGHT and y<=TOP and y >= BOTTOM: # crop out the region outside the tif file domain
                pointss.append([x,y])
                point_count +=1
            #print("x is {} y is {}".format(x,y))
                insert_value(points, vertices, zvalues, x, y,(z+0.1445)/10)
            # else:
            #     print("{},{} out of simulation domain".format(x,y))
        i+=1

    # sorted_pts = sorted(pointss)
    # densed_pts = []
    # pts = path_from_corners(corners=sorted_pts, output=None, min_edge_points=10, close=False)
    # print("original points_count", len(sorted_pts))
    # print("len of densed points",len(densed_pts))
    # for p in densed_pts:
        #insert_value(points, vertices, zvalues, p[0], p[1], 0.1)
    poly_data = set_poly(points, vertices, zvalues)
    print("polylllllllllllllllllll")

    out= "road_vtp_files/{}.vtp".format(gmt_file)
    write_poly(poly_data,out)


#==================different_routes gmts============================================================================================
def read_road_gmt(gmt_file):
    """take a normal gmt file, read into different vtp files according to different routes"""

    input_file = open('road_data_files/{}'.format(gmt_file),'r')
    flag=False
    points, vertices, zvalues = create_poly()
    i = 0
    lines = input_file.read()
    pts = {}
    #print(len(lines.splitlines()))
    splitted_lines = lines.splitlines()
    for line in splitted_lines:
        i+=1
        #print("llllllllllllllllllllllllllllllllllllllllllllllllllll",line,i)
        if line.startswith("#"):
            if line.startswith("# @D"):   #if a new route
                print("current line is {}".format(line))
                if flag:
                    poly_data=set_poly(points,vertices,zvalues)
                    filename = "road_vtp_files/{}_{}_{}.vtp".format(gmt_file, i, filename)
                    print("filename is {}".format(filename))
                    write_poly(poly_data,filename)
                    points, vertices, zvalues = create_poly()
                line=line.split("|")
                if line[1]=="":
                    filename=" ".join(line[3:])
                else:
                    filename=line[1]
                z=float(line[2])
                print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",z)
                flag=True
                #print("flag is true")

        elif line.startswith(">"):   #still the same route
            continue

        else:
            x,y=line.split(" ")
            insert_value(points,vertices,zvalues,float(x),float(y),(z+0.1445)/10)  #otherwise the route would appear much above the terrain
            if i == len(splitted_lines):
                poly_data = set_poly(points, vertices, zvalues)
                filename = "road_vtp_files/{}_{}_{}.vtp".format(gmt_file,i, filename)
                print("end of file,filename is {}".format(filename))
                write_poly(poly_data, filename)


def dense_road_gmt(gmt_file):
    """take a normal gmt file, read into different vtp files according to different routes with denser road"""

    input_file = open('road_data_files/{}'.format(gmt_file),'r')
    flag=False
    # points, vertices, zvalues = create_poly()
    i = 0
    pts=[]
    lines = input_file.read()
    #print(len(lines.splitlines()))
    splitted_lines = lines.splitlines()
    for line in splitted_lines:
        i+=1
        #print("llllllllllllllllllllllllllllllllllllllllllllllllllll",line,i)
        if line.startswith("#"):
            if line.startswith("# @D"):   #if a new route
                print("current line is {}".format(line))
                if flag:
                    #poly_data=set_poly(points,vertices,zvalues)
                    path_from_corners(corners=pts,min_edge_points=1000,close=False)

                    #filename = "road_densed_files/{}_{}_{}.txt".format(gmt_file, i, filename)
                    #print("filename is {}".format(filename))
                    #write_poly(poly_data,filename)
                    # points, vertices, zvalues = create_poly()
                # line=line.split("|")
                # if line[1]=="":
                #     filename=" ".join(line[3:])
                # else:
                #     filename=line[1]
                # z=float(line[-2])
                # print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",z)
                flag=True
                pts = []
                #print("flag is true")

        elif line.startswith(">"):   #still the same route
            continue

        else:
            x,y=line.split(" ")
            x = float(x)
            y = float(y)

            pts.append((x,y))
            #insert_value(points,vertices,zvalues,float(x),float(y),(z+0.1445)/10)  #otherwise the route would appear much above the terrain
            if i == len(splitted_lines):
                path_from_corners(corners=pts, min_edge_points=4, close=False)
                #poly_data = set_poly(points, vertices, zvalues)
                #filename = "road_densed_files/{}_{}_{}.txt".format(gmt_file,i, filename)
                #print("end of file,filename is {}".format(filename))
                #write_poly(poly_data, filename)


def main():
    dense_road_gmt_v2("9_21_Dec_2016.gmt")

    read_densed_points('9_21_Dec_2016.gmt')
    # dense_road_gmt("dup_removed.gmt")
    # read_densed_points('z0sim.modelpath_hr')
    #read_road_gmt_whole("dup_removed.gmt") #base layer

    #read_road_gmt('6_25_nov_2016.gmt')  #road that changes

    #read_ferry_gmt('14_Nov_2016_ferry.gmt')

    # file in glob.glob('rail_data_files/*.gmt'):
    # read_rail_gmt('14_Nov_2016_rail.gmt')

    #read_z_road_gmt('1_0300_14_Nov_2016.gmt')
if __name__ == '__main__':
    main()


#==================read a gmt file into a whole vtp file===============================================================
# def read_gmt_whole(gmt_file):
#     """take a gmt file, read into a whole vtp file regardless of different routes"""
#
#     input = open('road_data_files/{}'.format(gmt_file),'r')
#     lines = input.read().splitlines()
#     points, vertices, zvalues = create_poly()
#     #print(lines)
#     i = 0
#     count = 0
#     while i < len(lines):
#         if lines[i].startswith("# @D"): #read header
#             count +=1
#             print("current line is",lines[i])
#             line = lines[i].split('|')
#             if line[1]== '':
#                 rd = line[0]
#             else:
#                 rd = line[1:5]
#             print("rd             ",rd)
#             z =float(line[-2])
#             i+=1
#             x,y = (lines[i].split(' '))
#             #print("x is {} y is {}".format(x,y))
#             insert_value(points, vertices, zvalues, float(x), float(y),(z+0.1445)/10)
#
#         i+=1
#
#
#     poly_data = set_poly(points, vertices, zvalues)
#     print("polylllllllllllllllllll")
#
#     out= "road_vtp_files/{}.vtp".format(gmt_file)
#     write_poly(poly_data,out)
#     print("count",count)
#
# #==================read a gmt file into different vtp files=============================================================
# def read_gmt(gmt_file):
#     """take a normal gmt file, read into different vtp files according to different routes"""
#
#     input_file = open('road_data_files/{}'.format(gmt_file),'r')
#     flag=False
#     points, vertices, zvalues = create_poly()
#     i = 0
#     lines = input_file.read()
#     #print(len(lines.splitlines()))
#     splitted_lines = lines.splitlines()
#     for line in splitted_lines:
#         i+=1
#         #print("llllllllllllllllllllllllllllllllllllllllllllllllllll",line,i)
#         if line.startswith("#"):
#             if line.startswith("# @D"):   #if a new route
#                 print("current line is {}".format(line))
#                 if flag:
#                     poly_data=set_poly(points,vertices,zvalues)
#                     filename = "road_vtp_files/{}_{}_{}.vtp".format(gmt_file, i, filename)
#                     print("filename is {}".format(filename))
#                     write_poly(poly_data,filename)
#                     points, vertices, zvalues = create_poly()
#                 line=line.split("|")
#                 if line[1]=="":
#                     filename=" ".join(line[3:])
#                 else:
#                     filename=line[1]
#                 z=float(line[2])
#                 print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",z)
#                 flag=True
#                 #print("flag is true")
#
#         elif line.startswith(">"):   #still the same route
#             continue
#
#         else:
#             x,y=line.split(" ")
#             insert_value(points,vertices,zvalues,float(x),float(y),(z+0.145)/10.)  #otherwise the route would appear much above the terrain
#             if i == len(splitted_lines):
#                 poly_data = set_poly(points, vertices, zvalues)
#                 filename = "road_vtp_files/{}_{}_{}.vtp".format(gmt_file,i, filename)
#                 print("end of file,filename is {}".format(filename))
#                 write_poly(poly_data, filename)
#
#
# def main():
#     # read_gmt_whole("dup_removed.gmt") #base layer
#     read_gmt("1_0300_14_Nov_2016.gmt")  #road that changes


