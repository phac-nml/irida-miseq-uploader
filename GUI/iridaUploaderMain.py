import sys
sys.path.append("../")

from Parsers.miseqParser import completeParseSamples, parseMetadata, getPairFiles
from Model.SequencingRun import SequencingRun
from Validation.offlineValidation import validateSampleSheet, validatePairFiles, validateSampleList
from Exceptions.SampleSheetError import SampleSheetError
from Exceptions.SequenceFileError import SequenceFileError

from pprint import pprint

import wx
import os
#from ProgressPanel import ProgressPanel

class MainPanel(wx.Panel):

	def __init__(self, parent):
		self.parent=parent
		wx.Panel.__init__(self, parent)

		self.sampleSheetFile=""
		self.seqRun=None
		self.browsePath="../"#os.getcwd()
		self.fileDlg=None

		self.LONG_BOX_SIZE=(300,32) #url and directories
		self.SHORT_BOX_SIZE=(200,32) #user and pass
		self.LABEL_TEXT_WIDTH=70
		self.LABEL_TEXT_HEIGHT=32

		self.topSizer = wx.BoxSizer(wx.VERTICAL)
		self.urlSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.directorySizer = wx.BoxSizer(wx.HORIZONTAL)
		self.usernameSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.passwordSizer = wx.BoxSizer(wx.HORIZONTAL)

		self.addURLsection()
		self.addSelectSampleSheetSection()
		self.addUsernameSection()
		self.addPasswordSection()


		self.topSizer.Add(self.urlSizer, proportion=0, flag=wx.ALL, border=5)
		self.topSizer.Add(self.directorySizer, proportion=0, flag=wx.ALL, border=5)

		self.topSizer.AddSpacer(50)

		self.topSizer.Add(self.usernameSizer, proportion=0, flag=wx.ALL, border=5)
		self.topSizer.Add(self.passwordSizer, proportion=0, flag=wx.ALL, border=5)

		self.addUploadButton()

		self.SetSizer(self.topSizer)
		self.Layout()

		#self.progPanel=ProgressPanel(self.parent)
		#self.progPanel.Hide()

	def addURLsection(self):
		"""
		Adds URL text label and text box in to panel
		Sets a tooltip when hovering over text label or text box describing the URL that needs to be entered in the text box

		no return value
		"""
		self.baseUrlLabel= wx.StaticText(parent=self, id=-1, size=(self.LABEL_TEXT_WIDTH,self.LABEL_TEXT_HEIGHT), label="Base URL")
		self.baseUrlBox= wx.TextCtrl(self, size=self.LONG_BOX_SIZE)
		self.baseUrlBox.SetFocus()

		self.urlSizer.Add(self.baseUrlLabel, 0, wx.ALL,5)
		self.urlSizer.Add(self.baseUrlBox, 0, wx.ALL, 5)

		tip="Enter the URL for the IRIDA server"
		self.baseUrlBox.SetToolTipString(tip)
		self.baseUrlLabel.SetToolTipString(tip)


	def addSelectSampleSheetSection(self):
		"""
		Adds data directory text label, text box and button in to panel
		Sets a tooltip when hovering over text label, text box or button describing what file needs to be selected

		Clicking the browse button or the text box launches the file dialog so that user can select SampleSheet file

		no return value
		"""

		self.directoryLabel= wx.StaticText(parent=self, id=-1,size=(self.LABEL_TEXT_WIDTH,self.LABEL_TEXT_HEIGHT), label="Data directory")
		self.directoryBox= wx.TextCtrl(self, size=self.LONG_BOX_SIZE)
		self.browseButton =wx.Button(self, label="Choose directory")

		self.directorySizer.Add(self.directoryLabel,0, wx.ALL, 5)
		self.directorySizer.Add(self.directoryBox, 0, wx.ALL,5)
		self.directorySizer.Add(self.browseButton, 0 ,wx.ALL, 5)


		tip="Select the SampleSheet.csv file for the sequence files that you want to upload"
		self.directoryBox.SetToolTipString(tip)
		self.directoryLabel.SetToolTipString(tip)
		self.browseButton.SetToolTipString(tip)

		self.Bind(wx.EVT_BUTTON, self.openDirDialog, self.browseButton )
		self.directoryBox.Bind(wx.EVT_LEFT_DOWN, self.openDirDialog) #clicking directoryBox
		self.directoryBox.Bind(wx.EVT_SET_FOCUS , self.openDirDialog) #tabbing in to directorybox


	def addUsernameSection(self):
		"""
		Adds username text label and text box in to panel

		no return value
		"""
		self.usernameLabel= wx.StaticText(parent=self, id=-1, size=(self.LABEL_TEXT_WIDTH,self.LABEL_TEXT_HEIGHT),label="Username")
		self.usernameBox= wx.TextCtrl(self, size=self.SHORT_BOX_SIZE)
		self.usernameSizer.Add(self.usernameLabel)
		self.usernameSizer.Add(self.usernameBox)


	def addPasswordSection(self):
		"""
		Adds password text label and text box in to panel

		no return value
		"""
		self.passwordLabel= wx.StaticText(self, -1, size=(self.LABEL_TEXT_WIDTH,self.LABEL_TEXT_HEIGHT), label="Password")
		self.passwordBox= wx.TextCtrl(self, size=self.SHORT_BOX_SIZE, style=wx.TE_PASSWORD)
		self.passwordSizer.Add(self.passwordLabel)
		self.passwordSizer.Add(self.passwordBox)


	def addUploadButton(self):
		"""
		Adds upload button to panel

		no return value
		"""
		self.uploadButton =wx.Button(self, label="Upload")

		self.topSizer.AddStretchSpacer()
		self.topSizer.Add(self.uploadButton, 0, wx.BOTTOM|wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.uploadToServer, self.uploadButton)


	def displayWarning(self,warnMsg):
		"""Displays warning message

		arguments:
			warnMsg -- message to display in warning dialog baseUrlBox

		no return value
		"""
		warnDlg = wx.MessageDialog(parent=self, message=warnMsg, caption="Warning!", style=wx.OK | wx.ICON_WARNING)
		warnDlg.ShowModal()
		warnDlg.Destroy()

	def uploadToServer(self, event):
		"""
		Function bound to uploadButton being clicked
		Currently just prints values entered in text boxes and pairFiles in seqRun

		arguments:
			event -- EVT_BUTTON when upload button is clicked

		no return value
		"""

		print ("Server URL: " + self.baseUrlBox.GetValue() + "\n" + "User: " +self.usernameBox.GetValue() + "\n" + "Password: " + self.passwordBox.GetValue()).strip()

		if self.seqRun!=None:
			print self.seqRun.getWorkflow()
			pprint([self.seqRun.getPairFiles(sample.getID()) for sample in self.seqRun.getSamplesList()])



	def openDirDialog(self,event):
		"""
		Function bound to browseButton being clicked and directoryBox being clicked or tabbbed/focused
		Opens file dialog for user to select SampleSheet.csv
		Validates the selected SampleSheet
		If it's valid then proceed to create the sequence run (createSeqRun)
		else displays warning messagebox containing the error(s)

		arguments:
			event -- EVT_BUTTON when browse button is clicked
				or EVT_SET_FOCUS when directoryBox is focused via tabbing
				or EVT_LEFT_DOWN when directoryBox is clicked

		no return value
		"""

		self.browseButton.SetFocus()

		self.fileDlg= wx.FileDialog(self, "Select SampleSheet.csv file",  defaultDir=self.browsePath, style=wx.DD_DEFAULT_STYLE)

		if self.fileDlg.ShowModal() == wx.ID_OK:

			try:
				self.browsePath=self.fileDlg.GetDirectory()
				vRes=validateSampleSheet(self.fileDlg.GetPath())
				if vRes.isValid()==True:
					self.sampleSheetFile=self.fileDlg.GetPath()
					self.directoryBox.SetValue(self.sampleSheetFile)
					self.createSeqRun()
				else:
					self.displayWarning(vRes.getErrors())
					self.seqRun=None

			except SampleSheetError, e:
				self.displayWarning(str(e))
				self.seqRun=None

		self.fileDlg.Destroy()


	def createSeqRun(self):
		"""
		Try to create a SequencingRun object and store in to self.seqRun
		Parses out the metadata dictionary and sampleslist from selected self.sampleSheetFile
		Displays errors in warning messageBox
			if parsing raises/throws Exceptions
			if the parsed out samplesList fails validation
			if a pair file for a sample in samplesList fails validation

		no return value
		"""
		try:
			mDict=parseMetadata( self.sampleSheetFile )
			sList=completeParseSamples( self.sampleSheetFile )

		except SampleSheetError, e:
			self.displayWarning(str(e))
			return

		except SequenceFileError,e:
			self.displayWarning(str(e))
			return


		vRes=validateSampleList(sList)
		if vRes.isValid()==True:

			self.seqRun=SequencingRun()
			self.seqRun.setMetadata(mDict)
			self.seqRun.setSamplesList(sList)

		else:
			self.displayWarning(vRes.getErrors())
			return


		for sample in self.seqRun.getSamplesList():
			pfList=self.seqRun.getPairFiles( sample.getID() )

			vRes= validatePairFiles(pfList)
			if vRes.isValid()==False:
				self.displayWarning(vRes.getErrors())
				break


class MainFrame(wx.Frame):
	def __init__(self):
		self.WindowSize=(600,400)
		wx.Frame.__init__(self, parent=None, id=wx.ID_ANY, title="IRIDA Uploader", size=self.WindowSize, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)#use default frame style but disable border resize and maximize

		self.mp=MainPanel(self)
		self.Show()


if __name__ == "__main__":
	app = wx.App(False)
	frame = MainFrame()
	frame.Show()
	app.MainLoop()
