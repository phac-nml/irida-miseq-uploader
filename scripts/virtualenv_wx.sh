#!/bin/bash

#must be executed in the same folder that a virtualenv was created
#virtualenv must be activated
pyVersion=$(ls $VIRTUAL_ENV/lib/ | grep python2.*)
echo /usr/lib/$pyVersion/dist-packages/wx-2.8-gtk2-unicode/ > $VIRTUAL_ENV/lib/$pyVersion/site-packages/wx.pth
