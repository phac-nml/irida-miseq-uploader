IRIDA Uploader
==============

## NOTICE!
### This repo will be deprecated as of January 1st 2020, as Python 2 will be End of Life.
### Please use our new uploader https://github.com/phac-nml/irida-uploader

Windows Installation
--------------------

Download the installer from https://github.com/phac-nml/irida-miseq-uploader/releases

Running in Linux
----------------

Install pip and wxpython:

    $ sudo apt-get install python-pip python-wxgtk3.0

### virtualenv usage  

Install virtualenv and setuptools

    $ pip install virtualenv
    $ pip install setuptools

If you already have these packages installed, ensure they are up to date

    $ pip install virtualenv -U
    $ pip install setuptools -U

Build a virtualenv and install the dependencies:

    $ git clone https://github.com/phac-nml/irida-miseq-uploader
    $ cd irida-miseq-uploader
    $ make requirements
    $ source .virtualenv/bin/activate

You can then run the uploader by running:

    $ ./run_IRIDA_Uploader.py

Deactivate when finished:

    $ deactivate

Creating the Windows installer
------------------------------

### Requirements

You must install several packages to build the Windows installer:

    sudo apt-get install innoextract nsis python-pip python-virtualenv

### Building the Windows installer

From inside the `irida-miseq-uploader` directory, you can simply run:

    make windows

This will build a Windows installer inside the `build/nsis/` directory, named something like `IRIDA_Uploader_1.0.0.exe`.

Running Tests
-------------

You can run all tests (unit and integration) by running:

    $ echo "grant all privileges on irida_uploader_test.* to 'test'@'localhost' identified by 'test';" | mysql -u mysql_user -p
    $ make test

You can verify PEP8 conformity by running:

    $ ./scripts/verifyPEP8.sh

Note: No output is produced (other than `pip`-related output) if the PEP8 verification succeeds.
