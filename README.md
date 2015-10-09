IRIDA Uploader
==============


Windows Installation
--------------------

Download the installer from https://irida.corefacility.ca/downloads/tools/

Running in Linux
----------------

Install pip and wxpython:

    $ sudo apt-get install python-pip python-wxgtk2.8

### virtualenv usage  

Install virtualenv

    $ pip install virtualenv

Build a virtualenv and install the dependencies:

    $ mkdir iu; cd iu
    $ virtualenv .
    $ source bin/activate
    $ git clone https://irida.corefacility.ca/irida/irida-miseq-uploader.git
    $ cd irida-miseq-uploader
    $ pip install -r requirements.txt --allow-external pypubsub
    $ ./scripts/virtualenv_wx.sh
    $ cd docs
    $ make html
    $ cd ..

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

From inside the `iridaUploader` directory, you can simply run:

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
