"""
/***************************************************************************
 CAMSDataManagerDialog
                                 A QGIS plugin
 Manage and analyze CAMS air quality data in QGIS
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2025-05-02
        git sha              : $Format:%H$
        copyright            : (C) 2025 by POLIMI
        email                : zhanbin.wu@mail.polimi.it
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from .tools.ui_handler import AVAILABILITY

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'cams_data_manager_dialog_base.ui'))


class CAMSDataManagerDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(CAMSDataManagerDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        # Set default download folder path
        default_download_dir = os.path.expanduser("~/CAMS_Data")
        if not os.path.exists(default_download_dir):
            os.makedirs(default_download_dir, exist_ok=True)
        self.lineFolder.setText(default_download_dir)
        # Initialize yearCheckBox and monthCheckBox to prevent update_year_options errors
        self.yearCheckBox = {
            str(y): getattr(self, f"checkYear{y}", None)
            for y in range(2013, 2024)
            if hasattr(self, f"checkYear{y}")
        }
        self.monthCheckBox = {
            f"{m:02}": getattr(self, f"checkMonth{m:02}", None)
            for m in range(1, 13)
            if hasattr(self, f"checkMonth{m:02}")
        }
        self._ui_ready = False  # Don't show popup during initialization
        # Connect the Save button to the save_key method
        self.pushButton_save_key.clicked.connect(self.save_key)
        self.comboVariable.currentIndexChanged.connect(self.update_year_options)
        self.comboModel.currentIndexChanged.connect(self.update_year_options)
        self.comboType.currentIndexChanged.connect(self.update_year_options)
        self.update_year_options()

    def update_year_options(self):
        """
        Enable only the years available for the selected Variable, Model, and Type.
        """
        # UI friendliness: add an English hint above the year selection area
        if hasattr(self, 'labelYearHint'):
            self.labelYearHint.setText("Year availability depends on Variable, Model, and Type. LEVEL does not affect year selection.")
        var = self.comboVariable.currentText()
        model = self.comboModel.currentText()
        typ = self.comboType.currentText()
        years = AVAILABILITY.get((var, model, typ), [])
        # Robustness: if there are no available years, show a warning and disable all checkboxes
        if not years:
            for year, cb in self.yearCheckBox.items():
                cb.setEnabled(False)
                cb.setChecked(False)
            if getattr(self, '_ui_ready', False):
                QtWidgets.QMessageBox.warning(self, "No Available Years", "No available years for the current selection. Please change parameters.")
            return
        for year, cb in self.yearCheckBox.items():
            cb.setEnabled(year in years)
            if year not in years:
                cb.setChecked(False)

    def initialize_dropdown_menus(self):
        """Fill the combo boxes with options matching the Copernicus CAMS website."""
        # Disconnect signals to prevent multiple triggers during initialization
        self.comboVariable.blockSignals(True)
        self.comboModel.blockSignals(True)
        self.comboType.blockSignals(True)

        self.comboVariable.clear()
        self.comboVariable.addItems([
            "Ammonia", "Carbon monoxide", "Formaldehyde", "Glyoxal", "Nitrogen dioxide",
            "Nitrogen monoxide", "Non-methane VOCs", "Ozone",
            "Particulate matter < 2.5 µm (PM2.5)", "PM2.5, residential elementary carbon",
            "PM2.5, secondary inorganic aerosol", "PM2.5, total organic matter",
            "Particulate matter < 10 µm (PM10)", "PM10, dust", "PM10, sea salt (dry)",
            "PM10, wildfires", "PM10, total elementary carbon", "Peroxyacyl nitrates", "Sulphur dioxide"
        ])
        self.comboModel.clear()
        self.comboModel.addItems([
            "Ensemble median", "CHIMERE", "EMEP", "LOTOS-EUROS", "MATCH", "MINNI",
            "MOCAGE", "MONARCH", "SILAM", "EURAD-IM", "DEHM", "GEM-AQ"
        ])
        self.comboLevel.clear()
        self.comboLevel.addItems([
            "0", "50", "100", "250", "500", "750", "1000", "2000", "3000", "5000"
        ])
        self.comboType.clear()
        self.comboType.addItems([
            "Validated reanalysis", "Interim reanalysis"
        ])

        self.comboVariable.blockSignals(False)
        self.comboModel.blockSignals(False)
        self.comboType.blockSignals(False)

        # Call manually after filling
        self.update_year_options()
        self._ui_ready = True  # Initialization complete, can show popups now

    def save_key(self):
        """
        Save the user API key to the .cdsapirc file in the user's home directory.
        """
        user_key = self.lineEdit_api_key.text().strip()
        if not user_key:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter your API KEY.")
            return

        home_dir = os.path.expanduser("~")
        cdsapirc_path = os.path.join(home_dir, ".cdsapirc")
        try:
            with open(cdsapirc_path, "w") as f:
                f.write("url: https://ads.atmosphere.copernicus.eu/api\n")
                f.write(f"key: {user_key}\n")
            QtWidgets.QMessageBox.information(self, "Success", ".cdsapirc file saved successfully!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save .cdsapirc file:\n{str(e)}")
