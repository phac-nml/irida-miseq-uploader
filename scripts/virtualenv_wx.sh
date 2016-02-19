#!/bin/bash

VIRTUAL_ENV=".virtualenv"

pyVersion=$(ls $VIRTUAL_ENV/lib/ | grep python2.*)
python2 -c "import sys;import os;import wx;sys.stdout.write(os.path.dirname(wx.__file__)[:-3])" > $VIRTUAL_ENV/lib/$pyVersion/site-packages/wx.pth
