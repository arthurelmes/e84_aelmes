import matplotlib.pyplot as plt
import os
import numpy as np
from mpl_toolkits.basemap import Basemap
import osr
import gdal
import glob

# TODO maybe? break out rast_to_array to separate func


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


def make_all_plots(data_dir, ul, lr):
    data_dir = '/home/arthur/Dropbox/career/e84/sample_data/'
    out_dir = os.path.join(data_dir, 'png')
    os.chdir(data_dir)
    #img_0 = 'GRD-3_2018152-2018181_GRFO_JPLEM_BA01_0600_LND_v03.tif'

    # make output dir if it doesn't exist
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    # this will be user-entered via cmd
    # ul = (70, -130)
    # lr = (10, -20)

    # loop over all matching input files in workspace, create plot for each
    for file in glob.glob(os.path.join(data_dir, "*GRAC_JPLEM_BA01_0600_LND_v03.tif")):
        print(file)
        make_plot(file, out_dir, True, ul, lr)


def make_plot(img_file, o_dir, contrast_stretch, ul_coord, lr_coord):
    # use gdal to read in data as np array
    ds = gdal.Open(img_file)
    data = ds.ReadAsArray()
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()

    # mask out the NoData
    data = np.ma.masked_array(data, data == -99999.0)

    # parse geotransform details
    xres = gt[1]
    yres = gt[5]
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
    inproj.ImportFromWkt(proj)
    outproj = osr.SpatialReference()
    outproj.ImportFromProj4(m.proj4string)
    xx, yy = convert_xy(xy_source, inproj, outproj)

    # These to be implemented with any data with units that
    # aren't degrees, unlike the GRACE gridded data
    # col0, col1 = int((90 - ymax + xres * 0.5) / xres), \
    #              int((90 - ymin + xres * 0.5) / yres)
    # row0, row1 = int((180 + xmin) / gt[5]), \
    #              int((180 + xmax) / gt[5])

    # slice data based on user extent
    data = data[90 - ymax:90 - ymin, xmin + 180:xmax + 180]

    # plotting stuff
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    title = 'GRACE Land Water-Equivalent-Thickness Surface Mass Anomaly Rel 6.0 v 03 for dates: ' + img_file.split('/')[-1][6:21]
    ax.set_title(title, loc='center', pad=22, color='white')

    # for now, manually set min/max for colormap
    stretch_min = -0.4
    stretch_max = 0.4

    im = m.pcolormesh(xx,
                      yy,
                      data,
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


    fig.savefig('{a}{b}_{c}_{d}.png'.format(a=o_dir + '/',
                                            b=os.path.basename(img_file[:-4]),
                                            c=str(ul_coord[0]) + 'Deg_' + str(ul_coord[1]) + 'Deg_by',
                                            d=str(lr_coord[0]) + 'Deg_' + str(lr_coord[1]) + 'Deg'))
    ds = None


if __name__ == '__main__':
    workspace = '/home/arthur/Dropbox/career/e84/sample_data/'
    out_dir = os.path.join(workspace, 'png')
    os.chdir(workspace)

    # make output dir if it doesn't exist
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    # this will be user-entered via cmd
    ul = (-10, 100)
    lr = (-45, 160)

    # loop over all matching input files in workspace, create plot for each
    for file in glob.glob(os.path.join(workspace, "*GRAC_JPLEM_BA01_0600_LND_v03.tif")):
        print(file)
        make_plot(file, out_dir, True, ul, lr)
