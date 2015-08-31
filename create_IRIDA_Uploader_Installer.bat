C:\Python27\Scripts\pip.exe install -r requirements.txt --allow-external pypubsub
C:\Python27\python.exe setup.py bdist_msi
move dist\* prerequisites
"C:\Program Files (x86)\NSIS\makensis.exe" "iridaUploader_installer.nsi"
PAUSE
