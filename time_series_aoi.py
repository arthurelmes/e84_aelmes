
import os, glob, sys, pyproj, csv, statistics
from argparse import ArgumentParser
import numpy as np
import pandas as pd

from datetime import datetime
import seaborn as sns
import rasterio as rio
import timeit
from cycler import cycler
import matplotlib as mpl
import matplotlib.pyplot as plt


def tif_to_np(tif_fname):
    with rio.open(tif_fname,
                  'r',
                  driver='GTiff') as tif:
        data_np = tif.read()
        return data_np


def make_prod_list(in_dir, prdct, year, day):
    if 'GRD-3' in prdct:
        t_file_list = glob.glob(os.path.join(in_dir,
                                             '{prdct}*_{year}{day:03d}*.tif'.format(prdct=prdct,
                                                                                    day=day,
                                                                                    year=year)))
    elif 'MCD' in prdct or 'VNP' in prdct or 'VJ1' in prdct:
        t_file_list = glob.glob(os.path.join(in_dir,
                                             '{prdct}*{year}{day:03d}*.tif'.format(prdct=prdct,
                                                                                   day=day, year=year)))
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

    #print('{prdct}*{year}{day:03d}*.tif'.format(prdct=prdct, day=day, year=year))
    return t_file_list


def extract_pixel_values(sites_dict, t_file_day):
    # Open tifs with rasterio

    with rio.open(t_file_day,
                  'r',
                  driver='GTiff') as tif:

        rc_list = []
        for site in sites_dict.items():
            col, row = tif.index(float(site[1][1]), float(site[1][0]))
            rc_list.append((col, row))

        tif_np = tif.read(1)
        tif_np_masked = np.ma.masked_array(tif_np, tif_np == 32767)

        results = []
        for rc in rc_list:
            try:
                result = tif_np_masked[rc]
                results.append(result)
            except IndexError:
                #print('No raster value for this pixel/date')
                results.append(np.nan)
    results = np.ma.filled(results, fill_value=np.nan)
    return results


def year_scatter_plot(year, smpl_results_df, fig_dir, prdct, sites_dict):
    # This is for the the monthly averages

    sns.set_style('darkgrid')
    smpl_results_df.rename(columns={0: 'id_0', 1: 'id_1', 2: 'id_2', 3: 'id_3', 4: 'id_4'}, inplace=True)

    for site in smpl_results_df.columns.tolist():
        if site != 'doy':
            # Create a seaborn scatterplot (or regplot for now, small differences)
            sct = sns.scatterplot(x='doy', y=site, data=smpl_results_df)

            # sct = sns.regplot(x='doy', y=site, data=smpl_results_df, marker='o', label='sw ' ,
            #                   fit_reg=False, scatter_kws={'color':'darkblue', 'alpha':0.3,'s':20})

            sct.set_ylim(-0.00005, 0.00005)
            sct.set_xlim(1, 366)
            sct.legend(loc='best')

            # Access the figure, add title
            plt_name = str(str(year) + ' ' + prdct)
            plt.title(plt_name)
            plt.show()

            plt_name = plt_name.replace(' ', '_') + '_' + str(site)

            # Save each plot to figs dir
            print('Saving plot to: ' + '{fig_dir}/{plt_name}.png'.format(fig_dir=fig_dir, plt_name=plt_name))
            plt.savefig('{fig_dir}/{plt_name}.png'.format(fig_dir=fig_dir, plt_name=plt_name))
            plt.clf()
            sys.exit()


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
        ax_stack.set_xlim(80, 250)
        ax_stack.set_ylim(0.0, 1.0)
        ax_stack.grid(b=True, which='major', color='LightGrey', linestyle='-')
        ax_stack.set_yticks([0.5])
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
    ax_stack.set_ylim(0.0, 1.0)
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
    overall_mean = years.stack().mean()
    data_to_plot = years.to_numpy()

    # Filter out the NaNs, otherwise the boxplot is unhappy
    # https://stackoverflow.com/questions/44305873/how-to-deal-with-nan-value-when-plot-boxplot-using-python
    mask = ~np.isnan(data_to_plot)
    filtered_data = [d[m] for d, m in zip(data_to_plot.T, mask.T)]

    # Create a figure instance
    fig_box = plt.figure(1, figsize=(9, 6))
    fig_box.suptitle(aoi_name)

    # Create an axis instance
    ax_box = fig_box.add_subplot(111)
    ax_box.set_xticklabels(list(years.columns))
    ax_box.tick_params(
        axis='x',
        labelsize=5,
        labelrotation=45
                       )
    ax_box.set_ylim(0.0, 1.0)
    ax_box.grid(b=True, which='major', color='LightGrey', linestyle='-')
    ax_box.set_yticks([overall_mean])
    ax_box.tick_params(
        axis='y',
        labelsize=5
                   )
    ax_box.set_ylabel('White sky Albedo (Overall Mean)')
    outlier_marker = dict(markerfacecolor='black', fillstyle=None, marker='.')

    # print(filtered_data[0].shape)
    # data_years = np.empty(filtered_data[0].shape)
    # for i in filtered_data:
    #     np.concatenate((data_years, i))
    # print(data_years.shape)
    data_climo = np.concatenate((filtered_data[0], filtered_data[1]))

    print(len(filtered_data))

    data_2019 = filtered_data[19]
    i = 0

    # Store t-test of each year vs 2019 in txt file
    stats_txt_name = csv_path[:-4] + '_t_stats_vs_2019.txt'
    stats_txt = open(stats_txt_name, 'w')

    for dst in filtered_data:
        data_year = filtered_data[i]
        #print('T test results for year {x}'.format(x=str(i+2000)))
        stats_txt.write('T test results for year {x}'.format(x=str(i+2000)) + '\n')
        #print(stats.ttest_ind(data_year, data_2019))
        stats_txt.write(str(stats.ttest_ind(data_year, data_2019)) + '\n')
        #print('Mean of year {x} is {y}'.format(x=str(i+2000), y=data_year.mean()))
        stats_txt.write('Mean of year {x} is {y}'.format(x=str(i+2000), y=data_year.mean()) + '\n')
        i += 1

    stats_txt.close()

    # Create the boxplot
    bp = ax_box.boxplot(filtered_data, flierprops=outlier_marker)

    # Make subdir if needed and save fig
    file_path, file_name = os.path.split(csv_path)
    save_name = os.path.join(file_path, 'figs', aoi_name.replace(' ', '_') + '_boxplot.png')
    if not os.path.isdir(os.path.join(file_path, 'figs')):
        os.mkdir(os.path.join(file_path, 'figs'))
    plt.savefig(save_name, dpi=300, bbox_inches='tight')


def overpost_all_plot(years, aoi_name, csv_path):
    ### Create a plot where all the years are combined in a single graph

    fig_comb = plt.figure(figsize=(10, 5))
    ax_comb = fig_comb.add_subplot(111)

    # Set colormap and cycler to automatically apply colors to years plotted below
    n = len(years.columns)
    color = plt.cm.hsv(np.linspace(0, 1, n))
    mpl.rcParams['axes.prop_cycle'] = cycler('color', color)

    # Add each year to same plot -- for some reason a 'undefined' values comes back first, so
    # check for year part first
    for ycol in years.columns:
        if '20' in ycol:
            ax_comb.plot(years.index, years[ycol], label=str(ycol), alpha=0.2)

    ax_comb.plot(years.index, years['2019'], label='2019 Emphasis', color='orange')
    ax_comb.set_xlabel('DOY')
    ax_comb.set_ylabel('White Sky Albedo')
    ax_comb.set_ylim(0.0, 1.0)
    fig_comb.suptitle(aoi_name)
    plt.legend(ncol=4, loc='lower left', fontsize=10)

    # Save fig in figs subdir, making the subdir if needed
    file_path, file_name = os.path.split(csv_path)
    save_name = os.path.join(file_path, 'figs', aoi_name.replace(' ', '_') + 'white_sky_time_series_overpost_stack.png')
    if not os.path.isdir(os.path.join(file_path, 'figs')):
        os.mkdir(os.path.join(file_path, 'figs'))
    plt.savefig(save_name, dpi=300, bbox_inches='tight')


def year_vs_avg_plot(years, aoi_name, csv_path):
    #### Now plot 2019 vs the 2000 - 2018 avg

    # Calculate stats
    cols = years.loc[:, "2000":"2020"]
    years['base_mean'] = cols.mean(axis=1)
    years['base_sd'] = cols.std(axis=1)

    #TODO same issue here as in the anomaly version of this plot -- why the last value jump?

    fig_comb_mean = plt.figure(figsize=(10, 5))
    ax_comb_mean = fig_comb_mean.add_subplot(111)
    ax_comb_mean.plot(years.index, years['2010'], label='2010', color='chartreuse')
    ax_comb_mean.plot(years.index, years['2012'], label='2012', color='yellow')
    ax_comb_mean.plot(years.index, years['2014'], label='2014', color='green')
    ax_comb_mean.plot(years.index, years['2019'], label='2019', color='darkorange')
    ax_comb_mean.plot(years.index, years['2020'], label='2020', color='firebrick')
    ax_comb_mean.plot(years.index[:-85], years['base_mean'][:-85], label='2000-2020 Mean +/- 1 SD', color='slateblue',
                      alpha=0.5)
    plt.fill_between(years.index[:-85], years['base_mean'][:-85] - years['base_sd'][:-85], years['base_mean'][:-85] +
                     years['base_sd'][:-85], color='lightgrey')
    ax_comb_mean.set_ylim(0.0, 1.0)
    ax_comb_mean.set_ylabel('White Sky Albedo')
    ax_comb_mean.set_xlabel('DOY')
    plt.legend(loc='lower left')

    fig_comb_mean.suptitle(aoi_name)

    file_path, file_name = os.path.split(csv_path)
    save_name = os.path.join(file_path, 'figs', aoi_name.replace(' ', '_') + '_2000-2020_mean_' +
                             '_white_sky_time_series_2019_vs_mean.png')
    if not os.path.isdir(os.path.join(file_path, 'figs')):
        os.mkdir(os.path.join(file_path, 'figs'))
    plt.savefig(save_name, dpi=300, bbox_inches='tight')
    

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


def main():
    # CLI args
    parser = ArgumentParser()
    # TODO maybe delete years, and just plot all available data
    parser.add_argument('-y', '--years', dest='years', help='Years to extract data for.', metavar='YEARS')

    parser.add_argument('-d', '--input-dir', dest='base_dir',
                        help='Base directory containing sample and dir of imagery data called the product name'
                             ', e.g. ../MCD43A3/',
                        metavar='IN_DIR')
    parser.add_argument('-s', '--sites', dest='sites_csv_fname', help='CSV with no headings containing smpls. '+\
                        'must look like: id,lat,long',
                        metavar='SITES')
    parser.add_argument('-p', '--product', dest='prdct', help='Imagery product to be input, e.g. GRACE.',
                        metavar='PRODUCT')
    args = parser.parse_args()

    #TODO to avoid egregious geolocation errors, I should require the csv to have headers (currently it cannot)
    #and the headers should be id,lat,long, so I can check that the latitude and longitude cols are correct by
    #their name in the csv

    # for dev just hardcode
    # prdct = args.prdct
    # base_dir = args.base_dir
    # fig_dir = os.path.join(base_dir, 'time_series')

    prdct = 'GRD-3'
    base_dir = '/home/arthur/Dropbox/career/e84/sample_data/'
    fig_dir = os.path.join(base_dir, 'time_series')

    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)

    #years = [args.years]
    years = [2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2010, 2011, 2012, 2013, 2014, 2015, 2016,
             2017, 2018, 2019, 2020]

    # TODO define these
    aoi_name = 'DC'
    dt_indx = pd.date_range('2002-01-01', '2020-12-31')
    strt_year = dt_indx[0].to_pydatetime().year
    end_year = dt_indx[-1].to_pydatetime().year
    nyears = end_year - strt_year

    #sites_csv_input = os.path.join(base_dir, args.sites_csv_fname)
    sites_csv_input = os.path.join(base_dir, 'sample.csv')
    sites_dict = {}
    with open(sites_csv_input, mode='r') as sites_csv:
        reader = csv.reader(sites_csv)
        for row in reader:
            key = row[0]
            sites_dict[key] = row[1:]

    # Loop through the years provided, and extract the pixel values at the provided coordinates. Outputs CSV and figs.
    for year in years:
        print("extracting values for year:")
        print(year)
        doy_list = []
        if check_leap(year):
            for i in range(1, 367):
                doy_list.append(i)
        else:
            for i in range(1, 366):
                doy_list.append(i)

        # Make a blank pandas dataframe that results will be appended to,
        # and start it off with all possible doys (366)
        year_smpl_cmb_df = pd.DataFrame(doy_list, columns=['doy'])
        # Loop through each site and extract the pixel values

        # Create empty array for mean
        tif_mean = []
        for day in doy_list:
            # Open the ONLY BAND IN THE TIF! Cannot currently deal with multiband tifs
            t_file_list = make_prod_list(base_dir, prdct, year, day)
            file_name = '{in_dir}/{prdct}*_{year}{day:03d}*.tif'.format(in_dir=base_dir,
                                                                       prdct=prdct,
                                                                       day=day,
                                                                       year=year)

            # See if there is a raster for the date, if not use a fill value for the graph
            if len(t_file_list) == 0:
                # print('File not found: ' + file_name)
                pixel_values = [np.nan] * len(sites_dict)
            elif len(t_file_list) > 1:
                print('Multiple matching files found for same date! Please remove one.')
                sys.exit()
            else:
                # print('Found file: ' + file_name)
                t_file_day = t_file_list[0]
                # Extract pixel values and append to dataframe
                try:
                    pixel_values = extract_pixel_values(sites_dict, t_file_day)
                    # print(pixel_values)
                except:
                    # print('Warning! Pixel out of raster boundaries!')
                    pixel_values = [np.nan] * len(sites_dict)
                #print(pixel_values)
            tif_mean.append(pixel_values)

        smpl_results_df = pd.DataFrame(tif_mean)
        smpl_results_df = smpl_results_df * 0.001
        doy_list_year = doy_list

        i = 0
        for doy in doy_list_year:
            doy_list_year[i] = str(year) + convert_to_doy(doy)
            i += 1

        smpl_results_df['yyyyddd'] = doy_list

        # just moving some cols around
        cols = smpl_results_df.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        smpl_results_df = smpl_results_df[cols]

        # get the calendar dates back
        smpl_results_df['date'] = pd.to_datetime(smpl_results_df['yyyyddd'],
                                                    format='%Y%j')
        smpl_results_df.set_index('date', inplace=True)
        smpl_results_df = smpl_results_df.groupby('date').mean()

        series = smpl_results_df.squeeze()
        series = series.reindex(dt_indx, fill_value=np.NaN)
        groups = series.groupby(pd.Grouper(freq='A'))
        years = pd.DataFrame()



        # This is how the dataframe is set up with each column being a year of data, each row a doy
        for name, group in groups:
            years[name.year] = group.values[:364]
            print(name.year, group.values[:364])

        sys.exit()
        vert_stack_plot(years, nyears, strt_year, end_year, aoi_name, sites_csv_input)


        # Do plotting and save output PER YEAR (individual csv per year)
        year_scatter_plot(year, smpl_results_df, fig_dir, prdct, sites_dict)

        # Export data to csv
        os.chdir(fig_dir)
        file_name = sites_csv_input.split(sep='/')[-1]
        output_name = str(fig_dir + '/' + file_name[:-4] + '_extracted_values')
        csv_name = str(output_name + '_' + prdct + '_' + str(year) + '.csv')
        print('writing csv: ' + csv_name)
        smpl_results_df.to_csv(csv_name, index=False)


if __name__ == '__main__':
    main()
