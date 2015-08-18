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
              "iridaUploader.Parsers", "iridaUploader.Validation"]
)

# Assuming only running on either Windows or Linux
if platform.system() == "Windows":
    py_version = str(sys.version_info.major) + str(sys.version_info.minor)
    dest = path.join(site.USER_BASE, "python" + py_version, "site-packages")
    copy2("./iridaUploader/config.conf", dest)

    img_dest = path.join(dest, "iridaUploader", "GUI","images")
    distutils.dir_util.copy_tree("./iridaUploader/GUI/images", img_dest)

else:
    ver_info = sys.version_info
    py_version = str(ver_info.major) + "." + str(ver_info.minor)

    dest = path.join(site.USER_BASE, "lib", "python" + py_version,
                     "site-packages", "iridaUploader")
    copy2("./iridaUploader/config.conf", dest)

    img_dest = path.join(dest, "iridaUploader", "GUI","images")
    distutils.dir_util.copy_tree("./iridaUploader/GUI/images", img_dest)