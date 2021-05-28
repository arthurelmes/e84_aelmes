# Use pysimplegui to take in user inputs, do basic output

import PySimpleGUI as sg
import os.path
import datetime
import sys

# modules in this package
import time_series_aoi
import download_grace
import make_gif
import viz_grace

if __name__ == '__main__':
    base_dir = '/home/arthur/Dropbox/career/e84/sample_data/'
    # ul_coord = (70, -130)
    # lr_coord = (10, -20)

    # example gui from https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Button_Func_Calls.py
    def run_download(start, end, dl_dir):
        print('Now downloading GRACE images for time period.')
        download_grace.dl_data(dl_dir, start, end)

    def run_vis(ul, lr, workspace):
        print('Now creating map of AOI.')
        viz_grace.make_all_plots(workspace, ul, lr)
        make_gif.make_gif(png_dir=os.path.join(workspace, 'png/'),
                          gif_dir=os.path.join(workspace, 'gif/'))


    def run_plots(start, end, workspace):
        print('Now creating time series plots for AOI.')
        time_series_aoi.make_time_series_plots(base_dir=workspace,
                                               prdct='GRD-3',
                                               aoi_name='Alexandria, VA',
                                               start_date=start,
                                               end_date=end,
                                               csv_name='sample.csv')

    # set the layout bits
    layout = [[sg.Text('Welcome to the GRACE Tellus Data Viz Tool!')],
              [sg.Button('Download Time Series', key='-Download-'),
               sg.Button('Create AOI Maps', key='-Map-'),
               sg.Button('Time Series Button', key='-Time-')],
              [sg.Text('Start Date in YYYY-MM-DD', size=(25, 1)),
               sg.InputText(key='-StartDate-', size=(15, 1))],
              [sg.Text('End Date in YYYY-MM-DD', size=(25, 1)),
               sg.InputText(key='-EndDate-', size=(15, 1))],
              [sg.Text('Upper left corner latitude', size=(30, 1)),
               sg.InputText(key='-ULLAT-', size=(15, 1))],
              [sg.Text('Upper left corner longitude', size=(30, 1)),
               sg.InputText(key='-ULLON-', size=(15, 1))],
              [sg.Text('Lower right corner latitude', size=(30, 1)),
               sg.InputText(key='-LRLAT-', size=(15, 1))],
              [sg.Text('Lower right corner longitude', size=(30, 1)),
               sg.InputText(key='-LRLON-', size=(15, 1))],
              [sg.Button('Set date and AOI', key='-Submit-')]
              ]

    # make the window obj
    window = sg.Window('Test button functions', layout)

    # the event loop
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == '-Download-':
            run_download(date_start, date_end, base_dir)
        elif event == '-Map-':
            run_vis(ul_coord, lr_coord, base_dir)
        elif event == '-Time-':
            run_plots(date_start, date_end, base_dir)
        elif event == '-Submit-':
            date_start = datetime.datetime.strptime(values['-StartDate-'], '%Y-%m-%d')
            date_end = datetime.datetime.strptime(values['-EndDate-'], '%Y-%m-%d')
            ul_coord = (int(values['-ULLAT-']), int(values['-ULLON-']))
            lr_coord = (int(values['-LRLAT-']), int(values['-LRLON-']))
            print(date_start)
            print(date_end)
            print(ul_coord)
            print(lr_coord)

    window.close()
