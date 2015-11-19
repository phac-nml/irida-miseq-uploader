import distutils
import distutils.core

def readme():
    """Return the readme file"""
    with open("README.md") as f:
        return f.read()


distutils.core.setup(name="iridaUploader",
    version="1.1.0",
    url="http://irida.corefacility.ca/gitlab/rcamba/iridauploader.git",
    author='Kevin Camba',
    author_email='kevin.camba@phac-aspc.gc.ca',
    packages=["API", "Exceptions",
              "GUI", "Model",
              "Parsers", "Validation",
              "docs", "docs._static",
              "docs._static.basic_usage",
              "docs._static.handling_errors",
			  "docs._build",
			  "docs._build.html",
			  "docs._build.html._images",
			  "docs._build.html._sources",
			  "docs._build.html._static"],
    package_dir={
        "GUI/images": "GUI/images",
        "docs/_static": "docs/_static",
		"docs/_build": "docs/_build"
    },
    package_data={
        "GUI": ["images/*.png", "images/*.ico"],
        "docs._static.basic_usage": ["*.png", "*.gif"],
        "docs._static.handling_errors": ["*.png", "*.gif"],
		"docs._build": ["*"],
		"docs._build.html": ["*"],
		"docs._build.html._images": ["*"],
		"docs._build.html._sources": ["*"],
		"docs._build.html._static": ["*"]
    },
	scripts=["run_IRIDA_Uploader.py"]
)
