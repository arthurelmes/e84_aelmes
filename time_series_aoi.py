"""This module creates several data visualizations to better understand image time series
data sets, such as GRACE Tellus groundwater anomaly data.
Author: Arthur Elmes
2021-05-28"""

import os, glob, sys, csv
import numpy as np
import pandas as pd
from datetime import datetime
from cycler import cycler
# import rasterio as rio
import matplotlib.pyplot as plt
# import matplotlib.ticker as ticker
from osgeo import gdal

from scipy import stats


def tif_to_np(tif_fname):
    # TODO check taht this change to gdal from rio didn't break it
    # with rio.open(tif_fname,
    #               'r',
    #               driver='GTiff') as tif:
    #     data_np = tif.read()
    ds = gdal.Open(tif_fname)
    data_np = ds.ReadAsArray()
    ds = None
    return data_np


def make_prod_list(in_dir, prdct, year, day):
    if 'GRD-3' in prdct:
        t_file_list = glob.glob(os.path.join(in_dir,
                                             '{prdct}*_{year}{day}*.tif'.format(prdct=prdct,
                                                                                day=day,
                                                                                year=year)))

    elif 'MCD' in prdct or 'VNP' in prdct or 'VJ1' in prdct:
        t_file_list = glob.glob(os.path.join(in_dir,
                                             '{prdct}*{year}{day}*.tif'.format(prdct=prdct,
                                                                               day=day,
                                                                               year=year)))
    elif 'LC08' in prdct:
        dt_string = str(year) + '-' + str(day)
        date_complete = datetime.strptime(dt_string, '%Y-%j')
        mm = date_complete.strftime('%m')
        dd = date_complete.strftime('%d')
        t_file_list = glob.glob(os.path.join(in_dir, '{prdct}*_{year}{month}{day}_*.h*'.format(prdct=prdct,
                                                                                               month=mm,
                                                                                               day=dd,
                                                                                               year=year)))
    else:
        print('Product type unknown! Please check that input is MCD, VNP, VJ1 or LC08.')
        sys.exit()

    return t_file_list


def extract_pixel_values(sites_dict, t_file_day):
    # Open with gdal
    ds = gdal.Open(t_file_day)
    gt = ds.GetGeoTransform()
    xres = float(gt[1])
    yres = float(gt[5]) * -1
    xmin = float(gt[0])
    ymax = float(gt[3])

    # get array and mask out nodata values
    tif = ds.ReadAsArray()
    tif_np_masked = np.ma.masked_array(tif, tif == -99999.0)

    # look through list of sample sites in csv to extract data for all
    rc_list = []
    for site in sites_dict.items():
        col = int(((float(site[1][1])) - xmin) / xres)
        row = int((ymax - float(site[1][0])) / yres)

        rc_list.append((row, col))

    # create and return a list of results for all sites at the given date
    results = []
    for rc in rc_list:
        try:
            result = tif_np_masked[rc]
            results.append(result)
        except IndexError:
            # print('No raster value for this pixel/date')
            results.append(np.nan)
    results = np.ma.filled(results, fill_value=np.nan)

    ds = None
    return results


def vert_stack_plot(years, nyears, strt_year, end_year, aoi_name, csv_path):
    ### Create plot with all years stacked vertically in a series of parallel time series graphs
    ncols = 1
    nrows = nyears + 1

    # create the plots
    fig_stack = plt.figure(figsize=(10, 15))
    axes = [fig_stack.add_subplot(nrows, ncols, r * ncols + c + 1) for r in range(0, nrows) for c in range(0, ncols)]

    yr = strt_year
    # add the data one year at a time
    for ax_stack in axes:
        col = str(yr)
        ax_stack.plot(years[col])
        #print(years[col].mean())
        ax_stack.set_xlim(80, 250)
        ax_stack.set_ylim(-0.005, 0.005)
        ax_stack.grid(b=True, which='major', color='LightGrey', linestyle='-')
        ax_stack.set_yticks([0.0])
        ax_stack.tick_params(
            axis='y',
            labelsize=5
                       )
        ax_stack.text(260, 0.33, str(yr), fontsize=8)
        # Remove ticks for everything but final year so no overlapping/messiness
        if yr != end_year:
            ax_stack.set_xticklabels([])
        # Add label to middle year
        if yr == round((end_year + strt_year) / 2, 0):
            ax_stack.set_ylabel('White sky Albedo')
        yr += 1

    # This only needs to apply to the last ax
    ax_stack.set_xlabel('DOY')
    ax_stack.set_ylim(-0.005, 0.005)
    fig_stack.suptitle(aoi_name, y=0.9)

    # Make subdir if needed and save fig
    file_path, file_name = os.path.split(csv_path)
    save_name = os.path.join(file_path, 'figs', aoi_name.replace(' ', '_') +
                             '_white_sky_time_series_vert_stack.png')
    if not os.path.isdir(os.path.join(file_path, 'figs')):
        os.mkdir(os.path.join(file_path, 'figs'))
    plt.savefig(save_name, dpi=300, bbox_inches='tight')


def box_plot(years, aoi_name, csv_path):
    # Quck boxplot for each year
    overall_mean = round(years.stack().mean(), 2)
    overall_min = round(years.stack().min(), 2)
    overall_max = round(years.stack().max(), 2)
    data_to_plot = years.to_numpy()

    # Filter out the NaNs, otherwise the boxplot is unhappy
    # https://stackoverflow.com/questions/44305873/how-to-deal-with-nan-value-when-plot-boxplot-using-python
    mask = ~np.isnan(data_to_plot)
    filtered_data = [d[m] for d, m in zip(data_to_plot.T, mask.T)]

    # Create a figure instance
    fig_box = plt.figure(1, figsize=(9, 6))
    fig_box.suptitle(aoi_name, color='w')
    fig_box.set_facecolor('black')

    # Create an axis instance
    ax_box = fig_box.add_subplot(111)
    ax_box.set_facecolor('black')

    tick_labels = years.columns

    ax_box.tick_params(
        axis='x',
        labelsize=8,
        labelrotation=45,
        color='grey')

    ax_box.tick_params(
        axis='y',
        labelsize=8,
        color='grey')

    ax_box.set_ylim(overall_min*2,
                    overall_max*2)
    ax_box.grid(b=True,
                which='major',
                color='LightGrey',
                linestyle='-')

    ax_box.spines['bottom'].set_color('white')
    ax_box.spines['left'].set_color('white')
    ax_box.spines['top'].set_color('white')
    ax_box.spines['right'].set_color('white')

    ax_box.set_yticks([overall_min, overall_mean, overall_max])
    ax_box.set_yticklabels([overall_min, overall_mean, overall_max],
                           color='white')

    ax_box.set_ylabel('Grace Anomalies',
                      color='white')

    ax_box.set_xlabel('Year',
                      color='white')

    # Create the boxplot
    bp = ax_box.boxplot(filtered_data,
                        boxprops=dict(color='lightgray', linewidth=1.5),
                        whiskerprops=dict(color='white'),
                        flierprops=dict(markerfacecolor='white', fillstyle=None, marker='.'),
                        medianprops=dict(color='orange'),
                        capprops=dict(color='orange'),
                        showmeans=True,
                        labels=tick_labels)

    ax_box.tick_params(axis='x', colors='white')

    ax_box.grid(b=True,
                which='major',
                color='grey',
                linestyle='--',
                linewidth='0.7')

    # Make subdir if needed and save fig
    file_path, file_name = os.path.split(csv_path)
    save_name = os.path.join(file_path, 'figs', aoi_name.replace(' ', '_') + '_boxplot.png')
    if not os.path.isdir(os.path.join(file_path, 'figs')):
        os.mkdir(os.path.join(file_path, 'figs'))
    plt.savefig(save_name, dpi=300, bbox_inches='tight')


def overpost_all_plot(years, aoi_name, csv_path):
    ### Create a plot where all the years are combined in a single graph
    fig_comb = plt.figure(figsize=(10, 5))
    fig_comb.set_facecolor('black')
    ax_comb = fig_comb.add_subplot(111)
    ax_comb.set_facecolor('black')

    # Set colormap and cycler to automatically apply colors to years plotted below
    n = len(years.columns)
    color = plt.cm.plasma(np.linspace(0, 1, n))
    c = cycler('color', color)
    plt.rc('axes', prop_cycle=c)
    plt.rc('lines', linewidth=0.5)
    ax_comb.set_prop_cycle(c)

    min_display = 0
    max_display = 0

    data_climo = pd.DataFrame()
    data_climo['mean'] = years.mean(axis=1)

    # Add each year to same plot -- for some reason a 'undefined' values comes back first, so
    # check for year part first
    for ycol in years.columns:
        if '20' in ycol:
            if years[ycol].max() > max_display:
                max_display = years[ycol].max()
            if years[ycol].min() < min_display:
                min_display = years[ycol].min()

            s1mask = np.isfinite(years[ycol])
            ax_comb.plot(years.index[s1mask],
                         years[ycol][s1mask],
                         label=str(ycol),
                         marker='o',
                         ms=4,
                         linestyle='dashed')

    print(data_climo.head())
    s2mask = np.isfinite(data_climo['mean'])
    ax_comb.plot(data_climo.index[s2mask],
                 data_climo['mean'][s2mask],
                 label='Mean for period',
                 marker='o',
                 ms=4,
                 linestyle='dashed',
                 color='white'
                 )

    # auto-adjust range
    min_display *= 2
    max_display *= 2

    ax_comb.tick_params(colors='white')
    ax_comb.set_xlabel('DOY', color='white')
    ax_comb.set_ylabel('GRACE Anomaly', color='white')
    ax_comb.set_ylim(min_display, max_display)
    fig_comb.suptitle(aoi_name, color='white')
    lgnd = plt.legend(ncol=4, loc='lower left', fontsize=10)

    # to set legend transparency
    # TODO not working
    for lh in lgnd.legendHandles:
        lh._legmarker.set_alpha(0)

    # Save fig in figs subdir, making the subdir if needed
    file_path, file_name = os.path.split(csv_path)
    save_name = os.path.join(file_path, 'figs', aoi_name.replace(' ', '_') + 'grace_time_series_overpost_stack.png')
    if not os.path.isdir(os.path.join(file_path, 'figs')):
        os.mkdir(os.path.join(file_path, 'figs'))
    plt.savefig(save_name, dpi=300, bbox_inches='tight', facecolor='black')
    plt.close()


def check_leap(year):
    leap_status = False
    year = int(year)
    if (year % 4) == 0:
        if (year % 100) == 0:
            if (year % 400) == 0:
                leap_status = True
            else:
                leap_status = False
        else:
            leap_status = True
    else:
        leap_status = False

    return leap_status


def convert_to_doy(doy):
    doy = int(doy)
    if doy < 10:
        return '00' + str(doy)
    elif 10 <= doy < 100:
        return '0' + str(doy)
    elif doy >= 100:
        return str(doy)
    else:
        print('Oops, this is not a DOY!')
        sys.exit(1)


def make_time_series_plots(base_dir, prdct, aoi_name, start_date, end_date, csv_name):
    fig_dir = os.path.join(base_dir, 'time_series')

    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)

    years = [year for year in range(start_date.year, end_date.year+1)]

    dt_indx = pd.date_range(start_date, end_date)
    strt_year = dt_indx[0].to_pydatetime().year
    end_year = dt_indx[-1].to_pydatetime().year

    # var never gets used?
    nyears = end_year - strt_year

    sites_csv_input = os.path.join(base_dir, csv_name)
    sites_dict = {}
    with open(sites_csv_input, mode='r') as sites_csv:
        reader = csv.reader(sites_csv)
        for row in reader:
            key = row[0]
            sites_dict[key] = row[1:]

    # Loop through the years provided, and extract the pixel values at the provided coordinates. Outputs CSV and figs.
    smpl_results_df = pd.DataFrame(columns=['yyyyddd', 'value'])
    for year in years:
        print(f"extracting values for year: {year}")
        doy_list = []
        if check_leap(year):
            for i in range(1, 367):
                doy_list.append(convert_to_doy(i))
        else:
            for i in range(1, 366):
                doy_list.append(convert_to_doy(i))

        # Loop through each site and extract the pixel values
        for day in doy_list:
            # Open the ONLY BAND IN THE TIF! Cannot currently deal with multiband tifs
            t_file_list = make_prod_list(base_dir, prdct, year, day)

            file_name = '{in_dir}/{prdct}*_{year}{day}*.tif'.format(in_dir=base_dir,
                                                                        prdct=prdct,
                                                                        day=day,
                                                                        year=year)

            # See if there is a raster for the date, if not use a fill value for the graph
            if len(t_file_list) == 0:
                # print('File not found: ' + file_name)
                pixel_values = [np.nan] * len(sites_dict)
                new_row = {'yyyyddd': str(year)+str(day), 'value': pixel_values[0]}
                smpl_results_df = smpl_results_df.append(new_row, ignore_index=True)
            elif len(t_file_list) > 1:
                print('Multiple matching files found for same date! Please remove one.')
                sys.exit(1)
            else:
                # print('Found file: ' + file_name)
                t_file_day = t_file_list[0]
                # Extract pixel values and append to dataframe
                try:
                    pixel_values = extract_pixel_values(sites_dict, t_file_day)

                    new_row = {'yyyyddd': str(year)+str(day), 'value': pixel_values[0]}
                    smpl_results_df = smpl_results_df.append(new_row, ignore_index=True)
                except:
                    # print('Warning! Pixel out of raster boundaries!')
                    pixel_values = [np.nan] * len(sites_dict)

                    new_row = {'yyyyddd': str(year)+str(day), 'value': pixel_values[0]}
                    smpl_results_df = smpl_results_df.append(new_row, ignore_index=True)

    # Export data to csv
    os.chdir(fig_dir)
    file_name = sites_csv_input.split(sep='/')[-1]
    output_name = str(fig_dir + '/' + file_name[:-4] + '_extracted_values')
    csv_name = str(output_name + '_' + prdct + '_' + str(start_date) + '_' + str(end_date) + '.csv')
    print('writing csv: ' + csv_name)
    smpl_results_df.to_csv(csv_name, index=False)

    # rejig the date
    smpl_results_df['date'] = pd.to_datetime(smpl_results_df['yyyyddd'],
                                             format='%Y%j')
    smpl_results_df.set_index('date', inplace=True)
    smpl_results_df.drop(['yyyyddd'], axis=1)
    smpl_results_df = smpl_results_df.groupby('date').mean()

    # prep the dataset to be split into columns, one per year
    series = smpl_results_df.squeeze()
    series = series.reindex(dt_indx, fill_value=np.NaN)
    groups = series.groupby(pd.Grouper(freq='A'))
    years_df = pd.DataFrame()

    for name, group in groups:
        if len(group.values) > 1:
            years_df[name.year] = group.values[:364]

    # drop any years that have no data at all
    years_df = years_df.dropna(axis=1, how='all')

    # make columns into strings for easier plot labeling
    years_df.columns = years_df.columns.astype(str)

    # make the plots
    # vert_stack_plot(years_df, nyears, strt_year, end_year, aoi_name, sites_csv_input)
    overpost_all_plot(years_df, aoi_name, sites_csv_input)
    box_plot(years_df, aoi_name, sites_csv_input)


if __name__ == '__main__':
    base_dir = '/home/arthur/Dropbox/career/e84/sample_data/'
    prdct = "GRD-3"
    aoi_name = "TESTING"
    start_date = datetime.strptime('2010-01-01', '%Y-%m-%d')
    end_date = datetime.strptime('2015-01-01', '%Y-%m-%d')
    csv_name = os.path.join(base_dir, 'sample.csv')
    make_time_series_plots(base_dir, prdct, aoi_name, start_date, end_date, csv_name)
