import imageio
import os


def make_gif(png_dir, gif_dir):
    gif_list = [file for file in os.listdir(png_dir) if file.endswith('.png')]
    gif_list.sort()
    images = []
    for file_name in gif_list:
        images.append(imageio.imread(png_dir + file_name))
    try:
        imageio.mimsave(gif_dir + file_name + '.gif', images, 'GIF', duration=0.1)
    except:
        print('failed to make gif for {}'.format(file_name))

    print(f'Animated gif created: {os.path.join(gif_dir, file_name)}6.gif')
