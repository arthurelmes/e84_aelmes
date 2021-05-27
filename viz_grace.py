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

    # xmin = geotransform[0] - xres + 1
    # # temporarily hard coded ds.RasterXSize and ds.RasterYSize that multiply by xres, yres
    # xmax = geotransform[0] + (xres * 360)# - xres * 0.5
    # ymin = geotransform[3] + (yres * 180)# + yres * 0.5
    # ymax = geotransform[3] - yres - 1 #* 0.5

    # get the edge coordinates and add half the resolution
    # to go to center coordinates
    # xmin = gt[0] + xres * 0.5 - 0.5
    # xmax = gt[0] + (xres * 360) - xres * 0.5 + 0.5
    # ymin = gt[3] + (yres * 180) + yres * 0.5 + 0.5
    # ymax = gt[3] - yres * 0.5 - 0.5

    # get the edge coordinates and add half the resolution
    # to go to center coordinates
    xmin = gt[0] + xres * 0.5
    xmax = gt[0] + (xres * 360) - xres * 0.5
    ymin = gt[3] + (yres * 180) + yres * 0.5
    ymax = gt[3] - yres * 0.5

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

    print(f'lower left corner lat: {ymin}')
    print(f'upper right corner lat: {ymax}')
    print(f'lower left corner lon: {xmin}')
    print(f'upper right corner lon: {xmax}')
    print(f'central long is: {xmax + xmin}')

    m = Basemap(projection='robin',
                #lon_0=0,
                llcrnrlat=ymin+0.5,
                urcrnrlat=ymax-0.5,
                llcrnrlon=xmin-0.5,
                urcrnrlon=xmax+0.5,
                lon_0=0,
                resolution='c')


    # lon = (60.0, 10.0)
    # lat = (-140, -60)

    # make grid of xy coords for plotting
    xy_source = np.mgrid[ymax+yres:ymin:yres, xmin:xmax+xres:xres]

    inproj = osr.SpatialReference()
    inproj.ImportFromWkt(projection)

    outproj = osr.SpatialReference()
    outproj.ImportFromProj4(m.proj4string)

    xx, yy = convert_xy(xy_source, inproj, outproj)

    im = m.pcolormesh(xx, yy, data[:], alpha=0.9, cmap=plt.cm.RdBu, shading='auto')
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

    ul = (60.0, -140)
    lr = (10.0, -60.0)

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

