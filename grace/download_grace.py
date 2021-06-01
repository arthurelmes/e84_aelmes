""" This module downloads GRACE Tellus data from JPL DAAC for visualization and anaylsis.
Author: Arthur Elmes
Date: 2021-05-26"""

import requests
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import glob

import sys


def convert_date(in_date):
    #doy = datetime.strptime(in_date, '%Y-%m-%d')
    doy = datetime.strftime(in_date, '%Y%j')
    return doy


def convert_doy(doy):
    date_complete = datetime.strptime(doy, '%Y%j').date()
    date_complete = date_complete.strftime('%m/%d/%Y')
    return date_complete


def dl_data(dl_dir, date_start, date_end):
    vers = 'v03'
    os.chdir(dl_dir)
    base_url_grac = f'https://podaac-tools.jpl.nasa.gov/drive/files/allData/tellus/L3/grace/land_mass/RL06/{vers}/JPL/'
    base_url_grfo = f'https://podaac-tools.jpl.nasa.gov/drive/files/allData/tellus/L3/gracefo/land_mass/RL06/{vers}/JPL/'
    file_front = 'GRD-3_'

    while date_end > date_start:
        date_start_doy = convert_date(date_start)
        date_next = date_start + relativedelta(months=1) - relativedelta(days=1)
        date_next_doy = convert_date(date_next)

        file_date = '{x}-{y}'.format(x=date_start_doy, y=date_next_doy)
        file_end_grac = f'_GRAC_JPLEM_BA01_0600_LND_{vers}.tif'
        file_end_gfro = f'_GRFO_JPLEM_BA01_0600_LND_{vers}.tif'
        dl_url_grac = base_url_grac + file_front + file_date + file_end_grac
        dl_url_grfo = base_url_grfo + file_front + file_date + file_end_gfro
        print(f'Downloading {dl_url_grac}')
        print(f'Downloading {dl_url_grfo}')

        # note the API download credentials
        response_grac = requests.get(dl_url_grac, stream=True, auth=('arthur.elmes', 'Yrkob5xXqc@CRW5TJn3'))
        response_grfo = requests.get(dl_url_grfo, stream=True, auth=('arthur.elmes', 'Yrkob5xXqc@CRW5TJn3'))

        test_file_name_grac = file_front + file_date + file_end_grac
        test_file_name_grfo = file_front + file_date + file_end_gfro

        if os.path.isfile(test_file_name_grfo):
            os.remove(test_file_name_grfo)
        if os.path.isfile(test_file_name_grac):
            os.remove(test_file_name_grac)

        with open(test_file_name_grac, 'wb') as f:
            for chunk in response_grac.iter_content(chunk_size=16 * 1024):
                f.write(chunk)

        with open(test_file_name_grfo, 'wb') as f:
            for chunk in response_grfo.iter_content(chunk_size=16 * 1024):
                f.write(chunk)

        date_start = date_start + relativedelta(months=1)

    # TODO this needs a real solution!
    cleanup(dl_dir)


def cleanup(dir):
    for file in glob.glob(os.path.join(dir, "*.tif")):
        if os.path.getsize(file) < 350:
            os.remove(file)


if __name__ == '__main__':
    workspace = '/home/arthur/Dropbox/grace_data/'
    os.chdir(workspace)

    date_0 = datetime.strptime('2002-01-01', '%Y-%m-%d')
    date_1 = datetime.strptime('2020-12-01', '%Y-%m-%d')

    dl_data(workspace, date_0, date_1)

    # TODO this needs a real solution!
    cleanup(workspace)

