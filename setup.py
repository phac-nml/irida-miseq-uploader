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
              "iridaUploader.Parsers", "iridaUploader.Validation",
              "iridaUploader.docs", "iridaUploader.docs._static",
              "iridaUploader.docs._static.basic_usage",
              "iridaUploader.docs._static.handling_errors"],
    package_dir={
        "iridaUploader/GUI/images": "iridaUploader/GUI/images",
        "iridaUploader/docs/_static": "iridaUploader/docs/_static"
    },
    package_data={
        "iridaUploader.GUI": ["images/*.png", "images/*.ico"],
        "iridaUploader.docs._static.basic_usage": ["*.png", "*.gif"],
        "iridaUploader.docs._static.handling_errors": ["*.png", "*.gif"]
    },
	scripts=["iridaUploader/run_IRIDA_Uploader.py"]
)


post_installation()
