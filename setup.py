import sys
import site
import platform
from distutils.core import setup
from shutil import move, copy2, copytree
from os import path


def readme():
    """Return the readme file"""
    with open("README.md") as f:
        return f.read()

setup(name="iridaUploader",
      version="0.1",
      url="http://irida.corefacility.ca/gitlab/rcamba/iridauploader.git",
      author='Kevin Camba',
      author_email='kevin.camba@phac-aspc.gc.ca',
      packages=["API", "Exceptions", "GUI", "Model", "Parsers", "Validation"],
      install_requires=["mock", "rauth", "selenium", "pep8"],
      zip_safe=False
      )

# Assuming only running on either Windows or Linux
if platform.system() == "Windows":
    py_version = str(sys.version_info.major) + str(sys.version_info.minor)
    dest = path.join(site.USER_BASE, "python" + py_version, "site-packages")
    copy2("./config.conf", dest)

    img_dest = path.join(dest,"GUI","images")
    copytree("./GUI/images", img_dest)

else:
    ver_info = sys.version_info
    py_version = str(ver_info.major) + "." + str(ver_info.minor)

    dest = path.join(site.USER_BASE, "lib", "python" + py_version,
                     "site-packages")
    copy2("./config.conf", dest)

    img_dest = path.join(dest,"GUI","images")
    copytree("./GUI/images", img_dest)
