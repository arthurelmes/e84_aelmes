import imageio
import os

png_dir = '/home/arthur/Dropbox/career/e84/sample_data/png/'
gif_dir = '/home/arthur/Dropbox/career/e84/sample_data/gif/'

#for png in glob.glob(os.path.join(root_dir, "*.png")):
gif_list = [file for file in os.listdir(png_dir) if file.endswith('.png')]
gif_list.sort()
images = []
for file_name in gif_list:
    images.append(imageio.imread(png_dir + file_name))
try:
    imageio.mimsave(gif_dir + file_name + '.gif', images, 'GIF', duration=0.1)
except:
    print('failed to make gif for {}'.format(file_name))
