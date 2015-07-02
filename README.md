## Irida Uploader  


### Linux Installation
Install pip and wxpython:

    $ sudo apt-get install python-pip python-wxgtk2.8

### Windows Installation
pip:

    https://pip.pypa.io/en/latest/installing.html

wxpython:

    http://www.wxpython.org/download.php

### virtualenv usage  

Install virtualenv

    $ pip install virtualenv

Build a virtualenv and install the dependencies:

    $ mkdir iu; cd iu
    $ virtualenv .
    $ source bin/activate
    $ git clone http://irida.corefacility.ca/gitlab/rcamba/iridauploader.git
    $ cd iridauploader
    $ pip install -r requirements.txt
    $ scripts/virtualenv_wx.sh
    $ python setup.py install

Remember that wxPython must be already installed using:

    $ sudo apt-get install python-wxgtk2.8

Deactivate when finished:

    $ deactivate
