import site
import platform
import distutils
import distutils.core
from shutil import move, copy2
from os import path, mkdir
from appdirs import user_config_dir


def readme():
    """Return the readme file"""
    with open("README.md") as f:
        return f.read()


distutils.core.setup(name="iridaUploader",
    version="0.1",
    url="http://irida.corefacility.ca/gitlab/rcamba/iridauploader.git",
    author='Kevin Camba',
    author_email='kevin.camba@phac-aspc.gc.ca',
    packages=["iridaUploader", "iridaUploader.API", "iridaUploader.Exceptions",
              "iridaUploader.GUI", "iridaUploader.Model",
              "iridaUploader.Parsers", "iridaUploader.Validation"],
    package_dir={
        "iridaUploader/GUI/images": "iridaUploader/GUI/images",
        "iridaUploader": "iridaUploader"
    },
    package_data={
        "iridaUploader.GUI": ["images/*.png"],
        "iridaUploader": ["*.conf"]
    }
)


config_dest = user_config_dir("iridaUploader")
# if config file already exists do not copy
if not path.exists(path.join(config_dest, "config.conf")):
    if not path.isdir(config_dest):
        mkdir(config_dest)

    copy2("./config.conf", config_dest)
