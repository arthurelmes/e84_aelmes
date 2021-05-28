# Use pysimplegui to take in user inputs, do basic output

import PySimpleGUI as sg
import os.path
import datetime

# modules in this package
import time_series_aoi
import download_grace
import make_gif
import viz_grace

if __name__ == '__main__':
    ul = (70, -130)
    lr = (10, -20)
    date_start = datetime.datetime.strptime('2015-01-01', '%Y-%m-%d')
    date_end = datetime.datetime.strptime('2016-12-31', '%Y-%m-%d')
    base_dir = '/home/arthur/Dropbox/career/e84/sample_data/'

    #download_grace.dl_data(base_dir, date_start, date_end)
    # viz_grace.make_all_plots(base_dir, ul, lr)
    make_gif.make_gif(png_dir=os.path.join(base_dir, 'png/'),
                      gif_dir=os.path.join(base_dir, 'gif/'))
    # time_series_aoi.make_time_series_plots(base_dir=base_dir,
    #                                        prdct='GRD-3',
    #                                        aoi_name='Alexandria, VA',
    #                                        start_date=date_start,
    #                                        end_date=date_end,
    #                                        csv_name='sample.csv')

# # first the window layout in 2 cols
# file_list_column = [
#     [
#         sg.Text('Image Folder'),
#         sg.In(size=(25, 1), enable_events=True, key='-FOLDER-'),
#         sg.FolderBrowse(),
#     ],
#     [
#         sg.Listbox(
#             values=[], enable_events=True, size=(40, 20), key='-FILE LIST-'
#         )
#     ],
# ]
#
# # for now we only show the name of the file that was chosen
# image_viewer_column = [
#     [sg.Text('Choose an image from the list on the left:')],
#     [sg.Text(size=(40, 1), key='-TOUT-')],
#     [sg.Image(key='-IMAGE-')],
# ]
#
# # put the cols together to form complete layout
# layout = [
#     [
#         sg.Column(file_list_column),
#         sg.VSeparator(),
#         sg.Column(image_viewer_column),
#     ]
# ]
#
# # create the window obj
# window = sg.Window('Image Viewer', layout)
#
# # run the event loop for user input
# while True:
#     event, values = window.read()
#     if event == 'Exit' or event == sg.WIN_CLOSED:
#         break
#
#     # folder name was filled in, make a list of files in that folder
#     if event == '-FOLDER-':
#         folder = values['-FOLDER-']
#         try:
#             # get a list of files in folder
#             file_list = os.listdir(folder)
#         except:
#             file_list = []
#
#         fnames = [
#             f
#             for f in file_list
#             if os.path.isfile(os.path.join(folder, f))
#             and f.lower().endswith(('.png', '.gif'))
#         ]
#         window['-FILE LIST-'].update(fnames)
#     elif event == '-FILE LIST-':
#         # a file was chosen from the listbox
#         try:
#             filename = os.path.join(
#                 values['-FOLDER-'], values['-FILE LIST-'][0]
#             )
#             window['-TOUT-'].update(filename)
#             window['-IMAGE-'].update(filename=filename)
#         except:
#             pass
#
# window.close()
