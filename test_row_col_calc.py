from osgeo import gdal
from osgeo import osr
import rasterio as rio

file_name = '/home/arthur/Dropbox/career/e84/sample_data/GRD-3_2015213-2015243_GRAC_JPLEM_BA01_0600_LND_v03.tif'
lat_0 = 0
lon_0 = 0

ds = gdal.Open(file_name)
gt = ds.GetGeoTransform()
xres = gt[1]
yres = gt[5]*-1
xmin = gt[0]
ymax = gt[3]

arr = ds.ReadAsArray()

ds = None

col = int((lon_0 - xmin) / xres)
row = int((ymax - lat_0) / yres)

print(f'Column, row from GDAL is : {col}, {row}')

with rio.open(file_name, 'r', driver='GTiff') as tif:
    row_r, col_r = tif.index(lon_0, lat_0)
    print(f'Column, row from rio is : {col_r}, {row_r}')

