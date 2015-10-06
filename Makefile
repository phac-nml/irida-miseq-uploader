SHELL=/bin/bash

clean:
	rm -rf pynsist_pkgs
	rm -rf .virtualenv
	rm -rf build
	rm -rf docs/_build
	rm -rf wxPython3.0-win32-3.0.2.0-py27.exe
	find -name "*pyc" -delete

requirements:
	virtualenv .virtualenv
	source .virtualenv/bin/activate
	pip install -r requirements.txt --allow-external PyPubSub

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

.ONESHELL: