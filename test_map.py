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

# mask out the NoData
data = np.ma.masked_array(data, data == -99999.0)

fig = plt.figure(figsize=(12, 6))
ax = plt.Axes(fig, [0, 0, 1, 1])

# parse geotransform details
xres = gt[1]
yres = gt[5]

# WORKING LIMITS get the edge coordinates and add half the resolution
# to go to center coordinates
# xmin = gt[0] + xres * 0.5
# xmax = gt[0] + (xres * ds.RasterXSize) - xres * 0.5
# ymin = gt[3] + (yres * ds.RasterYSize)+ yres * 0.5
# ymax = gt[3] - yres * 0.5

xmin = -180
xmax = 0
ymin = 10
ymax = 90

print(f'ymax is: {ymax}')
print(f'ymin is: {ymin}')
print(f'xmax is: {xmax}')
print(f'xmin is: {xmin}')

m = Basemap(projection='robin',
            llcrnrlat=0,
            urcrnrlat=80,
            llcrnrlon=-180,
            urcrnrlon=0,
            lon_0=0,
            resolution='c')

# make grid of xy coords for plotting
xy_source = np.mgrid[ymax:ymin-1:yres, xmin:xmax+1:xres]

print(xy_source)

inproj = osr.SpatialReference()
inproj.ImportFromWkt(proj)

outproj = osr.SpatialReference()
outproj.ImportFromProj4(m.proj4string)

xx, yy = convert_xy(xy_source, inproj, outproj)

col0, col1 = int((80 - gt[0] + xres * 0.5) / gt[1]), \
             int((-80 - gt[0] + xres * 0.5) / gt[1])
row0, row1 = int((10 - gt[3]) / gt[5]), \
             int((-10 - gt[3]) / gt[5])

#data = data[col1:col0, row0:row1]
data = data[10:90, 0:180]
# print(col0)
# print(col1)
# print(row0)
# print(row1)
print(data.shape)

extent = [xmin, xmax, ymin, ymax]

#.imshow(data, origin='upper', extent=extent)

m.pcolormesh(xx, yy, data, cmap=plt.cm.jet, shading='auto')

# annotate
m.drawcountries()
m.drawcoastlines(linewidth=.5)

plt.show()

ds = None
#
#
# fig2 = plt.figure(figsize=(12, 6))
# ax1 = plt.Axes(fig2, [0, 0, 1, 1])
#
# im1 = plt.pcolormesh(data, cmap=plt.cm.jet, shading='auto')
#
# plt.show()