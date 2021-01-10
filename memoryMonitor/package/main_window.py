"""
 ----------------------------------------------------------------------------------------------------------------------
 memoryMonitor
 Version: 21.0.0
 Author: Hugo Durand-Mermet
 Last Modified by: Hugo Durand-Mermet
 Last Updated: January 10th, 2020
 ----------------------------------------------------------------------------------------------------------------------

 ----------------------------------------------------------------------------------------------------------------------
 USAGE:
 Creates a side panel to display your script's usage
 of RAM. Can be updated manually or self-updated every time
 interval you'll have set in the settings.
 ----------------------------------------------------------------------------------------------------------------------

 ----------------------------------------------------------------------------------------------------------------------
 ROOM FOR IMPROVEMENT:

 ----------------------------------------------------------------------------------------------------------------------

 ----------------------------------------------------------------------------------------------------------------------
 INSTRUCTIONS:

 -Save this py script in /.nuke or your favourite folder. Make sure the folder path has been saved in the init.py
 script.
 -In your menu.py script, add the following lines:

 pane = nuke.getPaneFor('Properties.1')
 panels.registerWidgetAsPanel('get_memory_monitor', 'Memory Monitor', 'ue.panel.ueSave', True).addToPane(pane)

 Add the following line if it isn't already in your menu.py script:

 import nukescripts
 -This script has been tested on a free trial version of Nuke12.2v3. If you have an older or a custom version of Nuke,
 it's possible this script doesn't work as
 expected, especially since it relies on modules to import. If that is the case, don't hesitate to reach out to me
 through my GitHub.
 ----------------------------------------------------------------------------------------------------------------------
"""

from PySide2 import QtWidgets, QtCore, QtGui, QtCharts
import datetime

import nuke
from nukescripts import panels

from package.api.functore import *
from package.api.widgets import *


class MainPanel(QtWidgets.QWidget):
    """Our main window panel importing the monitor widget and with all the necessaries settings for the users to run it
    their way.
    """
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.loop_time = 10
        self.layout = QtWidgets.QVBoxLayout()
        self.tabBar = QtWidgets.QTabWidget()
        self.layout.addWidget(self.tabBar)
        self.setLayout(self.layout)
        self.monitorTab = QtWidgets.QWidget()
        self.propertiesTab = QtWidgets.QWidget()
        self.tabBar.addTab(self.monitorTab, "Monitor")
        self.tabBar.addTab(self.propertiesTab, "Properties")
        self.monitorTabLayout = QtWidgets.QVBoxLayout()
        self.monitorTab.setLayout(self.monitorTabLayout)
        self.propertiesTabLayout = QtWidgets.QVBoxLayout()
        self.propertiesTab.setLayout(self.propertiesTabLayout)

        self.monitor = Monitor(self)
        self.monitorTabLayout.addWidget(self.monitor)
        self.worker = Worker(self.update_chart, (self.loop_time * 1000))

        self.autoUpdateLayout = QtWidgets.QHBoxLayout()
        self.autoUpdateStart = CustomPushButton("Start Auto-Update", "Start Auto-Update: Starts a loop that \n "
                                                                     "will automatically update the monitor, "
                                                                     "for every time interval "
                                                                     "\n you'll have set in the Properties "
                                                                     "panel (Default is 30 seconds)")
        self.autoUpdateStart.clicked.connect(self.worker.start)
        self.autoUpdateStop = CustomPushButton("Stop Auto-Update", "Stop Auto-Update: Stops the \n currently "
                                                                   "running Auto-Update.")
        self.autoUpdateStop.clicked.connect(self.worker.stop)

        self.autoUpdateLayout.addWidget(self.autoUpdateStart)
        self.autoUpdateLayout.addWidget(self.autoUpdateStop)
        self.monitorTabLayout.addLayout(self.autoUpdateLayout)

        self.manualUpdateButton = CustomPushButton("Manual Update",
                                                   "Manual Update: Click it to manually update \n the chart, "
                                                   "one sample at a time.")
        self.manualUpdateButton.clicked.connect(self.update_chart)
        self.monitorTabLayout.addWidget(self.manualUpdateButton)

        self.panel_title_font = QtGui.QFont("Calibri", 10, QtGui.QFont.Bold)
        self.subtitleFont = QtGui.QFont("Calibri", 9)
        self.minilabel_font = QtGui.QFont()
        self.minilabel_font.setItalic(True)

        self.monitorMenuLabel = SubLabel("Monitor settings:", self.panel_title_font)
        self.propertiesTabLayout.addWidget(self.monitorMenuLabel)

        self.samplesNumLabel = SubLabel("Number of samples:", self.subtitleFont)
        self.samplesNumSpinBox = QtWidgets.QSpinBox()
        self.samplesNumSpinBox.setRange(2, 50)
        self.samplesNumSpinBox.setValue(self.monitor.max_sample)
        self.samplesNumLayout = QtWidgets.QHBoxLayout()
        self.samplesNumSpinBox.valueChanged.connect(self.define_max_sample)
        self.samplesNumSpinBox.valueChanged.connect(self.update_chart)
        self.samplesNumSpinBox.valueChanged.connect(self.monitor.define_tick_count)
        self.samplesNumLayout.addWidget(self.samplesNumLabel, 2, QtCore.Qt.AlignLeft)
        self.samplesNumLayout.addWidget(self.samplesNumSpinBox, 1, QtCore.Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.samplesNumLayout)

        self.samplesNumSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.samplesNumSlider.setRange(2, 51)
        self.samplesNumSlider.setTickInterval(1)
        self.samplesNumSlider.setSliderPosition(self.monitor.max_sample)
        self.samplesNumSliderLayout = QtWidgets.QGridLayout()
        self.samplesNumSlider.setTickPosition(QtWidgets.QSlider.TicksBothSides)

        self.samplesNumSlider.valueChanged.connect(self.define_max_sample)
        self.samplesNumSlider.valueChanged.connect(self.update_chart)
        self.samplesNumSlider.valueChanged.connect(self.monitor.define_tick_count)
        self.samplesNumSliderLayout.addWidget(self.samplesNumSlider)
        self.propertiesTabLayout.addLayout(self.samplesNumSliderLayout)

        self.auTimerLabel = SubLabel("Auto-Update Timer:", self.subtitleFont)
        self.auTimeEditLabel = SubLabel("Hours:Minutes:Seconds", self.minilabel_font)
        self.auTimeEdit = QtWidgets.QTimeEdit()
        self.auTimerLabel.setToolTip(
            "Auto-Update Timer: Set a new timer (in seconds) \n If the value changes, it will automatically \n stops "
            "any auto-update running")
        self.auTimeEdit.setDisplayFormat("hh:mm:ss")
        self.timeDisplayed = QtCore.QTime(0, 0, self.loop_time)
        self.auTimeEdit.setTime(self.timeDisplayed)

        self.auTimeEdit.timeChanged.connect(lambda: self.worker.stop())
        self.auTimeEdit.timeChanged.connect(self.change_loop_time)

        self.auTimerLayout = QtWidgets.QHBoxLayout()
        self.auTimerLayout.addWidget(self.auTimerLabel, 4, QtCore.Qt.AlignLeft)
        self.auTimerLayout.addWidget(self.auTimeEditLabel, 1, QtCore.Qt.AlignRight)
        self.auTimerLayout.addWidget(self.auTimeEdit, 1, QtCore.Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.auTimerLayout)

        self.propertiesTabLayout.addWidget(QHLine())
        self.displayMenuLabel = SubLabel("Display settings:", self.panel_title_font)
        self.propertiesTabLayout.addWidget(self.displayMenuLabel)

        self.scaleAxisYLabel = SubLabel("Scale the Y-Axis to:", self.subtitleFont)
        self.highestListValueCB = QtWidgets.QCheckBox("Current highest memory value")
        self.highestListValueCB.setChecked(True)
        self.highestListValueCB.stateChanged.connect(self.cb_highest_value)
        self.maximumCacheCB = QtWidgets.QCheckBox("Total RAM allocated")
        self.maximumCacheCB.setChecked(False)
        self.maximumCacheCB.stateChanged.connect(self.cb_max_nuke_ram)
        self.scaleAxisYLayout = QtWidgets.QHBoxLayout()
        self.scaleAxisYLayout.addWidget(self.scaleAxisYLabel, 4, QtCore.Qt.AlignLeft)
        self.scaleAxisYLayout.addWidget(self.highestListValueCB, 1, QtCore.Qt.AlignRight)
        self.scaleAxisYLayout.addWidget(self.maximumCacheCB, 1, QtCore.Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.scaleAxisYLayout)

        self.bgColorLayout = ColorSettings("Background color:", self.define_color, "BG")
        self.propertiesTabLayout.addLayout(self.bgColorLayout)

        self.gridColorLayout = ColorSettings("Grid color:", self.define_color, "Grid")
        self.propertiesTabLayout.addLayout(self.gridColorLayout)

        self.lineColorLayout = ColorSettings("Line color:", self.define_color, "Line")
        self.propertiesTabLayout.addLayout(self.lineColorLayout)

        self.pointsColorLayout = ColorSettings("Points color:", self.define_color, "Points")
        self.propertiesTabLayout.addLayout(self.pointsColorLayout)

        self.axisLabelsColorLayout = ColorSettings("Axis labels color:", self.define_color, "AxisLabels")
        self.propertiesTabLayout.addLayout(self.axisLabelsColorLayout)

        self.axisTitlesColorLayout = ColorSettings("Axis titles color:", self.define_color, "AxisTitles")
        self.propertiesTabLayout.addLayout(self.axisTitlesColorLayout)

    def cb_highest_value(self, state):
        """Fit the chart axis Y to the memory list highest value.
        @param (Qt.Checked) state:
        State of the checkbox.
        @return (None):
        No return value.
        """
        if state == QtCore.Qt.Checked:
            self.monitor.axis_y.setRange(0, round(max(self.monitor.mem_list), -1) + 50)
            self.monitor.set_hlcb_area_gradient()
            self.maximumCacheCB.setChecked(False)
        else:
            self.monitor.axis_y.setRange(0, nk_value('max_usage'))
            self.monitor.set_mccb_area_gradient()
            self.highestListValueCB.setChecked(False)

    def cb_max_nuke_ram(self, state):
        """Fit the chart axis Y to the maximum Nuke can allocate on RAM.
        @param (Qt.Checked) state:
        State of the checkbox.
        @return (None):
        No return value.
        """
        if state == QtCore.Qt.Checked:
            self.monitor.axis_y.setRange(0, nk_value('max_usage'))
            self.monitor.set_mccb_area_gradient()
            self.highestListValueCB.setChecked(False)

        else:
            self.monitor.axis_y.setRange(0, round(max(self.monitor.mem_list), -1) + 50)
            self.monitor.set_hlcb_area_gradient()
            self.maximumCacheCB.setChecked(False)

    def change_loop_time(self, new_time):
        """Change the time desired for auto updates, and creates a new time worker in line with it.
        @param (int) new_time:
        Time entered by the user.
        @return (None):
        No return value.
        """
        num = QtCore.QTime(0, 0, 0).secsTo(new_time)
        self.loop_time = num
        self.worker = Worker(self.update_chart, (self.loop_time * 1000))
        self.autoUpdateStart.clicked.connect(self.worker.start)
        self.autoUpdateStop.clicked.connect(self.worker.stop)

    def define_color(self, target):
        """Opens up a ColorDialog and set the color chosen by the user to a specific target.
        @param (str) target:
        The target where the color needs to be set
        @return (None):
        No return value.
        """
        color_name = QtWidgets.QColorDialog.getColor()
        if color_name.isValid():
            if target == "BG":
                self.monitor.chart.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(color_name)))
            elif target == "Grid":
                self.monitor.axis_x.setGridLineColor(QtGui.QColor(color_name))
                self.monitor.axis_y.setGridLineColor(QtGui.QColor(color_name))
                self.monitor.axis_x.setMinorGridLineColor(QtGui.QColor(color_name))
                self.monitor.axis_y.setMinorGridLineColor(QtGui.QColor(color_name))
            elif target == "Line":
                self.monitor.upperSeries.setColor(QtGui.QColor(color_name))
            elif target == "Points":
                self.monitor.pointseries.setColor(QtGui.QColor(color_name))
            elif target == "AxisLabels":
                self.monitor.axis_x.setLabelsColor(QtGui.QColor(color_name))
                self.monitor.axis_y.setLabelsColor(QtGui.QColor(color_name))
            elif target == "AxisTitles":
                self.monitor.axis_x.setTitleBrush(QtGui.QBrush(QtGui.QColor(color_name)))
                self.monitor.axis_y.setTitleBrush(QtGui.QBrush(QtGui.QColor(color_name)))
            else:
                return None

    def define_max_sample(self, value):
        """Set a new max sample for the monitor and readapt the lists and widgets in consequence.
        @param (int) value:
        The new max sample.
        @return (None):
        No return value.
        """
        self.monitor.max_sample(value)
        lmod = ListsModifier(self.monitor.mem_list, self.monitor.dt_list, self.monitor.max_sample)
        lmod.resize()
        self.monitor.axis_x.setRange(0, self.monitor.max_sample)
        self.samplesNumSpinBox.setValue(self.monitor.max_sample)
        self.samplesNumSlider.setSliderPosition(self.monitor.max_samplee)

    def update_chart(self):
        """Updates monitor lists and the chart series.
        """
        lmod = ListsModifier(self.monitor.mem_list, self.monitor.dt_list, self.monitor.max_sample)
        lmod.update()
        if self.highestListValueCB.isChecked():
            self.monitor.axis_y.setRange(0, round(max(self.monitor.mem_list), -1) + 50)
        self.monitor.upperSeries.clear()
        self.monitor.pointseries.clear()
        self.monitor.append_series()
        self.monitor.update()


if __name__ == "__main__":
    mmWidget = MainPanel()
    mmWidget.resize(400, 200)
    mmWidget.show()
