import sys
import os
import mmap
import shutil
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import pyqtSlot

import BGA2Editor

class BGA2:
	def __init__(self, save_file):
		shutil.copyfile(save_file, save_file + '.bak')

		with open(save_file, 'rb+') as Profile:
			self.ProfileMM = mmap.mmap(Profile.fileno(), 0)

		self.ProfileMM.seek(0)
		self.ProfileMM.seek(self.ProfileMM.find(b'\x45\x6E\x75\x6D\x46\x61\x63\x74\x69\x6F\x6E\x00')+13) #EnumFaction
		StrLength = int.from_bytes(self.ProfileMM.read(4),sys.byteorder)
		self.ProfileMM.seek(13,os.SEEK_CUR)
		Faction = self.ProfileMM.read(StrLength-14).decode("utf-8").title()

		Difficulty = self.ProfileMM.find(b'\x45\x6E\x75\x6D\x44\x69\x66\x66\x69\x63\x75\x6C\x74\x79') #EnumDifficulty
		if (Difficulty == -1): #If difficulty is EASY there is no EnumDifficulty field so this will fail
		  Difficulty = "Easy"
		else:
		  self.ProfileMM.seek(Difficulty+16)
		  StrLength = int.from_bytes(self.ProfileMM.read(4),sys.byteorder)
		  self.ProfileMM.seek(16, os.SEEK_CUR)
		  Difficulty = self.ProfileMM.read(StrLength-17).decode("utf-8").title()

		OffsetStr = "CampaignCommander_" + Faction + "_C"
		self.ProfileMM.seek(self.ProfileMM.find(OffsetStr.encode())+len(OffsetStr)+6)
		self.CampaignOffset = self.ProfileMM.tell()
		Level = int.from_bytes(self.ProfileMM.read(4),sys.byteorder)
		Renown = int.from_bytes(self.ProfileMM.read(4),sys.byteorder)
		self.ProfileMM.seek(5,os.SEEK_CUR)
		Leadership = int.from_bytes(self.ProfileMM.read(4),sys.byteorder)
		Income = int.from_bytes(self.ProfileMM.read(4),sys.byteorder)
		UpgradePoints = int.from_bytes(self.ProfileMM.read(4),sys.byteorder)
		self.ProfileMM.seek(self.ProfileMM.find("Game_ProperNoun_GenericFleetName".encode())-12)
		FleetPoints = int.from_bytes(self.ProfileMM.read(4),sys.byteorder)
		self.ProfileMM.seek(self.ProfileMM.find(b'\xD2\x02\x96\x49')+4) #No clue what this is, but it seems to provide the correct location
		BattlePlans = int.from_bytes(self.ProfileMM.read(4),sys.byteorder)

		self.ProfileMM.seek(0)
		
		self.difficulty = Difficulty
		self.faction = Faction
		self.level = Level
		self.renown = Renown
		self.leadership = Leadership
		self.fleetpoints = FleetPoints
		self.income = Income
		self.upgradepoints = UpgradePoints
		self.battleplans = BattlePlans
		self.heal = False
		self.max = False


	def __del__(self):
		self.ProfileMM.flush()


	def write(self):
		self.ProfileMM.seek(self.CampaignOffset+4)
		self.ProfileMM.write(self.renown.to_bytes(4,sys.byteorder))

		self.ProfileMM.seek(self.CampaignOffset+13)
		self.ProfileMM.write(self.leadership.to_bytes(4,sys.byteorder))

		self.ProfileMM.seek(self.ProfileMM.find("Game_ProperNoun_GenericFleetName".encode())-12)
		self.ProfileMM.write(self.fleetpoints.to_bytes(4,sys.byteorder))

		self.ProfileMM.seek(self.CampaignOffset+17)
		self.ProfileMM.write(self.income.to_bytes(4,sys.byteorder))

		self.ProfileMM.seek(self.CampaignOffset+21)
		self.ProfileMM.write(self.upgradepoints.to_bytes(4,sys.byteorder))

		self.ProfileMM.seek(self.ProfileMM.find(b'\xD2\x02\x96\x49')+4)
		self.ProfileMM.write(self.battleplans.to_bytes(4,sys.byteorder))

		if self.heal:
			BGA2Editor.EditShips(self.ProfileMM, self.faction,0)

		if self.max:
			BGA2Editor.EditShips(self.ProfileMM, self.faction,1)


	def display(self):
		print('''
Faction:        {}
Difficulty:     {}
Level:          {}
Renown:         {}
Leadership:     {}
FleetPoints:    {}
Income:         {}
UpgradePoints:  {}
BattlePlans:    {}
Heal Ships:     {}
Max Ships:      {}
			'''.format(self.faction, self.difficulty, self.level, self.renown, self.leadership, self.fleetpoints,
			 self.income, self.upgradepoints, self.battleplans, self.heal, self.max))


class MyWindow(QMainWindow):
	def __init__(self, path):
		super().__init__()

		self.path = path

		self.title = 'BGA2 Save Editor'
		self.left = 100
		self.top = 100
		self.width = 640
		self.height = 480

		self.initUI()


	def initUI(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)
		font = QFont()
		font.setPointSize(15)
		self.setFont(font)

		self.openFileDialog()
		self.sav_data = BGA2(self.filename)

		self.statusBar().showMessage('File: ' + self.filename)

		label_faction = QLabel('Faction: ', self)
		label_faction.move(0, 10)
		label_faction_val = QLabel(self.sav_data.faction, self)
		label_faction_val.move(180, 10)

		label_difficulty = QLabel('Difficulty: ', self)
		label_difficulty.move(0, 50)
		label_difficulty_val = QLabel(self.sav_data.difficulty, self)
		label_difficulty_val.move(180, 50)

		label_level = QLabel('Level: ', self)
		label_level.move(0, 90)
		label_level_val = QLabel(str(self.sav_data.level), self)
		label_level_val.move(180, 90)

		label_renown = QLabel('Renown:', self)
		label_renown.move(0, 130)
		self.edit_renown = QLineEdit(self)
		self.edit_renown.move(180, 130)
		self.edit_renown.resize(80, 40)
		self.edit_renown.setText(str(self.sav_data.renown))

		label_leadership = QLabel('Leadership:', self)
		label_leadership.move(0, 180)
		label_leadership.resize(120, 40)
		self.edit_leadership = QLineEdit(self)
		self.edit_leadership.move(180, 180)
		self.edit_leadership.resize(80, 40)
		self.edit_leadership.setText(str(self.sav_data.leadership))

		label_fleetpoints = QLabel('Fleet Points:', self)
		label_fleetpoints.move(0, 230)
		label_fleetpoints.resize(140, 40)
		self.edit_fleetpoints = QLineEdit(self)
		self.edit_fleetpoints.move(180, 230)
		self.edit_fleetpoints.resize(80, 40)
		self.edit_fleetpoints.setText(str(self.sav_data.fleetpoints))

		label_income = QLabel('Income:', self)
		label_income.move(0, 280)
		self.edit_income = QLineEdit(self)
		self.edit_income.move(180, 280)
		self.edit_income.resize(80, 40)
		self.edit_income.setText(str(self.sav_data.income))

		label_upgradepoints = QLabel('Upgrade Points:', self)
		label_upgradepoints.move(0, 330)
		label_upgradepoints.resize(140, 40)
		self.edit_upgradepoints = QLineEdit(self)
		self.edit_upgradepoints.move(180, 330)
		self.edit_upgradepoints.resize(80, 40)
		self.edit_upgradepoints.setText(str(self.sav_data.upgradepoints))

		label_battleplans = QLabel('Battle Plans:', self)
		label_battleplans.move(370, 10)
		label_battleplans.resize(140, 40)
		self.edit_battleplans = QLineEdit(self)
		self.edit_battleplans.move(510, 10)
		self.edit_battleplans.resize(80, 40)
		self.edit_battleplans.setText(str(self.sav_data.battleplans))

		heal_button = QPushButton('Heal Ships', self)
		heal_button.setToolTip('Heal all ships')
		heal_button.move(370, 60)
		heal_button.clicked.connect(self.on_heal_click)

		max_button = QPushButton('Max Ships', self)
		max_button.setToolTip('Max the level of all ships')
		max_button.move(370, 110)
		max_button.clicked.connect(self.on_max_click)

		save_button = QPushButton('Save', self)
		save_button.setToolTip('Save Changes')
		save_button.move(520, 430)
		save_button.clicked.connect(self.on_save_click)

		self.show()


	def openFileDialog(self):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		filename, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", self.path, "All Files (*);;Save Files (*.sav)", options=options)
		if filename:
			self.filename = filename
		else:
			QMessageBox.warning(self, "Warning", "File Not Selected")
			self.openFileDialog()


	@pyqtSlot()
	def on_save_click(self):
		self.sav_data.renown = int(self.edit_renown.text())
		self.sav_data.leadership = int(self.edit_leadership.text())
		self.sav_data.fleetpoints = int(self.edit_fleetpoints.text())
		self.sav_data.income = int(self.edit_income.text())
		self.sav_data.upgradepoints = int(self.edit_upgradepoints.text())
		self.sav_data.battleplans = int(self.edit_battleplans.text())
		self.sav_data.write()

		QMessageBox.about(self, 'Notice', 'Save Complete')

		self.close()


	@pyqtSlot()
	def on_heal_click(self):
		self.sav_data.heal = True


	@pyqtSlot()
	def on_max_click(self):
		self.sav_data.max = True


if __name__ == '__main__':
	path = os.path.join(os.path.expandvars("%LOCALAPPDATA%"),"BattleFleetGothic2\Saved\SaveGames\Campaign")
	
	app = QApplication(sys.argv)

	application = MyWindow(path)
	app.exec_()
