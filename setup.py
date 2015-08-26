import distutils
import distutils.core

from appdirs import user_config_dir

from post_installation import post_installation

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
        "iridaUploader/GUI/images": "iridaUploader/GUI/images"
    },
    package_data={
        "iridaUploader.GUI": ["images/*.png"]
    }
)


post_installation()
