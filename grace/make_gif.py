"""Compile all PNGs in the given directory into an animated gif for visualization.
Author: Arthur Elmes
2021-05-28"""

import imageio
import os


def make_gif(png_dir, gif_dir):
    if not os.path.isdir(gif_dir):
        os.mkdir(gif_dir)

    gif_list = [file for file in os.listdir(png_dir) if file.endswith('.png')]
    gif_list.sort()
    images = []
    for file_name in gif_list:
        images.append(imageio.imread(os.path.join(png_dir, file_name)))
    try:
        imageio.mimsave(gif_dir + file_name + '.gif', images, 'GIF', duration=0.75)
    except:
        print('failed to make gif! Check input maps and directories.')

    print(f'Animated gif created: {os.path.join(gif_dir, file_name)}6.gif')


if __name__ == '__main__':
    png_dir = '/home/arthur/Dropbox/career/e84/sample_data/map_exports/-10_160_-45_100/'
    gif_dir = '/home/arthur/Dropbox/career/e84/sample_data/gif/'
    make_gif(png_dir, gif_dir)
