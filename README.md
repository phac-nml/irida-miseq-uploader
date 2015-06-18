**iridaUploader**


Install pip and wxpython: `sudo apt-get install python-pip python-wxgtk2.8`  


Install mock, rauth and selenium: `sudo pip install mock rauth selenium`    
Alternatively, download them manually:  
https://pypi.python.org/pypi/mock#downloads  
https://pypi.python.org/pypi/rauth/0.7.1  
https://pypi.python.org/pypi/selenium   
  
  
**virtualenv usage**  
install:  
`pip install virtualenv`    

create a new virtualenv:  
`virtualenv env`  

activate:  
`source env/bin/activate`  

install requirements:  
`pip install -r requirements.txt`  
run `scripts/virtualenv_wx.sh` to use already installed wxPython in virtualenv  
 *wxPython must be already installed* using `sudo apt-get install python-wxgtk2.8`  

deactivate when finished:  
`deactivate`  
