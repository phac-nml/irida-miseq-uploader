C:\Python27\Scripts\pip.exe install -r requirements.txt --allow-external pypubsub
C:\Python27\Scripts\pip.exe install -r requirements-building.txt --allow-external pypubsub
cd iridaUploader/docs
C:\Python27\Scripts\sphinx-build -b html -d _build/doctrees   . _build/html
echo. 2>_build/__init__.py
echo. 2>_build/html/__init__.py
echo. 2>_build/html/_images/__init__.py
echo. 2>_build/html/_sources/__init__.py
echo. 2>_build/html/_static/__init__.py
cd ../..
C:\Python27\python.exe setup.py bdist_msi
move dist\* prerequisites
"C:\Program Files (x86)\NSIS\makensis.exe" "iridaUploader_installer.nsi"
PAUSE
