"""Process shape files into gmt files
   Assumptions: (1) No space or brackets in any shapefile folder name
                (2) Redundant files like Aratere_rail-enabled_Ferry && Day_15_28_Nov_ not in any shapefile folder
   Sample command:
   python gmtify.py /home/melody/FW__Post-earthquake_infrastructure_restoration_rates_visualisation/Kaikoura_Transport_Shapefiles
"""

import os
import sys
import subprocess
import shutil
import glob
import calendar
import datetime
import argparse
import time
from collections import OrderedDict
#==========================================disaster begins=============================================================
GMT_DICT = OrderedDict([('flights', OrderedDict([(0.75, ("blue", 'Charter service')),
                                                 (0.50, ("pink", 'One way service')),
                                                 (0.95, ('orange', 'Temporary service')),
                                                 (1.50, ("magenta", 'Increased service')),
                                                 (1.00,('green', 'Regular service'))])),
                        ('rail', OrderedDict([(0.00, ('black', 'Closed')),
                                              (0.50, ('orange', 'Restricted')),
                                              (1.00,('white', 'Open'))])),
                        ('vehicle_passenger_ferries', OrderedDict([('2016_11_14', ('red', 'Closed')),    # ferry doesn't have los value somehow
                                                                   ('2016_11_15',('rosybrown', 'Reduced service & foot passage')),
                                                                   ('2016_11_17', ('rosybrown', 'Reduced service & foot passage')),
                                                                   ('2016_11_18', ('lightyellow', 'Reduced service')),
                                                                   ('2016_11_29',('green', 'Full service'))])),
                        ('road', OrderedDict([(0.00, ('red', 'Closed')),
                                              (0.10,('red', 'Closed')),
                                              (0.81,("navy", 'Convoy access')),
                                              (0.90,('darkorange', 'Limited access')),
                                              (0.91, ("darkorange", 'Limited access')),
                                              (0.80,('yellow', 'Open daytime (light vehicles)')),
                                              (0.95, ('limegreen', 'Open daytime')),
                                              (1.00, ('green', 'Open')),
                                              (1.10, ("green", 'Open'))]))])


SYMBOL_DICT = {'road': '', 'rail': '-.', 'flights': '-', 'vehicle_passenger_ferries': ''}
WIDTH_DICT = {'road': '2p', 'local': '0.7p', 'rail': '1p', 'flights': '2p', 'vehicle_passenger_ferries': '2p'}
LEGEND_WIDTH = '2p'
SHAPE_SIZE = {'road': '0.5i', 'rail': '0.7i', 'flights': '0.6i', 'vehicle_passenger_ferries': '0.5i'}
DX2 = {'road': '0.6i', 'rail': '0.8i', 'flights': '0.7i', 'vehicle_passenger_ferries': '0.6i'}
DX1 = {'road': '0.25i', 'rail': '0.35i', 'flights': '0.3i', 'vehicle_passenger_ferries': '0.25i'}
#===========================================ends========================================================================
TEMPLATE = "ogr2ogr -f 'GMT' {} {} -t_srs EPSG:4326"
GMT_DIR = "transport_gmts"
GMT_INFO = 'gmt_info.txt'
DUP = '2016_11_14'
# TEMPLATE2 = "ogr2ogr -f 'GMT' {} {} -s_srs EPSG:2193 -t_srs EPSG:4326"


def get_month_dict():
    """ convert from month number to abbreviated month name and
        return as a dict {month_name: month num}"""
    return {name: ("0{}".format(num) if num < 10 else str(num)) for num, name in enumerate(calendar.month_abbr)}


def validate_dir(dir):
    """validate user input abs dir path"""
    if not os.path.isdir(dir):
        sys.exit("{} does not exist".format(dir))


def make_folder(dir):
    """abs path to the biggest gmt folder containing all different kinds of transportation gmt files including dir name.
        eg./home/melody/FW__Post-earthquake_infrastructure_restoration_rates_visualisation/transport_gmts
    """
    if os.path.isdir(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)


def get_new_name(filename,month_dict):
    """return a new filename in 2017_01_21 or 2016_11_14_0300 format
       filename: *date_month_year.shp
       month_dict: {month_name: month num}
    """
    parts = filename[:-4].split('_')[::-1]
    length = len(parts)# reverse into year_month_day format
    if length >= 4:  # if road directory file untimed(len==4) or timed(5)
        parts = parts[:(length - 1)]
    month = parts[1]
    parts[1] = month_dict[month]    # convert Jan to 01
    date = parts[2]
    parts[2] = "0{}".format(date) if len(date) < 2 else date  # reformat date 8 to 08
    new_name = '_'.join(parts)
    output_file = "{}.gmt".format(new_name)  # form output gmt filename
    #print("output file is:", output_file)
    return output_file


def shp_to_gmt(input_dir,gmt_dir):
    """convert shape file to raw gmt
       input_dir: abs path to biggest folder of transportation shape files including dir name.
       eg./home/melody/FW__Post-earthquake_infrastructure_restoration_rates_visualisation/Kaikoura_Transport_Shapefiles
       gmt_dir:abs path inclusive to biggest output gmt files dir
    """
    validate_dir(input_dir)
    month_dict = get_month_dict()
    for subdir in os.listdir(input_dir):  # eg. subdir = Road
        subdir_path = os.path.join(input_dir,subdir)  # get abs path of subdir
        print("converting {} to raw gmts".format(subdir_path))
        if os.path.isdir(subdir_path):  # make sure it's a dir not a file
            #print("Processing {}".format(subdir_path))
            output_dirname = subdir.split("/")[-1].replace(" ", "_").lower()+'_temp'  # form output gmt folder name
            output_dir = os.path.join(gmt_dir, output_dirname)  # form sub folder for output gmts
            make_folder(dir=output_dir)  # make a sub folder for output gmts eg.road, under the biggest gmt folder
            #print("ouputdrrrrr",output_dir)
            for filename in glob.glob1(subdir_path,"*.shp"):   # now loop through the shape files in the shape file subdir # only convert file ending with shp, can use shx instead
                output_file = get_new_name(filename,month_dict)
                dest = os.path.join(output_dir,output_file)
                source = os.path.join(subdir_path,filename)
                cmd = TEMPLATE.format(dest, source)  # cmd to convert files
                #print(cmd)
                try:
                    subprocess.call(cmd,shell=True)  # convert shp to gmt
                except Exception as (e):
                    print(e)
                    sys.exit("Unable to convert from shp to gmt")
            #print("FINISHING {}".format(output_dir))


def get_width(z,name):
    """"return the correct width according to trans type/los value
        name:transportation type
        z: los value
    """
    remainder = str(2 - float(z))
    if '9' in remainder:  # local roads(ends with floating digit 1 eg 0.91, 0.1, 1.1) are skinnier
        width = WIDTH_DICT['local']
    else:
        width = WIDTH_DICT[name]
    return width


def process_gmt(dir):
    """it's too big, smart people please change this.
       add gmt info to raw gmts, return a dict of sets {transportation type: set(gmt_info)}
       why no use gmt_info eg. '1p,red,-,closed' as key? Because it's not 100% sure that all comobs of width + colour + symbol + status will be unique
       dir:abs path to the biggest gmt dir
           eg./home/melody/FW__Post-earthquake_infrastructure_restoration_rates_visualisation/transport_gmts
    """
    validate_dir(dir)
    # all_info = {}  # collecting all combos for making legends
    for subdir in os.listdir(dir):  # loop through the biggest gmt
        print("processing {}".format(subdir))
        name = subdir[:-5]
        # all_info[name] = set()
        #print(name)
        symbol = SYMBOL_DICT[name]  # get rid of '_temp'
        symbol_info = ""
        if symbol != '':
            symbol_info = ",{}".format(symbol)
        trans_dict = GMT_DICT[name]   # get the correct transportation dict
        subdir_path = os.path.join(dir,subdir)
        # print("subdir path",subdir_path)
        filenames = os.listdir(subdir_path)
        #print(symbol)

        if name == 'vehicle_passenger_ferries':  # ferries don't have los value. status are determined by date. not good
            print("process ferris")
            dates = sorted(trans_dict.keys())
            print("dates are",dates)
            for filename in filenames:
                date = filename[:-4]
                print("cuurent date is",date)
                for i in range(len(dates)):
                    day = dates[i]
                    if day <= date:
                        colour, status = trans_dict[day]
                    else:
                        day = dates[i-1]
                        break
                #print("date is {} day is {} clour is {} satus is {}".format(date, day, colour, status))
                filepath = os.path.join(subdir_path, filename)
                print(colour,day)
                with open(filepath, 'r') as in_gmt:
                    buf = in_gmt.readlines()  # first read the file into buffer memory so that we can read and write
                with open(filepath, 'w') as out_gmt:  # now we overwrite the original raw gmt file
                    out_gmt.write("#{}\n".format(name))
                    for line in buf:
                        if line.startswith('>'):
                            info = " -W{},{}{},{}\n".format(WIDTH_DICT[name], colour, symbol_info,day)  # form gmt info
                            # info_to_add = "{},{}\n".format(info[3:-1], status)
                            # all_info[name].add(info_to_add)
                            line = line.strip() + info
                            #print("write line", line)
                        if not line.startswith("#"):  # ignore header
                            out_gmt.write(line)

        else:  # if not ferry, get gmt info by los value
            for filename in filenames:   #loop through all subdirs inside the biggest gmt
                #print("fff",filename)
                found_z = False
                filepath = os.path.join(subdir_path,filename)
                with open(filepath, 'r') as in_gmt:
                    buf = in_gmt.readlines()   # first read the file into buffer memory so that we can read and write safely
                with open(filepath, 'w') as out_gmt:  # now we overwrite the original raw gmt file
                    z_index = -1
                    info = ""
                    i = 0
                    out_gmt.write('#{}\n'.format(name))
                    while i < len(buf):
                        current_line = buf[i]
                        if current_line.startswith("# @N"):  # Los value header line
                            #print("afdsadfsdf",current_line)
                            z_index = current_line.strip().split('|').index('LoS')  # get the index position of Los value in header
                            #print("z_index",z_index)
                            found_z = True
                        elif current_line.startswith('>') and found_z:  # if didn't find z, we keep the original raw gmt as we can't wirte any gmt info and need to look at the file individually as error may occur during convertion.current error files are Aratere_rail-enabled_Ferry.gmt and Day_15_28_Nov_2016.gmt
                            next_line = buf[i+1]
                            if next_line.startswith("# @D"):  # if next line is a new route, we need to add a new gmt info to the line above
                                #print("nexxt line is header {}".format(next_line))
                                z = next_line.strip().split('|')[z_index]   # get LoS value
                                #print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz", z)
                                width = get_width(z,name)
                                colour, status = trans_dict[float(z)]
                                info = " -W{},{}{},{}\n".format(width,colour,symbol_info,z)   #form gmt info
                                # info_to_add  = "{},{}\n".format(info[3:-1], status)
                                # print("to add name is",name)
                                # all_info[name].add(info_to_add)
                            current_line = current_line.strip() + info  # append additional gmt info to the header
                        if not current_line.startswith("#"):
                            out_gmt.write(current_line)
                        i += 1
                if not found_z:
                    print("No Los (z) value found in file {}".format(filepath))
                    shutil.move(filepath,dir)   #move files without los(z) upper a level`
    # print(all_info)
    # return all_info


def write_gmt_info(dir, date_info_dict):
    """write out a file with gmt pen info
       dir:abs path to gmt_info file, should be the same as biggest gmt dir
       date_info_dict: a dict of sets {date: {transportation type: set(gmt_info)}
    """
    file = open(os.path.join(dir,GMT_INFO ),'w')
    for date in sorted(date_info_dict.keys()):
        file.write("# {}\n".format(date))
        for name in date_info_dict[date]:
            file.write('{}\n'.format(name))
            for info in date_info_dict[date][name]:
                file.write('{}: {}\n'.format(info,GMT_DICT[name][info]))
    file.close()


def get_filenames(dir):
    """return tranportation files as a dict:{subdirpath:[filenames]} and
       return all different dates as as a set
       dir : abs path to the biggest gmt dir
             eg."/home/melody/FW__Post-earthquake_infrastructure_restoration_rates_visualisation/transport_gmts
    """
    timeline = set()
    validate_dir(dir)
    files={}
    for subdir in os.listdir(dir):  #loop through the biggest gmt
        subdir_path = os.path.join(dir,subdir)
        if os.path.isdir(subdir_path):
            #print("subdir path",subdir_path)
            filenames = os.listdir(subdir_path)
            files[subdir_path] = filenames
            for name in filenames:
                if name != "{}.gmt".format(DUP):  #already have 2016_11_14_0300/1600_1/2.gmt
                    timeline.add(name)
    #print(files)
    #print(timeline)
    return files, timeline


def get_closet_before(files,timeline):
    """find closet date <= the date in the time_set,
       one each from different transportation types
       return as a dict of dicts {date: {dir: filename}}
    """
    times = {}
    for time in timeline:
        time = time[:-4]  # get rid of '.gmt'
        times[time]={}
        #print("current times is",time)
        for dir,filenames in files.items():
            times[time][dir] = {}
            for name in filenames:
                date = name[:-4] # get rid of '.gmt'
                if times[time][dir] == {}:
                    if date <= time:
                        times[time][dir] = name
                else:
                    if times[time][dir] < date <= time:
                        times[time][dir] = name

    # print("times",times)
    return times


def swap_file(files, pattern, dest_index):
    """swap pattern-file with the dest-index file
       files: a list of file names
       pattern: pattern of the source file eg 'rail'
       dest_index: destination index to  put the pattern-file
    """
    pattern_index = -1
    for i in range(len(files)):
        #print(files)
        if pattern in files[i].split('/')[-2]:
            pattern_index = i
            break

    if pattern_index == -1:
        sys.exit("pattern {} file not found".format(pattern))

    files[dest_index], files[pattern_index] = files[pattern_index], files[dest_index]


def group_by_date(times, dir):
    """make a new folder named by date
       put all closet <= date from different transportation types in the new folder
       times: {date: {dir:filename}}
       dir: abs path to the biggest gmts folder
       file: to write closet date gmt files into a bigger file or not. Default False(not)
            If not, just keep them in a folder;
            else, a dated file instead of folder and return a dict{date: {trans_type: set(gmt_info)}} for greying in legend
    """
    print("grouping dates")
    sorted_dates = sorted(times.keys())
    #print(sorted_dates)
    #print("afdsafsf",sorted_dates[0].split('.')[0].split('_')[:3])
    year,month,date = sorted_dates[0].split('_')[:3]
    day1 = datetime.date(int(year),int(month),int(date))
    date_info = {}
    for date in sorted_dates:
        # new_dir = os.path.join(dir,date)
        # make_folder(new_dir)
        #files = [None for i in range(len(times[date].keys()))]
        files = []
        # index = 0
        for sub_dir,filename in times[date].items():
            #print("sub_dir,name",sub_dir,filename)
            if filename != {}:
                old_path = os.path.join(sub_dir, filename)
                files.append(old_path)

        year, month, ddate = date.split('_')[:3]  # take the first 3 parts year_month_date
        days = (datetime.date(int(year),int(month),int(ddate)) - day1).days + 1  # no difference from first date = Day1
        big = open("{}/{}_{}.gmt".format(dir,days,date),'a')
        key_name = "{}_{}".format(days,date)
        date_info[key_name] = {}

        swap_file(files, 'flights', -1)  # swap flights with the last item of the list as flights need to be plotted on top

        # not in the same loop to avoid the case that we just swapped flights with rail
        swap_file(files, 'rail', -2) # rail width is thinner than rail so needs to be plotted after road

        print("now files are: ",files)
        #print("{}/{}_{}".format(dir,days,date),len(files))
        for f in files:
            #print("appending to big",f)
            #print(f)
            with open(f,'r') as r:
                lines = r.readlines()
                for line in lines:
                    if line.startswith('#'):
                        trans_type = line.strip()[1:]
                        if trans_type not in date_info[key_name].keys():
                            date_info[key_name][trans_type] = set()
                    if line.startswith('>'):
                        parts = line.strip().split(',')
                        try:
                           parts[-1] = float(parts[-1]) # get los or date'
                        except ValueError:
                           print("encounting ferries")
                        date_info[key_name][trans_type].add(parts[-1])
                        line = ','.join(parts[:-1]) + '\n'   # get rid of los or date at the end or gmt line
                    big.write(line)
        big.close()
    print("date info",date_info)
    return date_info


def clean_up(dir, pattern='_temp'):
    """dir:abs path to the folder containing directries you want to clean up
       pattern: common pattern of directories that you want to delete"""
    print("cleaning up")
    dirs = glob.glob1(dir,'*'+ pattern + '*')
    for d in dirs:
        #print(d)
        shutil.rmtree(os.path.join(dir,d))


def write_legend(gmt_dir, date_info_dict, dx1='0.2i',column=1, shape='-', shape_size='0.5i',shape_colour='-', dx2='0.5i', unused_text_colour='grey', background='darkgrey'):
    """write a legend sh file for ecah GMT file
       gmt_dir: abs path to dir containing all unique-day gmt files
       gmtinfo_dict: a dict of sets {transportation type: set(gmt_info)}
       date_info_dict: a dict of sets {date:{transportation type: set(gmt_info)}}
       column: how many columns each row
       S [dx1 shape shape_size shape_colour, pen [ dx2 text ]]
       bash: to out put as a bash script or not, default False(not)
       http://gmt.soest.hawaii.edu/doc/5.3.2/pslegend.html
    """
    print("writing legends")
    validate_dir(gmt_dir)
    gmt_files = glob.glob1(gmt_dir,'*_*.gmt')
    #print(gmt_files)

    for gmt_name in gmt_files:
        prefix = gmt_name.split('.')[0]
        parts = prefix.split('_')
        #print(parts[1:4])
        year, month, date = parts[1:4]
        #print("mongth is ",month)
        month = calendar.month_abbr[int(month)]
        day = parts[0]
        time = " "
        if len(parts) == 5:  # if name has time
            time += parts[-1]
            time = time[0:3] + ':' + time[3:] + " "   # change ' 0300' to ' 03:00 '

        outputpath = os.path.join(gmt_dir,"{}.legend".format(prefix))
        file = open(outputpath,'w')

        # file.write('#!/usr/bin/env bash\n')
        # file.write("gmt pslegend -R-10/10/-10/10 -JM10i -F+g{} -Dx0i/0i+w10i/10i+jBL+l1.2 -C1i/0.5i -B5f1 << EOF > legend_{}.ps\n".format(background, prefix))
        # file.write('# G is vertical gap, V is vertical line, N sets # of columns, D draws horizontal line.\n# H is header, L is label, S is symbol, T is paragraph text, M is map scale.\n')

        file.write('# w-4i\n')
        file.write('H 20p Helvetica-Bold{}Day {} ({} {} {})\n'.format(time, day, date, month, year))
        # file.write('N {}\n'.format(column))
        # file.write('V 0 1p\n')

        for trans in GMT_DICT.keys():
            trans_parts = ''.join(trans.split('_')[-1])  # 'vechcle passagne ferries' to 'ferries'
            s = 's' if trans_parts[-1] != 's' and trans_parts != 'rail' else ''   #if trans type not ending with 's' and it's not a rail
            trans_txt = trans_parts[0].upper() + trans_parts[1:] + s  #caplitaize first letter
            file.write('G 1l\n')
            file.write('L - Helvetica-Bold L {}\n'.format(trans_txt))
            status = ""
            for los in GMT_DICT[trans].keys():
                pen_colour, new_status = GMT_DICT[trans][los]
                if new_status != status:   #local have same status text as SH, so get rid of local in the legends
                    status = new_status
                    set_text_colour = ''
                    end_text_colour = ''
                    #print(date_info_dict[prefix][trans])
                    #print(prefix)
                    if los not in date_info_dict[prefix][trans]:
                        set_text_colour = '@;{};'.format(unused_text_colour)
                        end_text_colour = '@;;'
                    symbol = SYMBOL_DICT[trans]
                    if symbol:
                        symbol = ',{}'.format(symbol)
                    file.write('S {} {} {} {} {},{}{} {} {}{}{}\n'.format(DX1[trans], shape, SHAPE_SIZE[trans], shape_colour, LEGEND_WIDTH,
                                                                        pen_colour, symbol, DX2[trans], set_text_colour,
                                                                        status, end_text_colour))
        # file.write('EOF\n')
        # file.write("psconvert -E500 -A -TG legend_{}.ps\n".format(prefix))

        file.close()
    print("all finished")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dir',type=str, help='abs path to biggest folder of transportation shape files including dir name.eg./home/melody/FW__Post-earthquake_infrastructure_restoration_rates_visualisation/Kaikoura_Transport_Shapefiles')
    args = parser.parse_args()

    shapes_dir = args.dir
    gmt_dir = os.path.join('/'.join(shapes_dir.split('/')[:-1]),GMT_DIR)

    make_folder(gmt_dir)

    shp_to_gmt(shapes_dir,gmt_dir)

    process_gmt(gmt_dir)

    files, timeline = get_filenames(gmt_dir)
    times = get_closet_before(files, timeline)
    date_info_dict = group_by_date(times,gmt_dir)
    write_gmt_info(gmt_dir, date_info_dict)

    clean_up(gmt_dir)

    write_legend(gmt_dir, date_info_dict)


if __name__ == '__main__':
    pre = time.time()
    main()
    duration = time.time() - pre
    print(duration)
