#!C:\Python27\python.exe
from shutil import copy2, copytree
from os import path, makedirs
from appdirs import user_config_dir

def post_installation():

    config_dest = user_config_dir("iridaUploader")
    # if config file already exists do not copy
    if not path.exists(path.join(config_dest, "config.conf")):
        if not path.isdir(config_dest):
            makedirs(config_dest)

        copy2("./iridaUploader/config.conf", config_dest)


if __name__ == "__main__":
    post_installation()
