import vtk
import os

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

#==================read a gmt file into a whole vtp file===============================================================
def read_gmt_whole(gmt_file):
    """take a gmt file, read into a whole vtp file regardless of different routes"""

    input = open('road_data_files/{}'.format(gmt_file),'r')
    lines = input.read().splitlines()
    points, vertices, zvalues = create_poly()
    #print(lines)
    i = 0
    count = 0
    while i < len(lines):
        if lines[i].startswith("# @D"): #read header
            count +=1
            print("current line is",lines[i])
            line = lines[i].split('|')
            if line[1]== '':
                rd = line[0]
            else:
                rd = line[1:5]
            print("rd             ",rd)
            z =float(line[-2])
            i+=1
            x,y = (lines[i].split(' '))
            #print("x is {} y is {}".format(x,y))
            insert_value(points, vertices, zvalues, float(x), float(y),(z+0.1445)/10)

        i+=1


    poly_data = set_poly(points, vertices, zvalues)
    print("polylllllllllllllllllll")

    out= "road_vtp_files/{}.vtp".format(gmt_file)
    write_poly(poly_data,out)
    print("count",count)

#==================read a gmt file into different vtp files=============================================================
def read_gmt(gmt_file):
    """take a normal gmt file, read into different vtp files according to different routes"""

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
            insert_value(points,vertices,zvalues,float(x),float(y),(z+0.145)/10.)  #otherwise the route would appear much above the terrain
            if i == len(splitted_lines):
                poly_data = set_poly(points, vertices, zvalues)
                filename = "road_vtp_files/{}_{}_{}.vtp".format(gmt_file,i, filename)
                print("end of file,filename is {}".format(filename))
                write_poly(poly_data, filename)


def main():
    # read_gmt_whole("dup_removed.gmt") #base layer
    read_gmt("1_0300_14_Nov_2016.gmt")  #road that changes




if __name__ == '__main__':
    main()
