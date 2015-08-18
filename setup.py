import sys
import site
import platform
import distutils
import distutils.core
from shutil import move, copy2
from os import path


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
