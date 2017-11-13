from math import *
import pyproj
from road_txt_reader import *
from pylab import *

def draw_arc(startlon,startlat,endlon,endlat,n,upper,outname):
    """take the longitude and latitude of two end points, drawn a dotted arc between the two points;
       n is the number of points along the arc;
       upper=True/False decides whether the upper or lower half of the ellipse will be drawn as the arc;
       outname is the route name of the output vtp file"""

    n = float(n)
    u = sqrt((endlon-startlon)**2 + (endlat-startlat)**2)/2    #distance between 2 end points (2a of an ellipse)
    print("uuuuuuuuuuuuuuu",u)
    v = u/2.5 #2b of an ellipse
    dt = u/n
    theta = atan((endlat-startlat)/(endlon-startlon))  #angle between x-axis and line u
    center_x = (endlon + startlon)/ 2.
    center_y = (endlat + startlat) / 2.
    print("center_x,center_y",center_x,center_y)
    pts = []
    X=[]  #to visualize the points in python
    Y=[]
    points, vertices, zvalues = create_poly()
    insert_value(points, vertices, zvalues,startlon, startlat, 0.11446)
    for i in range(0,int(n)):
        t = dt * i/u
        if upper == False:
            t = -t
        print("t",t)
        x = cos(theta) * u * cos(pi*t) - sin(theta)* v *sin(pi*t)   #x is the offset between new_x center_X
        y = sin(theta) * u * cos(pi*t) + cos(theta)* v *sin(pi*t)
        print("x,y",x,y)
        new_lon = center_x + x
        new_lat = center_y + y
        pts.append((new_lon,new_lat))
        X.append(new_lon)
        Y.append(new_lat)
        print("appended",(new_lon,new_lat))
        insert_value(points,vertices,zvalues,new_lon,new_lat,0.11446)
    insert_value(points, vertices, zvalues, endlon, endlat, 0.11446)
    poly_data = set_poly(points, vertices, zvalues)
    write_poly(poly_data, "airlines/{}.vtp".format(outname))
    plot(X, Y)
    scatter(X, Y)
    scatter([center_x], [center_y], color='r', s=100)
    axis('equal')
    show()

#draw_arc(172.639847,-43.525650,174.776217, -41.28648,70,False,"air_chch_welly2")
# draw_arc(172.639847,-43.525650,173.9528,-41.51603,50,True,"air_chch_blenheim")
# draw_arc(174.776217, -41.28648,173.9528,-41.51603,20,False,"air_welly_blenheim")
draw_arc(174.776217, -41.28648,174.045,-41.28472,20,True,"air_welly_picton")
# draw_arc(172.639847,-43.525650,173.70222,-42.42500,20,False,"air_chch_kaikoura")
#draw_arc(174.0528,-41.51603, 173.70222, -42.36500, 20, False, "air_blenheim_kaikoura")
#draw_arc(174.776217, -41.28648, 173.70222,-42.36500, 20, False,"air_welly_kaikoura")
#
# def draw_circular_line(longitude1,latitude1,longitude2,latitude2,num_of_segments):
#     """takes longitudes and latitudes of two end points and a given number,
#        return a list of calculated points based on the great circle line between these two points"""
#
#     onelessthansegments = num_of_segments - 1
#     fractionalincrement = (1.0/onelessthansegments)
#
#     ptlon1_radians = math.radians(longitude1)
#     ptlat1_radians = math.radians(latitude1)
#     ptlon2_radians = math.radians(longitude2)
#     ptlat2_radians = math.radians(latitude2)
#
#     distance_radians=2*math.asin(math.sqrt(math.pow((math.sin((ptlat1_radians-ptlat2_radians)/2)),2) + math.cos(ptlat1_radians)*math.cos(ptlat2_radians)*math.pow((math.sin((ptlon1_radians-ptlon2_radians)/2)),2)))
#     # 6371.009 represents the mean radius of the earth
#     # shortest path distance
#     distance_km = 6371.009 * distance_radians
#     coords = []
#     coords.append((longitude1,latitude1))
#
#     f = fractionalincrement
#
#     for i in range(1,onelessthansegments):
#             # f is expressed as a fraction along the route from point 1 to point 2
#             A=math.sin((1-f)*distance_radians)/math.sin(distance_radians)
#             #print("A IS",A)
#             B=math.sin(f*distance_radians)/math.sin(distance_radians)
#             #print("B IS", B)
#             x = A*math.cos(ptlat1_radians)*math.cos(ptlon1_radians) + B*math.cos(ptlat2_radians)*math.cos(ptlon2_radians)
#             y = A*math.cos(ptlat1_radians)*math.sin(ptlon1_radians) +  B*math.cos(ptlat2_radians)*math.sin(ptlon2_radians)
#             z = A*math.sin(ptlat1_radians) + B*math.sin(ptlat2_radians)
#             #print("x y z are",x,y,z)
#             newlat=math.atan2(z,math.sqrt(math.pow(x,2)+math.pow(y,2)))
#             newlon=math.atan2(y,x)
#
#             newlat_degrees = math.degrees(newlat)
#             newlon_degrees = math.degrees(newlon)
#             coords.append((newlon_degrees,newlat_degrees))
#             print("new lat, new lon is({},{})".format(newlat_degrees, newlon_degrees))
#             i += 1
#             f = f + fractionalincrement
#     coords.append((longitude2,latitude2))
#     return coords
#
# #draw_circular_line(172.639847,-43.525650,173.283966, -41.270634,200)
#
#
# def geod_circlular_line(lon1,lat1,lon2,lat2,steps):
#     # calculate distance between points
#     g = pyproj.Geod(ellps='GRS80')
#     (az12, az21, dist) = g.inv(lon1,lat1,lon2,lat2)
#
#     # calculate line string along path with segments <= 1 km
#     lonlats = g.npts(lon1,lat1,lon2,lat2, 1 + int(dist / steps))
#
#     # npts doesn't include start/end points, so prepend/append them
#     lonlats.insert(0, (lon1,lat1))
#     lonlats.append((lon2,lat2))
#     print(lonlats)
#     return lonlats
#
# from numpy import cos,sin,arccos
# import numpy as np
#
# def parametric_circle(t,xc,yc,R):
#     x = xc - R*cos(t)
#     y = yc - R*sin(t)
#     return x,y
#
# def inv_parametric_circle(x,xc,R):
#     t = arccos((xc-x)/R)
#     return t
#
# def inv_parametric_circle2(y,yc,R):
#     t = arccos((yc-y)/R)
#     return t
#
# N = 10
#
#
#
# start_point = (172.639847,-43.525650)
# end_point   = (173.283966,-41.270634)
#
# xc = float(start_point[0] + end_point[0])/2
# yc = float(start_point[1] + end_point[1])/2
#
# r = float(math.sqrt((start_point[0]-end_point[0])**2 + (start_point[1] - end_point[1])**2)/2)
#
# pts = []
# start_t = inv_parametric_circle(start_point[0], xc, r)
# end_t   = inv_parametric_circle(end_point[0], xc, r)
#
# arc_T = np.linspace(start_t, end_t, N)
# print(arc_T)
# points, vertices, zvalues = create_poly()
# X,Y = parametric_circle(arc_T, xc, yc, r)
# print(X,Y)
# # for i in range(N):
# #     x,y = parametric_circle(arc_T[i],xc,yc,r)
# #     print(x,y)
#
# #     insert_value(points, vertices, zvalues, float(x), float(y), 0.1446)
# # poly_data = set_poly(points, vertices, zvalues)
# # write_poly(poly_data, 'chch_nelson_circular_line.vtp')
#
#
#
#
#
#
#
#
# # arc_T = np.linspace(start_t, end_t, N)
# # print(arc_T)
# #
# from pylab import *
# X,Y = parametric_circle(arc_T, xc, yc, R)
# plot(X,Y)
# scatter(X,Y)
# scatter([xc],[yc],color='r',s=100)
# axis('equal')
# show()


#
# # #geod_circlular_line(172.639847,-43.525650,173.283966, -41.270634,200)
# # def main():
# #     #chch to nelson
# #     pts = random_draw(173.283966, -41.270634,172.639847, -43.525650,10)
# #     points, vertices, zvalues = create_poly()
# #     for x,y in pts:
# #         insert_value(points, vertices, zvalues, float(x), float(y), 0.1446)
# #     poly_data = set_poly(points, vertices, zvalues)
# #     write_poly(poly_data, 'chch_nelson_circular_line.vtp')
# #
# # if __name__ == '__main__':
# #     main()