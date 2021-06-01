"""This module creates image difference maps of specified AOIs and
 time periods from GRACE Tellus groundwater anomaly data, to show
 change over time.
Author: Arthur Elmes
2021-05-28"""

import os
# some odd error with the basemap data
try:
    print(os.environ['PROJ_LIB'])
except:
    os.environ["PROJ_LIB"] = r"C:\Users\arthu\Anaconda3\envs\e84_win\Library\share\proj"
print(os.environ['PROJ_LIB'])

from osgeo import osr
from mpl_toolkits.basemap import Basemap
import numpy as np
import matplotlib.pyplot as plt
import glob


# this pckg
from grace import viz_grace


def get_file_from_date(base_dir, in_date):
    file_name = glob.glob(os.path.join(base_dir, "GRD-3_" + in_date + "*"))[0]

    return file_name


def img_diff(img_file_0, img_file_1, o_dir, contrast_stretch, ul_coord, lr_coord):
    coords = '_'.join([str(ul_coord[0]), str(ul_coord[1]), str(lr_coord[0]), str(lr_coord[1])])
    o_dir = os.path.join(o_dir, 'map_exports', coords)

    if not os.path.exists(o_dir):
        os.makedirs(o_dir, exist_ok=True)

    # a lot of this should be condensed with viz_grace
    # use gdal to read in data as np array
    data_0, gt_0, proj_0 = viz_grace.img_to_arr(img_file_0)
    data_1, gt_1, proj_1 = viz_grace.img_to_arr(img_file_1)

    # mask out the NoData
    data_0 = np.ma.masked_array(data_0, data_0 == -99999.0)
    data_1 = np.ma.masked_array(data_1, data_1 == -99999.0)

    # parse geotransform details
    # can be the same, because both files should have identical SRS and dims
    xres = gt_0[1]
    yres = gt_0[5]
    xmin = ul_coord[1]
    xmax = lr_coord[1]
    ymax = ul_coord[0]
    ymin = lr_coord[0]

    # TODO figure out weird quirk in central longitude
    m = Basemap(projection='laea',
                llcrnrlat=ymin,
                urcrnrlat=ymax,
                llcrnrlon=xmin,
                urcrnrlon=xmax,
                lon_0=((xmax+xmin)/2),
                lat_0=ymax+10,
                lat_1=((ymax+ymin)/2),
                lat_2=ymin-10,
                resolution='c')

    # make grid of xy coords for plotting
    xy_source = np.mgrid[ymax:ymin - 1:yres, xmin:xmax + 1:xres]
    inproj = osr.SpatialReference()
    inproj.ImportFromWkt(proj_0)
    outproj = osr.SpatialReference()
    outproj.ImportFromProj4(m.proj4string)
    xx, yy = viz_grace.convert_xy(xy_source, inproj, outproj)

    # These to be implemented with any data with units that
    # aren't degrees, unlike the GRACE gridded data
    # col0, col1 = int((90 - ymax + xres * 0.5) / xres), \
    #              int((90 - ymin + xres * 0.5) / yres)
    # row0, row1 = int((180 + xmin) / gt[5]), \
    #              int((180 + xmax) / gt[5])

    # slice data based on user extent
    data_0 = data_0[90 - ymax:90 - ymin, xmin + 180:xmax + 180]
    data_1 = data_1[90 - ymax:90 - ymin, xmin + 180:xmax + 180]

    # take image difference to show change
    data_diff = data_1 - data_0

    # plotting stuff
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    title = 'GRACE Land Water-Equivalent-Thickness Surface Mass Delta between: ' + \
            os.path.splitext(os.path.basename(img_file_0))[0][6:21] + \
            ' and ' + os.path.splitext(os.path.basename(img_file_1))[0][6:21]
    ax.set_title(title, loc='center', pad=22, color='white')

    # TODO these need to be dynamic
    stretch_min = -0.25
    stretch_max = 0.25

    im = m.pcolormesh(xx,
                      yy,
                      data_diff,
                      cmap=plt.cm.plasma,
                      shading='auto',
                      vmin=stretch_min,
                      vmax=stretch_max)
    fig.set_facecolor('black')
    ax.set_facecolor('black')
    ax.tick_params(
        axis='x',
        color='white'
    )

    # annotate
    # credit to: https://stackoverflow.com/questions/31411793/basemap-drawparallels-tick-label-color
    def setcolor(x, color):
        for m in x:
            for t in x[m][1]:
                t.set_color(color)

    m.drawcountries()
    m.drawcoastlines(linewidth=.5)

    # for some reason getting lat/long labels to change color requires this funny trick
    merid = m.drawmeridians(np.arange(0, 361, 20), labels=[1, 0, 0, 1], color='white')
    setcolor(merid, 'white')
    par = m.drawparallels(np.arange(-90, 91, 20), labels=[1, 0, 0, 1], color='white')
    setcolor(par, 'white')

    cb = m.colorbar(im, location='bottom', pad=0.5, ax=ax)

    cb.set_label('GRACE Groundwater Anomaly', color='white')
    cb.ax.xaxis.set_tick_params(color='white')
    cb.ax.yaxis.set_tick_params(color='white')
    cb.ax.set_xticklabels(np.round(np.arange(stretch_min, stretch_max+0.1, 0.1), 2),
                          color='white')

    f_name = os.path.join(o_dir, "_".join([os.path.basename(img_file_0[:-4]),
                                           os.path.basename(img_file_1[:-4]),
                                           str(ul_coord[0]), 'Deg',
                                           str(ul_coord[1]), 'Deg_by',
                                           str(lr_coord[0]), 'Deg_',
                                           str(lr_coord[1]), 'Deg']))
    fig.savefig(f_name)
    # fig.savefig('{a}{b}_{c}_{d}_{e}.png'.format(a=o_dir,
    #                                                 b=os.path.basename(img_file_0[:-4]),
    #                                                 c=os.path.basename(img_file_1[:-4]),
    #                                                 d=str(ul_coord[0]) + 'Deg_' + str(ul_coord[1]) + 'Deg_by',
    #                                                 e=str(lr_coord[0]) + 'Deg_' + str(lr_coord[1]) + 'Deg'))


def run_img_diff(start_date, end_date, ul_coord, lr_coord, workspace):
    img_file_0 = get_file_from_date(workspace, start_date)
    img_file_1 = get_file_from_date(workspace, end_date)
    img_diff(img_file_0, img_file_1, workspace, True, ul_coord, lr_coord)


if __name__ == '__main__':
    import os
    import glob
    import sys
    #workspace = '/home/arthur/Dropbox/career/e84/sample_data/'
    workspace = r'C:\Users\arthu\Dropbox\career\e84\sample_data'

    # out_dir = os.path.join(workspace, 'map_exports')
    out_dir = workspace
    os.chdir(workspace)

    # for testing
    date_0 = '2010152'
    date_1 = '2010213'

    img_file_0 = get_file_from_date(workspace, date_0)
    img_file_1 = get_file_from_date(workspace, date_1)

    # make output dir if it doesn't exist
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    # this will be user-entered via cmd
    ul = (-10, 100)
    lr = (-45, 160)

    # create difference image between the two provided dates
    img_diff(img_file_0, img_file_1, out_dir, True, ul, lr)