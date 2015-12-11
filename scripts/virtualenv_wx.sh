#!/bin/bash


#virtualenv must be activated  
pyVersion=$(ls $VIRTUAL_ENV/lib/ | grep python2.*)
echo /usr/lib/$pyVersion/dist-packages/wx-3.0-gtk2/ > $VIRTUAL_ENV/lib/$pyVersion/site-packages/wx.pth
