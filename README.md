## Irida Uploader  


### Installation
Install pip and wxpython:

    $ sudo apt-get install python-pip python-wxgtk2.8
    $ pip install virtualenv
    $ sudo python setup.py install

### virtualenv usage  

Build a virtualenv and install the dependencies:

    $ mkdir iu; cd iu
    $ virtualenv .
    $ source bin/activate
    $ git clone http://irida.corefacility.ca/gitlab/rcamba/iridauploader.git
    $ cd iridauploader
    $ pip install -r requirements.txt
    $ scripts/virtualenv_wx.sh

Remember that wxPython must be already installed using:

    $ sudo apt-get install python-wxgtk2.8

Deactivate when finished:

    $ deactivate

