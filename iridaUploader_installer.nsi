RequestExecutionLevel admin
InstallDir $EXEDir
Section
StrCpy $0 $sysdir 3
DetailPrint $0
DetailPrint "$INSTDIR"
DetailPrint "$0\Python27"
SectionEnd

Section prerequisites
  SetOutPath "$INSTDIR"

  File ".\\prerequisites\\python-2.7.10.msi"
  ExecWait '"msiexec" /qb! /i "prerequisites\\python-2.7.10.msi" TARGETDIR=C:\Python27'


  File ".\\prerequisites\\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"
  ExecWait "prerequisites\\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"


  File ".\\prerequisites\\iridaUploader-0.1.win32.msi"
  ExecWait '"msiexec" /qb! /i "prerequisites\\iridaUploader-0.1.win32.msi" TARGETDIR=C:\Python27'

  
SectionEnd

Section installmodules


  ExecWait "C:\Python27\Scripts\pip.exe install -r requirements.txt --allow-external pypubsub"


SectionEnd

Section postinstall

  
  ExecWait "C:\Python27\python.exe $INSTDIR\post_installation.py"


SectionEnd


Section create_desktop_shortcut
  File ".\\iridaUploader\GUI\images\\iu.ico"
  CreateShortCut "$DESKTOP\IRIDA Uploader.lnk" "C:\\Python27\\pythonw.exe" "C:\\Python27\\Lib\\site-packages\\iridaUploader\\run_IRIDA_Uploader.py" "$INSTDIR\iu.ico"
SectionEnd

Section create_startmenu_shortcut
  CreateDirectory "$SMPROGRAMS\iridaUploader"
  CreateShortCut "$SMPROGRAMS\IRIDA Uploader.lnk" "C:\\Python27\\pythonw.exe" "C:\\Python27\\Lib\\site-packages\\iridaUploader\\run_IRIDA_Uploader.py" "$INSTDIR\iu.ico"
SectionEnd