import distutils.core
from run_IRIDA_Uploader.Uploader import __version__

distutils.core.setup(name="iridaUploader",
    version=__version__,
    url="https://github.com/phac-nml/irida-miseq-uploader",
    author='Kevin Camba, Franklin Bristow, Thomas Matthews',
    author_email='franklin.bristow@phac-aspc.gc.ca,thomas.matthews@phac-aspc.gc.ca',
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
