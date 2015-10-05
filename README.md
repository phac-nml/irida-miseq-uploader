IRIDA Uploader
==============


Windows Installation
--------------------

Download the installer from https://irida.corefacility.ca/downloads/tools/

Linux Installation
------------------

Install pip and wxpython:

    $ sudo apt-get install python-pip python-wxgtk2.8

### virtualenv usage  

Install virtualenv

    $ pip install virtualenv

Build a virtualenv and install the dependencies:

    $ mkdir iu; cd iu
    $ virtualenv .
    $ source bin/activate
    $ git clone http://irida.corefacility.ca/gitlab/rcamba/iridauploader.git
    $ cd iridauploader
    $ pip install -r requirements.txt --allow-external pypubsub
    $ ./scripts/virtualenv_wx.sh
    $ cd docs
    $ make html
    $ cd ..
    $ python setup.py install

Deactivate when finished:

    $ deactivate

Running Tests
-------------

Run unit tests and PEP8 verification with:

    $ python RunAllTests.py

Running integration tests in addition to unit tests and PEP8 verification: (can take a while)
Google Chrome must be installed for selenium testing

    $ echo "grant all privileges on irida_uploader_test.* to 'test'@'localhost' identified by 'test';" | mysql -u mysql_user -p
    $ python RunAllTests.py --integration

You can comment out `test_suites` inside RunAllTests.py to not have them run

Creating the Windows installer
------------------------------

### Requirements

You must install several packages to build the Windows installer:

    sudo apt-get install innoextract nsis python-pip python-virtualenv

### Building the Windows installer

From inside the `iridaUploader` directory, you can simply run:

    make windows

This will build a Windows installer inside the `build/nsis/` directory, named something like `IRIDA_Uploader_1.0.0.exe`.

