# Author: Arthur Elmes
# Date: 2021-05-26
# Purpose: Download GRACE Tellus data from JPL DAAC for

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


def dl_data(date_start, date_end):

    while date_end > date_start:
        date_start_doy = convert_date(date_start)
        date_next = date_start + relativedelta(months=1) - relativedelta(days=1)
        date_next_doy = convert_date(date_next)

        #base_url = 'https://podaac-tools.jpl.nasa.gov/drive/files/allData/tellus/L3/grace/land_mass/RL06/v03/JPL'
        base_url = 'https://podaac-tools.jpl.nasa.gov/drive/files/allData/tellus/L3/grace/land_mass/RL06/v03/JPL/'
        file_front = 'GRD-3_'
        file_date = '{x}-{y}'.format(x=date_start_doy, y=date_next_doy)
        file_end = '_GRAC_JPLEM_BA01_0600_LND_v03.tif'

        dl_url = base_url + file_front + file_date + file_end
        print(dl_url)
        response = requests.get(dl_url, stream=True, auth=('arthur.elmes', 'Yrkob5xXqc@CRW5TJn3'))

        # try:
        #     response = requests.get(dl_url, stream=True, auth=('arthur.elmes', 'Yrkob5xXqc@CRW5TJn3'))
        #     response.raise_for_status()
        # except requests.exceptions.HTTPError as err:
        #     continue #raise SystemExit(err)


        test_file_name = file_front + file_date + file_end

        if os.path.isfile(test_file_name):
            os.remove(test_file_name)

        with open(test_file_name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=16 * 1024):
                f.write(chunk)

        date_start = date_start + relativedelta(months=1)


def cleanup(dir):
    for file in glob.glob(os.path.join(dir, "*.tif")):
        if os.path.getsize(file) < 350:
            os.remove(file)


if __name__ == '__main__':
    workspace = '/home/arthur/Dropbox/career/e84/sample_data/'
    os.chdir(workspace)

    # TODO when users enter year-mm, add the day 1 of that month to construct complete date
    date_0 = datetime.strptime('2003-01-01', '%Y-%m-%d')
    date_1 = datetime.strptime('2021-12-01', '%Y-%m-%d')

    dl_data(date_0, date_1)

    # TODO this needs a real solution!
    cleanup(workspace)

