; These are the programs that are needed by ACME Suite.
RequestExecutionLevel admin
Section -prerequisites
  
   MessageBox MB_YESNO "Install Python" /SD IDYES IDNO endPythonInstall
	File ".\\prerequisites\\python-2.7.10.msi"
    ExecWait '"msiexec" /i "prerequisites\\python-2.7.10.msi"'
  endPythonInstall:
  
  MessageBox MB_YESNO "Install wxPython" /SD IDYES IDNO endwxPythonInstall
	File ".\\prerequisites\\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"
    ExecWait "prerequisites\\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"
  endwxPythonInstall:
  
  MessageBox MB_YESNO "Install iridaUploader" /SD IDYES IDNO end_IU_Install
	File ".\\prerequisites\\iridaUploader-0.1.win32.msi"
    ExecWait '"msiexec" /i "prerequisites\\iridaUploader-0.1.win32.msi"'
  end_IU_Install:
  
SectionEnd

Section -installmodules

  MessageBox MB_YESNO "Install required modules" /SD IDYES IDNO endModuleInstall
    ExecWait "C:\Python27\Scripts\pip.exe install -r requirements.txt --allow-external pypubsub"
  endModuleInstall:

SectionEnd