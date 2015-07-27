## Irida Uploader  


### Linux Installation

Install pip and wxpython:

    $ sudo apt-get install python-pip python-wxgtk2.8


### Windows Installation

pip:

    https://pip.pypa.io/en/latest/installing.html

wxpython:

    http://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/
    Download wxPython2.8-win64-unicode-2.8.12.1-py27.exe for Windows 64 bit
    or wxPython2.8-win32-unicode-2.8.12.1-py27.exe for Windows 32 bit

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
    $ scripts/virtualenv_wx.sh
    $ python setup.py install

Remember that wxPython must be already installed using:

    $ sudo apt-get install python-wxgtk2.8

Deactivate when finished:

    $ deactivate

### Running Tests  

Run unit tests and PEP8 verification with:

    $ python RunAllTests.py

Running integration tests in addition to unit tests and PEP8 verification: (can take a while)
Google Chrome must be installed for selenium testing

    $ echo "grant all privileges on irida_uploader_test.* to 'test'@'localhost' identified by 'test';" | mysql -u mysql_user -p
    $ python RunAllTests.py --integration

You can comment out test_suites inside RunAllTests.py to not have them run
