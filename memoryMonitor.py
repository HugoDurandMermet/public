# ----------------------------------------------------------------------------------------------------------------------
#  memoryMonitor.py
#  Version: 20.0.0
#  Author: Hugo Durand-Mermet
#
#  Last Modified by: Hugo Durand-Mermet
#  Last Updated: January 9th, 2021
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
#  USAGE:
#
#  Creates a side panel to display your script's usage
#  of RAM. Can be updated manually or self-updated every time
#  interval you'll have set in the settings. 
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
#  ROOM FOR IMPROVEMENT: 
#  Need to refactor a lot of this script to fit more SOLID design guidelines and be less heavy handed.
#  A lot could probably be simplified and less prone to failures.
#  Will implement docstrings on next iteration.
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
#  INSTRUCTIONS: 
#
#  -Save this py script in /.nuke or your favourite folder. Make sure the folder path has been saved in the init.py
#  script.
#  -In your menu.py script, add the following lines: 
#
#  pane = nuke.getPaneFor('Properties.1')
#  panels.registerWidgetAsPanel('get_memory_monitor', 'Memory Monitor', 'ue.panel.ueSave', True).addToPane(pane)
# 
#  Add the following line if it isn't already in your menu.py script: 
#
#  import nukescripts
#
# -This script has been tested on a free trial version of Nuke12.2v3. If you have an older or a custom version of Nuke,
#  it's possible this script doesn't work as
#  expected, especially since it relies on modules to import. If that is the case, don't hesitate to reach out to me
#  through my GitHub.
# ----------------------------------------------------------------------------------------------------------------------


from PySide2 import QtWidgets, QtCore, QtGui, QtCharts
import datetime

import nuke
from nukescripts import panels

# -----------------------------------------------------------------------------------------------------
# ===============================
# === FUNCTIONS AND VARIABLES ===
# ===============================

maxSample = 20
memList = [0 for x in list(range(maxSample + 1))]
dateList = ["---" for y in list(range(maxSample + 1))]


def memory_retriever():
    memory_value = (nuke.memory('usage')) * 0.000001
    final_value = round(memory_value, 2)
    return final_value


# Functions below, will update, shrink or extend both lists depending on the maxSample value.


def lists_update():
    lists_length = len(memList) - 1
    current_mem_value = memory_retriever()
    current_date_time = datetime.datetime.now().strftime("%x - %X")
    if lists_length <= maxSample:
        memList.append(current_mem_value)
        dateList.append(current_date_time)
    else:
        memList.pop(0)
        dateList.pop(0)
        lists_update()


def lists_resize():
    if len(memList) > (maxSample + 1):
        while len(memList) > (maxSample + 1):
            memList.pop(0)
            dateList.pop(0)
            if len(memList) == (maxSample + 1):
                break
    elif len(memList) < (maxSample + 1):
        while len(memList) < (maxSample + 1):
            memList.append(0)
            memList.append("---")
            if len(memList) == (maxSample + 1):
                break
    else:
        return None


listLen = len(memList)
lastMemListValue = memList[listLen - 1]
range_list = list(range(listLen))

# This variable will be the one the auto-update feature will be based one. 
# Represents seconds.
loopTime = 10


# The next two function are here so they can be called for readjusting the Y-Axis of the monitor.


def list_highest_value():
    highest_value = 0
    for i in memList:
        if i > highest_value:
            highest_value = 1
    return highest_value


def get_list_max_y():
    max_value = list_highest_value()
    max_axis_y = round(max_value, -1)
    return max_axis_y


def get_max_nuke_ram():
    max_nuke_ram = (nuke.memory('max_usage')) * 0.000001
    final_max_ram = round(max_nuke_ram, 2)
    return final_max_ram


def perc_total_ram(number):
    total_ram = get_max_nuke_ram()
    percentage = (number / total_ram) * 100
    round_percentage = round(percentage, 2)
    return round_percentage


# my_multiplier purpose is to find a number that could fit well for the ticks to set on
# the X-Axis. You can ditch it in profit of the command applyNiceNumbers but I personally found that
# even though this add YET another function to the script, it provides better results than the former.


def my_multiplier(number):
    temp_list = []
    my_list = list(range(1, number))
    for i in my_list:
        if number % i == 0:
            temp_list.append(i)
    if len(temp_list) <= 3:
        return temp_list[-1]
    else:
        return temp_list[-2]


# -----------------------------------------------------------------------------------------------------
# ===============
# === CLASSES ===
# ===============

# QHLine class will create an horizontal line to be used as a separator.
# On a second thought, there might be more convenient ways to create one
# through a setStyledSheet or another command perhaps.
class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

    # Worker class is what will power the "Auto-Update" functionality.


class Worker(QtCore.QObject):
    def __init__(self, function, interval):
        super(Worker, self).__init__()
        self._funcion = function
        self._timer = QtCore.QTimer(self, interval=interval, timeout=self.execute)

    @property
    def running(self):
        return self._timer.isActive()

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.stop()

    def execute(self):
        self._funcion()


# Callout class will create the tooltip we want for each point on the scatter series line.


class Callout(QtWidgets.QGraphicsItem):
    def __init__(self, chart):
        QtWidgets.QGraphicsItem.__init__(self, chart)
        self._chart = chart
        self._text = ""
        self._textRect = QtCore.QRectF()
        self._anchor = QtCore.QPointF()
        self._font = QtGui.QFont()
        self._rect = QtCore.QRectF()

    def boundingRect(self):
        anchor = self.mapFromParent(self._chart.mapToPosition(self._anchor))
        rect = QtCore.QRectF()
        rect.setLeft(min(self._rect.left(), anchor.x()))
        rect.setRight(max(self._rect.right(), anchor.x()))
        rect.setTop(min(self._rect.top(), anchor.y()))
        rect.setBottom(max(self._rect.bottom(), anchor.y()))

        return rect

    def paint(self, painter, option, widget):
        path = QtGui.QPainterPath()
        path.addRoundedRect(self._rect, 5, 5)
        anchor = self.mapFromParent(self._chart.mapToPosition(self._anchor))
        if not self._rect.contains(anchor) and not self._anchor.isNull():
            point1 = QtCore.QPointF()
            point2 = QtCore.QPointF()

            path.moveTo(point1)
            path.lineTo(anchor)
            path.lineTo(point2)
            path = path.simplified()

        painter.setBrush(QtGui.QColor(171, 97, 7, 200))
        callout_pen = QtGui.QPen(QtGui.QColor(200, 200, 200))
        callout_pen.setWidth(3)
        painter.setPen(callout_pen)
        painter.drawPath(path)
        painter.drawText(self._textRect, self._text)

    def set_text(self, text):
        self._text = text
        metrics = QtGui.QFontMetrics(self._font)
        self._textRect = QtCore.QRectF(metrics.boundingRect(
            QtCore.QRect(0, -25, 0, 0), QtCore.Qt.AlignRight, self._text))
        self._textRect.translate(5, 5)
        self.prepareGeometryChange()
        self._rect = self._textRect.adjusted(-5, -5, 5, 5)

    def set_anchor(self, point):
        self._anchor = QtCore.QPointF(point)

    def update_geometry(self):
        self.prepareGeometryChange()
        self.setPos(self._chart.mapToPosition(
            self._anchor) + QtCore.QPointF(10, -50))


# Our Monitor will be set in this class, as from experience, I've found it
# interacts better when declared outside of our main one rather than trying
# to create a QGraphicsView inside our MainPanel.


class Monitor(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(Monitor, self).__init__(parent)
        self.setScene(QtWidgets.QGraphicsScene(self))

        self.setDragMode(QGraphicsView.NoDrag)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self._chart = QtCharts.QChart()
        self._chart.setBackgroundBrush(QtGui.QBrush(QtGui.QColor("black")))
        self._chart.setTitle("Hover the points to display individual values.")
        self._chart.legend().hide()

        # I've made the choice to go with two series, as a scatter one proved to
        # be easier to be customised than trying to modify the points of a QLineSeries
        self.upperSeries = QtCharts.QLineSeries()
        self.pointsSeries = QtCharts.QScatterSeries()
        self.upperSeries.setColor(QtGui.QColor("cyan"))
        self.pointsSeries.setColor(QtGui.QColor("cyan"))
        self.pointsSeries.setBorderColor(QtGui.QColor("transparent"))
        self.pointsSeries.setPointLabelsFormat("@yPoint")
        self.pointsSeries.setPointLabelsColor(QtGui.QColor("white"))
        self.pointsSeries.setPointLabelsClipping(False)
        self.pointsSeries.setMarkerSize(10)
        for index, value in enumerate(memList):
            self.upperSeries.append(index, value)
            self.pointsSeries.append(index, value)
        self._chart.addSeries(self.upperSeries)
        self._chart.addSeries(self.pointsSeries)
        self.axis_x = QtCharts.QValueAxis()
        self._chart.addAxis(self.axis_x, QtCore.Qt.AlignBottom)
        self.axis_y = QtCharts.QValueAxis()
        self._chart.addAxis(self.axis_y, QtCore.Qt.AlignLeft)
        self._chart.setAcceptHoverEvents(True)

        self.axis_x.setRange(0, maxSample)
        self.axis_y.setRange(0, get_list_max_y() + 50)

        self.axis_x.setMinorTickCount(4)
        self.axis_y.applyNiceNumbers()
        self.axis_x.setTitleText("Number of samples")
        self.axis_y.setTitleText("Memory (in MB)")
        title_color = QtGui.QBrush(QtGui.QColor("lightGrey"))
        self.axis_x.setTitleBrush(title_color)
        self.axis_y.setTitleBrush(title_color)
        self.axis_x.setLabelsColor(QtGui.QColor("grey"))
        self.axis_y.setLabelsColor(QtGui.QColor("grey"))
        title_font = QtGui.QFont("Calibri", 14, QtGui.QFont.Bold)
        label_font = QtGui.QFont("Calibri", 10, QtGui.QFont.Bold)
        self.axis_x.setTitleFont(title_font)
        self.axis_y.setTitleFont(title_font)
        self.axis_x.setLabelsFont(label_font)
        self.axis_y.setLabelsFont(label_font)

        self.upperSeries.attachAxis(self.axis_x)
        self.upperSeries.attachAxis(self.axis_y)
        self.pointsSeries.attachAxis(self.axis_x)
        self.pointsSeries.attachAxis(self.axis_y)
        self.areaSeries = QtCharts.QAreaSeries(self.upperSeries)
        self.areaPen = QtGui.QPen(Qt.cyan)
        self.areaPen.setWidth(3)
        self.areaSeries.setPen(self.areaPen)

        self._chart.addSeries(self.areaSeries)
        self.areaSeries.attachAxis(self.axis_x)
        self.areaSeries.attachAxis(self.axis_y)

        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.scene().addItem(self._chart)

        self._coordX = QtWidgets.QGraphicsSimpleTextItem(self._chart)
        self._tooltipFont = QtGui.QFont("Calibri", 7, QtGui.QFont.Bold)
        self._coordX.setPos(
            self._chart.size().width() / 2 - 50, self._chart.size().height())
        self._coordX.set_text("At sample ")

        self._coordY = QtWidgets.QGraphicsSimpleTextItem(self._chart)
        self._coordY.setPos(
            self._chart.size().width() / 2 + 50, self._chart.size().height())
        self._coordY.set_text("RAM used")

        self._callouts = []
        self._tooltip = Callout(self._chart)
        self.pointsSeries.hovered.connect(self.tooltip)

        self.setMouseTracking(True)

    def resizeEvent(self, event):
        if self.scene():
            self.scene().setSceneRect(QtCore.QRectF(QtCore.QPointF(0, 0), event.size()))
            self._chart.resize(event.size())
            self._coordX.setPos(
                self._chart.size().width() / 2 - 50,
                self._chart.size().height() - 20)
            self._coordY.setPos(
                self._chart.size().width() / 2 + 50,
                self._chart.size().height() - 20)
            for callout in self._callouts:
                callout.update_geometry()
        QtWidgets.QGraphicsView.resizeEvent(self, event)

    def keepCallout(self):
        self._callouts.append(self._tooltip)
        self._tooltip = Callout(self._chart)

    def tooltip(self, point, state):
        if self._tooltip == 0:
            self._tooltip = Callout(self._chart)

        if state:
            self._tooltip.set_text("{0:s}\nAt sample: {1:.2f} \nMemory used: {2:.2f}MB \nTotal RAM usage: {3:.2f}% "
                                   .format(dateList[int(point.x())], point.x(), point.y(),
                                           perc_total_ram(point.y())))
            self._tooltip.set_anchor(point)
            self._tooltip.setZValue(11)
            self._tooltip.update_geometry()
            self._tooltip.show()
        else:
            self._tooltip.hide()

    @property
    def chart(self):
        return self._chart


# MainPanel will feature our monitor, but also a lot settings buttons on the Properties tab.
# Feel free to remove some if you deem them useless.
class MainPanel(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
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
        self.worker = Worker(self.update_chart, (loopTime * 1000))

        self.autoUpdateLayout = QtWidgets.QHBoxLayout()
        self.autoUpdateStart = QtWidgets.QPushButton("Start Auto-Update")
        self.autoUpdateStart.setToolTip(
            "Start Auto-Update: Starts a loop that \n will automatically update the monitor, for every time interval "
            "\n you'll have set in the Properties panel (Default is 30 seconds)")
        self.autoUpdateStart.setCheckable(False)
        self.autoUpdateStart.toggle()
        self.autoUpdateStart.clicked.connect(self.worker.start)

        self.autoUpdateStop = QtWidgets.QPushButton("Stop Auto-Update")
        self.autoUpdateStop.setToolTip("Stop Auto-Update: Stops the \n currently running Auto-Update.")
        self.autoUpdateStop.setCheckable(False)
        self.autoUpdateStop.toggle()
        self.autoUpdateStop.clicked.connect(self.worker.stop)

        self.autoUpdateLayout.addWidget(self.autoUpdateStart)
        self.autoUpdateLayout.addWidget(self.autoUpdateStop)
        self.monitorTabLayout.addLayout(self.autoUpdateLayout)

        self.manualUpdateButton = QtWidgets.QPushButton("Manual Update")
        self.manualUpdateButton.setToolTip(
            "Manual Update: Click it to manually update \n the chart, one sample at a time.")
        self.manualUpdateButton.setCheckable(False)
        self.manualUpdateButton.toggle()
        self.manualUpdateButton.clicked.connect(self.update_chart)
        self.monitorTabLayout.addWidget(self.manualUpdateButton)
        panel_title_font = QtGui.QFont("Calibri", 10, QtGui.QFont.Bold)
        self.monitorMenuLabel = QtWidgets.QLabel("Monitor settings:")
        self.monitorMenuLabel.setFont(panel_title_font)
        self.propertiesTabLayout.addWidget(self.monitorMenuLabel)

        self.subtitleFont = QtGui.QFont("Calibri", 9)

        self.samplesNumLabel = QtWidgets.QLabel("Number of samples:")
        self.samplesNumLabel.setFont(self.subtitleFont)
        self.samplesNumSpinBox = QtWidgets.QSpinBox()
        self.samplesNumSpinBox.setRange(2, 50)
        self.samplesNumSpinBox.setValue(maxSample)
        self.samplesNumLayout = QtWidgets.QHBoxLayout()
        self.samplesNumSpinBox.valueChanged.connect(self.define_max_sample)
        self.samplesNumSpinBox.valueChanged.connect(self.update_chart)
        self.samplesNumSpinBox.valueChanged.connect(self.define_tick_count)
        self.samplesNumLayout.addWidget(self.samplesNumLabel, 2, QtCore.Qt.AlignLeft)
        self.samplesNumLayout.addWidget(self.samplesNumSpinBox, 1, QtCore.Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.samplesNumLayout)

        self.samplesNumSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.samplesNumSlider.setRange(2, 51)
        self.samplesNumSlider.setTickInterval(1)
        self.samplesNumSlider.setSliderPosition(maxSample)
        self.samplesNumSliderLayout = QtWidgets.QGridLayout()
        self.samplesNumSlider.setTickPosition(QtWidgets.QSlider.TicksBothSides)

        self.samplesNumSlider.valueChanged.connect(self.define_max_sample)
        self.samplesNumSlider.valueChanged.connect(self.update_chart)
        self.samplesNumSlider.valueChanged.connect(self.define_tick_count)
        self.samplesNumSliderLayout.addWidget(self.samplesNumSlider)
        self.propertiesTabLayout.addLayout(self.samplesNumSliderLayout)

        self.auTimerLabel = QtWidgets.QLabel("Auto-Update Timer:")
        self.auTimerLabel.setFont(self.subtitleFont)
        self.minilabel_font = QtGui.QFont()
        self.minilabel_font.setItalic(True)
        self.auTimeEditLabel = QtWidgets.QLabel("Hours:Minutes:Seconds")
        self.auTimeEditLabel.setFont(self.minilabel_font)
        self.auTimeEdit = QtWidgets.QTimeEdit()
        self.auTimerLabel.setToolTip(
            "Auto-Update Timer: Set a new timer (in seconds) \n If the value changes, it will automatically \n stops "
            "any auto-update running")
        self.auTimeEdit.setDisplayFormat("hh:mm:ss")
        self.timeDisplayed = QtCore.QTime(0, 0, loopTime)
        self.auTimeEdit.setTime(self.timeDisplayed)

        self.auTimeEdit.timeChanged.connect(lambda: self.worker.stop())
        self.auTimeEdit.timeChanged.connect(self.change_loop_time)

        self.auTimerLayout = QtWidgets.QHBoxLayout()
        self.auTimerLayout.addWidget(self.auTimerLabel, 4, QtCore.Qt.AlignLeft)
        self.auTimerLayout.addWidget(self.auTimeEditLabel, 1, QtCore.Qt.AlignRight)
        self.auTimerLayout.addWidget(self.auTimeEdit, 1, QtCore.Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.auTimerLayout)

        self.propertiesTabLayout.addWidget(QHLine())
        self.displayMenuLabel = QtWidgets.QLabel("Display settings:")

        self.displayMenuLabel.setFont(panel_title_font)
        self.propertiesTabLayout.addWidget(self.displayMenuLabel)

        self.scaleAxisYLabel = QtWidgets.QLabel("Scale the Y-Axis to:")
        self.scaleAxisYLabel.setFont(self.subtitleFont)
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

        # Normally (I say normally as I haven't stress tested a nuke script to the point of reaching max RAM usage -
        # I know shame on me-), this gradient will go from green when the memvalue appended in the series use the
        # lowest amount of ram, to red when it comes close to the max allocated, with yellow acting as an
        # intermediate color.
        self.areaGradient = QtGui.QLinearGradient(QtCore.QPointF(0, 0), QtCore.QPointF(0, 1))
        if self.maximumCacheCB.isChecked():
            self.areaGradient.setColorAt(0.0, QtGui.QColor(255, 0, 0, 180))
            self.areaGradient.setColorAt(0.5, QtGui.QColor(255, 255, 0, 120))
            self.areaGradient.setColorAt(1, QtGui.QColor(0, 255, 0, 60))
        elif self.highestListValueCB.isChecked():
            self.totalByUsageDivision = nuke.memory('usage') / nuke.memory('max_usage')
            self.areaGradient.setColorAt(0.0, QtGui.QColor(255, 0, 0, 180))
            self.areaGradient.setColorAt((self.totalByUsageDivision * 0.5), QtGui.QColor(255, 255, 0, 120))
            self.areaGradient.setColorAt(self.totalByUsageDivision, QtGui.QColor(0, 255, 0, 60))
        self.areaGradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
        self.monitor.areaSeries.setBrush(self.areaGradient)

        self.bgColorLayout = self.create_color_settings("Background color:", self.define_color, "BG")
        self.propertiesTabLayout.addLayout(self.bgColorLayout)

        self.gridColorLayout = self.create_color_settings("Grid color:", self.define_color, "Grid")
        self.propertiesTabLayout.addLayout(self.gridColorLayout)

        self.lineColorLayout = self.create_color_settings("Line color:", self.define_color, "Line")
        self.propertiesTabLayout.addLayout(self.lineColorLayout)

        self.pointsColorLayout = self.create_color_settings("Points color:", self.define_color, "Points")
        self.propertiesTabLayout.addLayout(self.pointsColorLayout)

        self.axisLabelsColorLayout = self.create_color_settings("Axis labels color:", self.define_color, "AxisLabels")
        self.propertiesTabLayout.addLayout(self.axisLabelsColorLayout)

        self.axisTitlesColorLayout = self.create_color_settings("Axis titles color:", self.define_color, "AxisTitles")
        self.propertiesTabLayout.addLayout(self.axisTitlesColorLayout)

    # A series of functions dedicated to set color of the elements featured in the monitor.

    def create_color_settings(self, label, signal, target):
        color_label = QtWidgets.QtWidgets.QLabel(label)
        color_label.setFont(self.subtitleFont)
        color_button = QtWidgets.QPushButton('Open color dialog', self)
        color_button.clicked.connect(lambda: signal(target))
        color_layout = QtWidgets.QHBoxLayout()
        color_layout.addWidget(color_label, 4, QtCore.Qt.AlignLeft)
        color_layout.addWidget(color_button, 1, QtCore.Qt.AlignRight)
        return color_layout

    def define_color(self, target):
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

    # This is the core of this script. Will update both lists so they can be used to re-append
    # existing chart series.
    def update_chart(self):
        lists_update()
        if self.highestListValueCB.isChecked():
            self.monitor.axis_y.setRange(0, get_list_max_y() + 50)
        self.monitor.upperSeries.clear()
        self.monitor.pointseries.clear()
        for index, value in enumerate(memList):
            self.monitor.upperSeries.append(index, value)
            self.monitor.pointseries.append(index, value)
        self.monitor.update()

    # Once a new number has been entered, both lists will be either reduced or extended.
    # Will also update the X-Axis.
    def define_max_sample(self, value):
        global maxSample
        maxSample = value
        lists_resize()
        self.monitor.axis_x.setRange(0, maxSample)
        self.samplesNumSpinBox.setValue(maxSample)
        self.samplesNumSlider.setSliderPosition(maxSample)

    # The function calling on my_multiplier.
    # Again you can remove it in profit of applyNiceNumbers (IMO I prefer the results of this one)
    def define_tick_count(self):
        tick_count_num = my_multiplier(maxSample) + 1
        self.monitor.axis_x.setTickCount(tick_count_num)
        minor_tick_count_num = (maxSample / tick_count_num)
        self.monitor.axis_x.setMinorTickCount(minor_tick_count_num)

    # Our time box for changing the time loop. 
    # If a new value is entered, any running worker will stop and will need to be restarted.
    def change_loop_time(self, new_time):
        num = QtCore.QTime(0, 0, 0).secsTo(new_time)
        global loopTime
        loopTime = num
        self.worker = Worker(self.update_chart, (loopTime * 1000))
        self.autoUpdateStart.clicked.connect(self.worker.start)
        self.autoUpdateStop.clicked.connect(self.worker.stop)

    # Two functions for resizing the Y-Axis to the scale you want.
    def cb_highest_value(self, state):
        if state == QtCore.Qt.Checked:
            self.monitor.axis_y.setRange(0, get_list_max_y() + 50)
            self.maximumCacheCB.setChecked(False)

        else:
            self.monitor.axis_y.setRange(0, get_max_nuke_ram())
            self.highestListValueCB.setChecked(False)

    def cb_max_nuke_ram(self, state):
        if state == QtCore.Qt.Checked:
            self.monitor.axis_y.setRange(0, get_max_nuke_ram())
            self.highestListValueCB.setChecked(False)

        else:
            self.monitor.axis_y.setRange(0, get_list_max_y() + 50)
            self.maximumCacheCB.setChecked(False)


if __name__ == "__main__":
    mmWidget = MainPanel()
    mmWidget.resize(400, 200)
    mmWidget.show()
