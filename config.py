import os


class Config:

    # put the data in another directory so that we don't
    # clutter our projects/code folder with data
    user_dir = os.path.expanduser('~')
    unpaywall_dir = os.path.join(user_dir,'.Unpaywall')
    data_dir = os.path.join(unpaywall_dir, 'data')

    # can put images with data, or in this folder. Choosing this folder.
    # images_dir = os.path.join(unpaywall_dir, 'images')
    images_dir = 'images'
    
    paths = [unpaywall_dir, data_dir, images_dir]

    for p in paths:
        if not os.path.exists(p):
            os.mkdir(p)