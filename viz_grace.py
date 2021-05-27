import matplotlib.pyplot as plt
import rasterio as rio
from rasterio.warp import transform
import os
from skimage import exposure
import numpy as np
from matplotlib.font_manager import FontProperties
from PIL import Image
from mpl_toolkits.basemap import Basemap
import osr
import gdal

import sys


def convert_xy(xy_source, inproj, outproj):
    # function to convert coordinates
    # credit: Rutger Kassies https://stackoverflow.com/questions/20488765/plot-gdal-raster-using-matplotlib-basemap

    shape = xy_source[0, :, :].shape
    size = xy_source[0, :, :].size

    # the ct object takes and returns pairs of x,y, not 2d grids
    # so the the grid needs to be reshaped (flattened) and back.
    ct = osr.CoordinateTransformation(inproj, outproj)
    xy_target = np.array(ct.TransformPoints(xy_source.reshape(2, size).T))

    xx = xy_target[:, 0].reshape(shape)
    yy = xy_target[:, 1].reshape(shape)

    return xx, yy


def do_plot(img, img_name, out_dir, contrast_stretch, low, high, ul_coord, lr_coord, geotransform, projection):

    # parse geotransform details
    xres = geotransform[1]
    yres = geotransform[5]

    # WORKING LIMITS get the edge coordinates and add half the resolution
    # to go to center coordinates
    # xmin = gt[0] + xres * 0.5
    # xmax = gt[0] + (xres * 360) - xres * 0.5
    # ymin = gt[3] + (yres * 180) + yres * 0.5
    # ymax = gt[3] - yres * 0.5

    # get the edge coordinates and add half the resolution
    # to go to center coordinates
    xmin = geotransform[0]# + xres * 0.5
    xmax = geotransform[0]# + (xres * 360) - xres * 0.5
    ymin = geotransform[3]# + (yres * 180) + yres * 0.5
    ymax = geotransform[3]# - yres * 0.5


    #
    # ymax = ul_coord[0] - yres * 0.5
    # ymin = lr_coord[0] + yres * 0.5
    #
    # xmax = lr_coord[1]  - xres * 0.5
    # xmin = ul_coord[1] + xres * 0.5

    print(f'upper right corner lat: {ymax}')
    print(f'lower left corner lat: {ymin}')
    print(f'upper right corner lon: {xmax}')
    print(f'lower left corner lon: {xmin}')


    # TODO probably just cut this, and also the parameter for it
    # Perform contrast stretch on RGB range
    if contrast_stretch:
        img = exposure.rescale_intensity(img, in_range=(low, high))

    # Set the figure size
    fig = plt.figure(figsize=(10, 10))
    ax = plt.Axes(fig, [0, 0, 1, 1])

    # TODO add vertical axis, and make axes display lat/long
    #ax.set_axis_off()
    fig.add_axes(ax)

    fp = FontProperties(family='DejaVu Sans', size=16, weight='bold')
    fig.suptitle(os.path.basename(img_name), fontproperties=fp, color='black')

    m = Basemap(projection='merc',
                #lon_0=0,
                llcrnrlat=ymin,
                urcrnrlat=ymax,
                llcrnrlon=xmin,
                urcrnrlon=xmax,
                lon_0=(ymin+ymax)/2,
                resolution='c')

    col0, col1 = int((ul_coord[1] - geotransform[0] + xres * 0.5)/geotransform[1]), \
                 int((lr_coord[1] - geotransform[0] + xres * 0.5)/geotransform[1])
    row0, row1 = int((ul_coord[0] - geotransform[3])/geotransform[5]), \
                 int((lr_coord[0] - geotransform[3])/geotransform[5])

    # print(ul_coord)
    # print(lr_coord)
    # print(col0, col1)
    # print(row0, row1)
    #print(img.shape)
    img = img[row0:row1, col0:col1]
    #print(img.shape)

    # make grid of xy coords for plotting
    xy_source = np.mgrid[ymax+yres:ymin:yres, xmin:xmax+xres:xres]

    inproj = osr.SpatialReference()
    inproj.ImportFromWkt(projection)

    outproj = osr.SpatialReference()
    outproj.ImportFromProj4(m.proj4string)

    xx, yy = convert_xy(xy_source, inproj, outproj)

    im = m.pcolormesh(xx, yy, img[:], alpha=0.9, cmap=plt.cm.RdBu, shading='auto')
    print(img)

    m.drawcoastlines(linewidth=1)
    m.drawcountries(linewidth=1)

    cb = fig.colorbar(im, location='bottom')
    cb.ax.yaxis.set_tick_params(color='black')
    cb.outline.set_edgecolor('white')
    plt.setp(plt.getp(cb.ax.axes, 'yticklabels'), color='black')

    fig.savefig('{}{}_test.png'.format(out_dir + '/', os.path.basename(img_name[:-4])))
    plt.show()
    #image = Image.open('{}{}_test.png'.format(out_dir + '/', os.path.basename(img_name[:-4])))
    #image.show()

    # Tidy up
    plt.close('all')


if __name__ == "__main__":
    workspace = '/home/arthur/Dropbox/career/e84/sample_data/'
    os.chdir(workspace)
    img_0 = 'GRD-3_2018152-2018181_GRFO_JPLEM_BA01_0600_LND_v03.tif'

    ul = (90.0, -180.0)
    lr = (-90.0, 180.0)

    # ul = (89, -179)
    # lr = (0, 0)

    # use gdal to read in data as np array
    ds = gdal.Open(os.path.join(workspace, img_0))

    data = ds.ReadAsArray()
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()

    ds = None

    # mask out the NoData
    data = np.ma.masked_array(data, data == -99999.0)

    do_plot(data,
            img_0,
            workspace,
            False,
            data.min(),
            data.max(),
            ul,
            lr,
            gt,
            proj)

