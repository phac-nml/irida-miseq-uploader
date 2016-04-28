SHELL=/bin/bash
IRIDA_VERSION?=master

all: clean requirements documentation windows

clean:
	rm -rf .cache
	rm -rf pynsist_pkgs
	rm -rf .virtualenv
	rm -rf build
	rm -rf docs/_build
	rm -rf wxPython3.0-win32-3.0.2.0-py27.exe
	find -name "*pyc" -delete
	rm -rf Tests/integrationTests/repos/

requirements:
	virtualenv -p python2 .virtualenv
	source .virtualenv/bin/activate
	pip install -r requirements.txt
	deactivate
	./scripts/virtualenv_wx.sh

documentation: requirements
	source .virtualenv/bin/activate
	pushd docs
	make html
	popd

windows: documentation requirements
	wget --no-clobber http://downloads.sourceforge.net/project/wxpython/wxPython/3.0.2.0/wxPython3.0-win32-3.0.2.0-py27.exe
	rm -rf pynsist_pkgs
	innoextract -d pynsist_pkgs -s wxPython3.0-win32-3.0.2.0-py27.exe
	mv pynsist_pkgs/app/wx-3.0-msw/wx pynsist_pkgs/
	rm -rf pynsist_pkgs/{app,code*}
	source .virtualenv/bin/activate
	pynsist irida-uploader.cfg 2>&1 > /dev/null

test: clean requirements documentation
	source .virtualenv/bin/activate
	xvfb-run --auto-servernum --server-num=1 py.test --integration --irida-version=$(IRIDA_VERSION)

.ONESHELL:
