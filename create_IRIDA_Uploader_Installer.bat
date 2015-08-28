C:\Python27\python.exe setup.py bdist_msi
move dist\* prerequisites
"C:\Program Files (x86)\NSIS\makensis.exe" "iridaUploader_installer.nsi"
