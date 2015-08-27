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


### Creating the Windows installer with NSIS

The `iridaUploader.msi` is created with `python setup.py bdist_msi`  
This creates a `dist` folder in the working directory which contains the `iridaUploader.msi`  
This needs to be moved into the `prerequisites` folder in order to compile the .nsi because that's where it's checking for python-2.7.10.msi, wxPython2.8-win32-unicode-2.8.12.1-py27.exe and iridaUploader.msi.  

Download and install NSIS 3.0b2 at http://nsis.sourceforge.net/Download on Windows. Right click the .nsi file and select compile NSIS script.
![NSIS](https://irida.corefacility.ca/gitlab/uploads/rcamba/iridauploader/fbef81fd4a/NSIS.png)  

You should now have the installer executable created.
