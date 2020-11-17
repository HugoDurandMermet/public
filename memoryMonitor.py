# --------------------------------------------------------------
#  memoryMonitor.py
#  Version: 18.2.0
#  Author: Hugo Durand-Mermet
#
#  Last Modified by: Hugo Durand-Mermet
#  Last Updated: November 27th, 2020
# --------------------------------------------------------------

# --------------------------------------------------------------
#  USAGE:
#
#  Creates a side panel to display your script's usage
#  of RAM. Can be updated manually or self-updated every time
#  interval you'll have set in the settings. 
# --------------------------------------------------------------

# --------------------------------------------------------------
#  ROOM FOR IMPROVEMENT: 
#
#  I have pretty much achieved what I wanted to do with this 
#  script. Still, this is my first Nuke tool, and a lot of work
#  could probably be simplified (With over 700 lines this is 
#  definitely a chunky boi)
# --------------------------------------------------------------

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  INSTRUCTIONS: 
#
#  -Save this py script in /.nuke or your favourite folder. Make sure the folder path has been saved in the init.py script.
#  -In your menu.py script, add the following lines: 
#
#  pane = nuke.getPaneFor('Properties.1')
#  panels.registerWidgetAsPanel('get_memory_monitor', 'Memory Monitor', 'ue.panel.ueSave', True).addToPane(pane)
# 
#  Add the following line if it isn't already in your menu.py script: 
#
#  import nukescripts
#
# -This script has been tested on a free trial version of Nuke12.2v3. If you have an older or a custom version of Nuke, it's possible this script doesn't work as
#  expected, especially since it relies on modules to import. If that is the case, don't hesitate to reach out to me through my GitHub. 
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------


from PySide2.QtCore import *
from PySide2 import *
from PySide2.QtWidgets import *
from PySide2.QtCharts import *
from PySide2.QtGui import *

from nukescripts import panels
import datetime
import nuke    
        


# -----------------------------------------------------------------------------------------------------
# ===============================
# === FUNCTIONS AND VARIABLES ===
# ===============================

memValuesList = []
# DateTime list will be mostly used through the scatter line tooltips.
dateTimeList = []
maxSample = 20

def memoryRetriever():
    
    memoryValue = nuke.memory('usage')
    memoryValueAsMB = memoryValue * 0.000001
    finalValue = round(memoryValueAsMB, 2)
    
    return finalValue

# The following conditions are here so that both lists aren't empty when the panel starts. 
# You can replace 0 or --- by anything you want.
while len(memValuesList) < (maxSample + 1):
    memValuesList.append(0)
    if len(memValuesList) == (maxSample + 1): 
        break
    
while len(dateTimeList) < (maxSample + 1): 
    dateTimeList.append("---")
    if len(dateTimeList) == (maxSample + 1): 
        break

# Functions below, will update, shrink or extend both lists depending on the maxSample value.
def memoryListUpdate(): 
    listLength = len(memValuesList) - 1
    currentMemValue = memoryRetriever()
    if listLength <= maxSample: 
        memValuesList.append(currentMemValue)
    else: 
        memValuesList.pop(0)
        memValuesList.append(currentMemValue)

def memValuesListShrinker():
    while len(memValuesList) > (maxSample + 1): 
        memValuesList.pop(0)
        if len(memValuesList) == (maxSample + 1): 
            break
        
def memValuesListExtender(): 
    while len(memValuesList) < (maxSample +1): 
        memValuesList.insert(0, 0)
        if len(memValuesList) == (maxSample + 1): 
            break
        
def dateTimeListUpdate(): 
    dtlistLength = len(dateTimeList)
    currentDateTime = datetime.datetime.now().strftime("%x - %X")
    if dtlistLength <= maxSample: 
        dateTimeList.append(currentDateTime)
    else:
        dateTimeList.pop(0)
        dateTimeList.append(currentDateTime)
        
def dateTimeListShrinker(): 
    while len(dateTimeList) > (maxSample +1): 
        dateTimeList.pop(0)
        if len(dateTimeList) == (maxSample +1): 
            break  

def dateTimeListExtender(): 
    while len(dateTimeList) < (maxSample +1): 
        dateTimeList.insert(0, "---")
        if len(dateTimeList) == (maxSample +1):
            break




currentMemListLen = len(memValuesList)
lastListValue = memValuesList[currentMemListLen -1]
rangeList = list(range(currentMemListLen)) 

# This variable will be the one the auto-update feature will be based one. 
# Represents seconds.
loopTime = 10

# The next two function are here so they can be called for readjusting the Y-Axis of the monitor.
def listHighestValue(): 
    highestValue = 0
    for i in memValuesList: 
        if i > highestValue: 
            highestValue = i
    return highestValue

def getListMaxY():
    maxValue = listHighestValue()
    maxAxisY = round(maxValue, -1)
    return maxAxisY

def getMaxNukeRAM(): 
    MaxNukeRAM = nuke.memory('max_usage')
    MaxNukeRAMInMB = MaxNukeRAM * 0.000001
    finalMaxNukeRAM = round(MaxNukeRAMInMB, 2)
    return finalMaxNukeRAM

def percentageOfTotalRAM(number):
    totalRAM = getMaxNukeRAM()
    percentage = (number / totalRAM) * 100 
    roundPercentage = round(percentage, 2)
    return roundPercentage

# FindAppropriateMultiplier purpose is to find a number that could fit well for the ticks to set on
# the X-Axis. You can ditch it in profit of the command applyNiceNumbers but I personally found that
# even though this add YET another function to the script, it provides better results than the former.
def findAppropriateMultiplier(number):
    temporaryMultList = []
    rangeList = list(range(1,number))
    for i in rangeList: 
        if number % i ==0:
            temporaryMultList.append(i)
    if len(temporaryMultList) <= 3: 
        return temporaryMultList[-1]
    else: 
        return temporaryMultList[-2]
    



# -----------------------------------------------------------------------------------------------------
# ===============
# === CLASSES ===
# ===============

# QHLine class will create an horizontal line to be used as a separator.
# On a second thought, there might be more convenient ways to create one
# through a setStyledSheet or another command perhaps.
class QHLine(QFrame): 
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
class Callout(QGraphicsItem):

    def __init__(self, chart):
        QGraphicsItem.__init__(self, chart)
        self._chart = chart
        self._text = ""
        self._textRect = QRectF()
        self._anchor = QPointF()
        self._font = QFont()
        self._rect = QRectF()

    def boundingRect(self):
        anchor = self.mapFromParent(self._chart.mapToPosition(self._anchor))
        rect = QRectF()
        rect.setLeft(min(self._rect.left(), anchor.x()))
        rect.setRight(max(self._rect.right(), anchor.x()))
        rect.setTop(min(self._rect.top(), anchor.y()))
        rect.setBottom(max(self._rect.bottom(), anchor.y()))

        return rect

    def paint(self, painter, option, widget):
        path = QPainterPath()
        path.addRoundedRect(self._rect, 5, 5)
        anchor = self.mapFromParent(self._chart.mapToPosition(self._anchor))
        if not self._rect.contains(anchor) and not self._anchor.isNull():
            point1 = QPointF()
            point2 = QPointF()

            path.moveTo(point1)
            path.lineTo(anchor)
            path.lineTo(point2)
            path = path.simplified()

        painter.setBrush(QColor(171, 97, 7, 200))
        calloutPen = QPen(QColor(200, 200, 200))
        calloutPen.setWidth(3)
        painter.setPen(calloutPen)
        painter.drawPath(path)
        painter.drawText(self._textRect, self._text)

    def mousePressEvent(self, event):
        event.setAccepted(False)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.setPos(mapToParent(
                event.pos() - event.buttonDownPos(Qt.LeftButton)))
            event.setAccepted(True)
        else:
            event.setAccepted(False)

    def setText(self, text):
        self._text = text
        metrics = QFontMetrics(self._font)
        self._textRect = QRectF(metrics.boundingRect(
            QRect(0.0, -25.0, 0.0, 0.0),Qt.AlignRight, self._text))
        self._textRect.translate(5, 5)
        self.prepareGeometryChange()
        self._rect = self._textRect.adjusted(-5, -5, 5, 5)

    def setAnchor(self, point):
        self._anchor = QPointF(point)

    def updateGeometry(self):
        self.prepareGeometryChange()
        self.setPos(self._chart.mapToPosition(
            self._anchor) + QPointF(10, -50))

# Our Monitor will be set in this class, as from experience, I've found it
# interacts better when declared outside of our main one rather than trying
# to create a QGraphicsView inside our MainPanel.
class Monitor(QGraphicsView):
    def __init__(self, parent = None):
        super(Monitor, self).__init__(parent)
        self.setScene(QGraphicsScene(self))

        self.setDragMode(QGraphicsView.NoDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


        self._chart = QtCharts.QChart()
        self._chart.setBackgroundBrush(QBrush(QColor("black")))
        self._chart.setTitle("Hover the points to display individual values.")
        self._chart.legend().hide()

        # I've made the choice to go with two series, as a scatter one proved to
        # be easier to be customised than trying to modify the points of a QLineSeries
        self.upperSeries = QtCharts.QLineSeries()
        self.pointseries = QtCharts.QScatterSeries()
        self.upperSeries.setColor(QtGui.QColor("cyan"))
        self.pointseries.setColor(QtGui.QColor("cyan"))
        self.pointseries.setBorderColor(QtGui.QColor("transparent"))
        self.pointseries.setPointLabelsFormat("@yPoint")
        self.pointseries.setPointLabelsColor(QtGui.QColor("white"))
        self.pointseries.setPointLabelsClipping(False)
        self.pointseries.setMarkerSize(10)
        for i in rangeList:
            self.upperSeries.append(i,memValuesList[i])
            self.pointseries.append(i, memValuesList[i])
        self._chart.addSeries(self.upperSeries)
        self._chart.addSeries(self.pointseries)
        self.axis_x = QtCharts.QValueAxis()
        self._chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.axis_y = QtCharts.QValueAxis()
        self._chart.addAxis(self.axis_y, Qt.AlignLeft)
        self._chart.setAcceptHoverEvents(True)

        self.axis_x.setRange(0, maxSample)
        self.axis_y.setRange(0, getListMaxY() + 50)
       

        self.axis_x.setMinorTickCount(4)
        self.axis_y.applyNiceNumbers()
        self.axis_x.setTitleText("Number of samples")
        self.axis_y.setTitleText("Memory (in MB)")
        titleColor = QtGui.QBrush(QtGui.QColor("lightGrey"))
        self.axis_x.setTitleBrush(titleColor)
        self.axis_y.setTitleBrush(titleColor)
        self.axis_x.setLabelsColor(QtGui.QColor("grey"))
        self.axis_y.setLabelsColor(QtGui.QColor("grey"))
        titleFont = QFont("Calibri", 14, QFont.Bold)
        labelFont = QFont("Calibri", 10, QFont.Bold)
        self.axis_x.setTitleFont(titleFont)
        self.axis_y.setTitleFont(titleFont)
        self.axis_x.setLabelsFont(labelFont)
        self.axis_y.setLabelsFont(labelFont)
        
        self.upperSeries.attachAxis(self.axis_x)
        self.upperSeries.attachAxis(self.axis_y)
        self.pointseries.attachAxis(self.axis_x)
        self.pointseries.attachAxis(self.axis_y)
        self.areaSeries = QtCharts.QAreaSeries(self.upperSeries)
        self.areaPen = QPen(Qt.cyan)
        self.areaPen.setWidth(3)
        self.areaSeries.setPen(self.areaPen)
        


        self._chart.addSeries(self.areaSeries)
        self.areaSeries.attachAxis(self.axis_x)
        self.areaSeries.attachAxis(self.axis_y)

        self.setRenderHint(QPainter.Antialiasing)
        self.scene().addItem(self._chart)

        self._coordX = QGraphicsSimpleTextItem(self._chart)
        self._tooltipFont = QFont("Calibri", 7, QFont.Bold)
        self._coordX.setPos(
            self._chart.size().width()/2 - 50, self._chart.size().height())
        self._coordX.setText("At sample ")


        self._coordY = QGraphicsSimpleTextItem(self._chart)
        self._coordY.setPos(
            self._chart.size().width()/2 + 50, self._chart.size().height())
        self._coordY.setText("RAM used")

        self._callouts = []
        self._tooltip = Callout(self._chart)
        self.pointseries.hovered.connect(self.tooltip)


        self.setMouseTracking(True)

    def resizeEvent(self, event):
        if self.scene():
            self.scene().setSceneRect(QRectF(QPointF(0, 0), event.size()))
            self._chart.resize(event.size())
            self._coordX.setPos(
                self._chart.size().width()/2 - 50,
                self._chart.size().height() - 20)
            self._coordY.setPos(
                self._chart.size().width()/2 + 50,
                self._chart.size().height() - 20)
            for callout in self._callouts:
                callout.updateGeometry()
        QGraphicsView.resizeEvent(self, event)


    def mouseMoveEvent(self, event):
        self._coordX.setText("At sample: {0:.2f}"
            .format(self._chart.mapToValue(event.pos()).x()))

        self._coordY.setText("RAM used: {0:.2f} MB"
            .format(self._chart.mapToValue(event.pos()).y()))


        QGraphicsView.mouseMoveEvent(self, event)

    def keepCallout(self):
        self._callouts.append(self._tooltip)
        self._tooltip = Callout(self._chart)

    def tooltip(self, point, state):
        if self._tooltip == 0:
            self._tooltip = Callout(self._chart)

        if state:
            self._tooltip.setText("{0:s}\nAt sample: {1:.2f} \nMemory used: {2:.2f}MB \nTotal RAM usage: {3:.2f}% "
                .format(dateTimeList[int(point.x())], point.x(),point.y(), percentageOfTotalRAM(point.y())))
            self._tooltip.setAnchor(point)
            self._tooltip.setZValue(11)
            self._tooltip.updateGeometry()
            self._tooltip.show()
        else:
            self._tooltip.hide()

# MainPanel will feature our monitor, but also a lot settings buttons on the Properties tab.
# Feel free to remove some if you deem them useless.
class MainPanel(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.tabBar = QTabWidget()
        self.layout.addWidget(self.tabBar)
        self.setLayout(self.layout)
        self.monitorTab = QWidget()
        self.propertiesTab = QWidget()
        self.tabBar.addTab(self.monitorTab, "Monitor")
        self.tabBar.addTab(self.propertiesTab, "Properties")
        self.monitorTabLayout = QVBoxLayout()
        self.monitorTab.setLayout(self.monitorTabLayout)
        self.propertiesTabLayout = QVBoxLayout()
        self.propertiesTab.setLayout(self.propertiesTabLayout)
        self.monitor = Monitor(self)

        self.monitorTabLayout.addWidget(self.monitor)
        self.worker = Worker(self.update_chart, (loopTime * 1000))
        
        
        self.autoUpdateLayout = QHBoxLayout()
        self.autoUpdateStart = QPushButton("Start Auto-Update")
        self.autoUpdateStart.setToolTip("Start Auto-Update: Starts a loop that \n will automatically update the monitor, for every time interval \n you'll have set in the Properties panel (Default is 30 seconds)")
        self.autoUpdateStart.setCheckable(False)
        self.autoUpdateStart.toggle()
        self.autoUpdateStart.clicked.connect(self.worker.start)
        
        self.autoUpdateStop = QPushButton("Stop Auto-Update")
        self.autoUpdateStop.setToolTip("Stop Auto-Update: Stops the \n currently running Auto-Update.")
        self.autoUpdateStop.setCheckable(False)
        self.autoUpdateStop.toggle()
        self.autoUpdateStop.clicked.connect(self.worker.stop)
        
        self.autoUpdateLayout.addWidget(self.autoUpdateStart)
        self.autoUpdateLayout.addWidget(self.autoUpdateStop)
        self.monitorTabLayout.addLayout(self.autoUpdateLayout)
        
        self.autoUpdateLayout.addWidget(self.autoUpdateStart)
        self.autoUpdateLayout.addWidget(self.autoUpdateStop)
        self.monitorTabLayout.addLayout(self.autoUpdateLayout)
        
        self.manualUpdateButton = QPushButton("Manual Update")
        self.manualUpdateButton.setToolTip("Manual Update: Click it to manually update \n the chart, one sample at a time.")
        self.manualUpdateButton.setCheckable(False)
        self.manualUpdateButton.toggle()
        self.manualUpdateButton.clicked.connect(self.update_chart)
        self.monitorTabLayout.addWidget(self.manualUpdateButton)
        panelTitleFont = QFont("Calibri", 10, QFont.Bold)
        self.monitorMenuLabel = QLabel("Monitor settings:")
        self.monitorMenuLabel.setFont(panelTitleFont)
        self.propertiesTabLayout.addWidget(self.monitorMenuLabel)
        
        subTitleFont = QFont("Calibri", 9)
        
        self.samplesNumLabel = QLabel("Number of samples:")
        self.samplesNumLabel.setFont(subTitleFont)
        self.samplesNumSpinBox = QSpinBox()
        self.samplesNumSpinBox.setRange(2,50)
        self.samplesNumSpinBox.setValue(maxSample)
        self.samplesNumLayout = QHBoxLayout()
        self.samplesNumSpinBox.valueChanged.connect(self.defineMaxSample)
        self.samplesNumSpinBox.valueChanged.connect(self.update_chart)
        self.samplesNumSpinBox.valueChanged.connect(self.defineTickCount)
        self.samplesNumLayout.addWidget(self.samplesNumLabel, 2, Qt.AlignLeft)
        self.samplesNumLayout.addWidget(self.samplesNumSpinBox, 1, Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.samplesNumLayout)
        
        self.samplesNumSlider = QSlider(Qt.Horizontal, self)
        self.samplesNumSlider.setRange(2,51)
        self.samplesNumSlider.setTickInterval(1)
        self.samplesNumSlider.setSliderPosition(maxSample)
        self.samplesNumSliderLayout = QGridLayout()
        self.samplesNumSlider.setTickPosition(QSlider.TicksBothSides)
        
        self.samplesNumSlider.valueChanged.connect(self.defineMaxSample)
        self.samplesNumSlider.valueChanged.connect(self.update_chart)
        self.samplesNumSlider.valueChanged.connect(self.defineTickCount)
        self.samplesNumSliderLayout.addWidget(self.samplesNumSlider)
        self.propertiesTabLayout.addLayout(self.samplesNumSliderLayout)
        
        self.auTimerLabel = QLabel("Auto-Update Timer:")
        self.auTimerLabel.setFont(subTitleFont)
        self.miniLabelFont = QFont()
        self.miniLabelFont.setItalic(True)
        self.auTimeEditLabel = QLabel("Hours:Minutes:Seconds")
        self.auTimeEditLabel.setFont(self.miniLabelFont)
        self.auTimeEdit = QTimeEdit()
        self.auTimerLabel.setToolTip("Auto-Update Timer: Set a new timer (in seconds) \n If the value changes, it will automatically \n stops any auto-update running")
        self.auTimeEdit.setDisplayFormat("hh:mm:ss")
        self.timeDisplayed = QTime(0, 0, loopTime)
        self.auTimeEdit.setTime(self.timeDisplayed)


        self.auTimeEdit.timeChanged.connect(lambda: self.worker.stop())
        self.auTimeEdit.timeChanged.connect(self.changeLoopTime)
        
        self.auTimerLayout = QHBoxLayout()
        self.auTimerLayout.addWidget(self.auTimerLabel, 4, Qt.AlignLeft)
        self.auTimerLayout.addWidget(self.auTimeEditLabel, 1, Qt.AlignRight)
        self.auTimerLayout.addWidget(self.auTimeEdit, 1, Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.auTimerLayout)

        self.propertiesTabLayout.addWidget(QHLine())
        self.displayMenuLabel = QLabel("Display settings:")

        self.displayMenuLabel.setFont(panelTitleFont)
        self.propertiesTabLayout.addWidget(self.displayMenuLabel)
        
        self.scaleAxisYLabel = QLabel("Scale the Y-Axis to:")
        self.scaleAxisYLabel.setFont(subTitleFont)
        self.highestListValueCB = QCheckBox("Current highest memory value")
        self.highestListValueCB.setChecked(True)
        self.highestListValueCB.stateChanged.connect(self.highestValueCheckboxFunction)
        self.maximumCacheCB = QCheckBox("Total RAM allocated")
        self.maximumCacheCB.setChecked(False)
        self.maximumCacheCB.stateChanged.connect(self.MaxNukeRAMCheckboxFunction)
        self.scaleAxisYLayout = QHBoxLayout()
        self.scaleAxisYLayout.addWidget(self.scaleAxisYLabel, 4, Qt.AlignLeft)
        self.scaleAxisYLayout.addWidget(self.highestListValueCB, 1, Qt.AlignRight)
        self.scaleAxisYLayout.addWidget(self.maximumCacheCB, 1, Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.scaleAxisYLayout)

        # Normally (I say normally as I haven't stress tested a nuke script to the point of reaching max RAM usage - I know shame on me-),
        # this gradient will go from green when the memvalue appended in the series use the lowest amount of ram, to red when it comes
        # close to the max allocated, with yellow acting as an intermediate color.
        self.areaGradient = QLinearGradient(QPointF(0, 0), QPointF(0, 1)) 
        if self.maximumCacheCB.isChecked() == True:
            self.areaGradient.setColorAt(0.0, QColor(255, 0, 0, 180))
            self.areaGradient.setColorAt(0.5, QColor(255, 255, 0, 120))
            self.areaGradient.setColorAt(1, QColor(0, 255, 0, 60))
        elif self.highestListValueCB.isChecked() == True:
            self.totalByUsageDivision = nuke.memory('usage') / nuke.memory('max_usage')
            self.areaGradient.setColorAt(0.0, QColor(255, 0, 0, 180))
            self.areaGradient.setColorAt((self.totalByUsageDivision * 0.5), QColor(255, 255, 0, 120))
            self.areaGradient.setColorAt(self.totalByUsageDivision, QColor(0, 255, 0, 60))
        self.areaGradient.setCoordinateMode(QGradient.ObjectBoundingMode)
        self.monitor.areaSeries.setBrush(self.areaGradient)

        self.bgColorLabel = QLabel("Background color:")
        self.bgColorLabel.setFont(subTitleFont)
        self.bgColorButton = QPushButton('Open color dialog', self)
        self.bgColorButton.clicked.connect(self.defineBGColor)
        self.bgColorLayout = QHBoxLayout()
        self.bgColorLayout.addWidget(self.bgColorLabel, 4, Qt.AlignLeft)
        self.bgColorLayout.addWidget(self.bgColorButton, 1, Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.bgColorLayout)
        
        
        self.gridColorLabel = QLabel("Grid color:")
        self.gridColorLabel.setFont(subTitleFont)
        self.gridColorButton = QPushButton('Open color dialog', self)
        self.gridColorButton.clicked.connect(self.defineGridColor)
        self.gridColorLayout = QHBoxLayout()
        self.gridColorLayout.addWidget(self.gridColorLabel, 4, Qt.AlignLeft)
        self.gridColorLayout.addWidget(self.gridColorButton, 1, Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.gridColorLayout) 
        
        self.lineColorLabel = QLabel("Line color:")
        self.lineColorLabel.setFont(subTitleFont)
        self.lineColorButton = QPushButton('Open color dialog', self)
        self.lineColorButton.clicked.connect(self.defineLineColor)
        self.lineColorLayout = QHBoxLayout()
        self.lineColorLayout.addWidget(self.lineColorLabel, 4, Qt.AlignLeft)
        self.lineColorLayout.addWidget(self.lineColorButton, 1, Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.lineColorLayout)
        
        self.pointsColorLabel = QLabel("Points color:")
        self.pointsColorLabel.setFont(subTitleFont)
        self.pointsColorButton = QPushButton('Open color dialog', self)
        self.pointsColorButton.clicked.connect(self.definePointsColor)
        self.pointsColorLayout = QHBoxLayout()
        self.pointsColorLayout.addWidget(self.pointsColorLabel, 4, Qt.AlignLeft)
        self.pointsColorLayout.addWidget(self.pointsColorButton, 1, Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.pointsColorLayout)
        
        
        
        
        self.axisLabelsColorLabel = QLabel("Axis labels color:")
        self.axisLabelsColorLabel.setFont(subTitleFont)
        self.axisLabelsColorButton = QPushButton('Open color dialog', self)
        self.axisLabelsColorButton.clicked.connect(self.defineAxisLabelsColor)
        self.axisLabelsColorLayout = QHBoxLayout()
        self.axisLabelsColorLayout.addWidget(self.axisLabelsColorLabel, 4, Qt.AlignLeft)
        self.axisLabelsColorLayout.addWidget(self.axisLabelsColorButton, 1, Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.axisLabelsColorLayout)    
        
        self.axisTitlesColorLabel = QLabel("Axis titles color:")
        self.axisTitlesColorLabel.setFont(subTitleFont)
        self.axisTitlesColorButton = QPushButton('Open color dialog', self)
        self.axisTitlesColorButton.clicked.connect(self.defineAxisTitlesColor)
        self.axisTitlesColorLayout = QHBoxLayout()
        self.axisTitlesColorLayout.addWidget(self.axisTitlesColorLabel, 4, Qt.AlignLeft)
        self.axisTitlesColorLayout.addWidget(self.axisTitlesColorButton, 1, Qt.AlignRight)
        self.propertiesTabLayout.addLayout(self.axisTitlesColorLayout)
        

        
    # A series of functions dedicated to set color of the elements featured in the monitor.    
    def defineBGColor(self):
        BG_color_name = QColorDialog.getColor()
        if BG_color_name.isValid():
            self.monitor._chart.setBackgroundBrush(QBrush(QColor(BG_color_name)))
        
    def defineGridColor(self):
        grid_color_name = QColorDialog.getColor()
        if grid_color_name.isValid():
            self.monitor.axis_x.setGridLineColor(QtGui.QColor(grid_color_name))
            self.monitor.axis_y.setGridLineColor(QtGui.QColor(grid_color_name))
            self.monitor.axis_x.setMinorGridLineColor(QtGui.QColor(grid_color_name))
            self.monitor.axis_y.setMinorGridLineColor(QtGui.QColor(grid_color_name)) 
            
    def defineLineColor(self):
        line_color_name = QColorDialog.getColor()
        if line_color_name.isValid():
            self.monitor.upperSeries.setColor(QtGui.QColor(line_color_name))
    
    def definePointsColor(self):
        points_color_name = QColorDialog.getColor()
        if points_color_name.isValid():
            self.monitor.pointseries.setColor(QtGui.QColor(points_color_name))

    def defineAxisLabelsColor(self): 
        axis_labels_color = QColorDialog.getColor()
        if axis_labels_color.isValid():
            self.monitor.axis_x.setLabelsColor(QtGui.QColor(axis_labels_color))
            self.monitor.axis_y.setLabelsColor(QtGui.QColor(axis_labels_color))
            
    def defineAxisTitlesColor(self): 
        axis_titles_color = QColorDialog.getColor()
        if axis_titles_color.isValid():
            self.monitor.axis_x.setTitleBrush(QtGui.QBrush(QtGui.QColor(axis_titles_color)))
            self.monitor.axis_y.setTitleBrush(QtGui.QBrush(QtGui.QColor(axis_titles_color)))
            
        
    # This is the core of this script. Will update both lists so they can be used to re-append
    # existing chart series.
    def update_chart(self):
        memoryListUpdate()
        dateTimeListUpdate()
        if self.highestListValueCB.isChecked():
            self.monitor.axis_y.setRange(0, getListMaxY() + 50)
        self.monitor.upperSeries.clear()
        self.monitor.pointseries.clear()
        for i in list(range(maxSample + 1)):
            self.monitor.upperSeries.append(i,memValuesList[i])
            self.monitor.pointseries.append(i, memValuesList[i])
        self.monitor.update()

            
    # Once a new number has been entered, both lists will be either reduced or extended. 
    # Will also update the X-Axis.
    def defineMaxSample(self, value):
        global maxSample
        maxSample = value
        if len(memValuesList) > (maxSample + 1):
            memValuesListShrinker()
            dateTimeListShrinker()
        elif len(memValuesList) < (maxSample + 1): 
            memValuesListExtender()
            dateTimeListExtender()
        self.monitor.axis_x.setRange(0, maxSample)
        self.samplesNumSpinBox.setValue(maxSample)
        self.samplesNumSlider.setSliderPosition(maxSample)

        

    # The function calling on findAppropriateMultiplier. 
    # Again you can remove it in profit of applyNiceNumbers (IMO I prefer the results of this one)
    def defineTickCount(self):
        self.tickCountNum = findAppropriateMultiplier(maxSample) +1
        self.monitor.axis_x.setTickCount(self.tickCountNum)
        self.minorTickCountNum = (maxSample / self.tickCountNum) 
        self.monitor.axis_x.setMinorTickCount(self.minorTickCountNum)
        

    # Our time box for changing the time loop. 
    # If a new value is entered, any running worker will stop and will need to be restarted.
    def changeLoopTime(self, newTime): 
        num = QTime(0, 0, 0).secsTo(newTime)
        global loopTime
        loopTime = num
        self.worker = Worker(self.update_chart, (loopTime * 1000))      
        self.autoUpdateStart.clicked.connect(self.worker.start)
        self.autoUpdateStop.clicked.connect(self.worker.stop)

        
        
    # Two functions for resizing the Y-Axis to the scale you want.
    def highestValueCheckboxFunction(self, state):
        if state == QtCore.Qt.Checked:
            self.monitor.axis_y.setRange(0, getListMaxY() + 50)
            self.maximumCacheCB.setChecked(False)

        else: 
            self.monitor.axis_y.setRange(0, getMaxNukeRAM())
            self.highestListValueCB.setChecked(False)
            

    def MaxNukeRAMCheckboxFunction(self, state):
        if state == QtCore.Qt.Checked:
            self.monitor.axis_y.setRange(0, getMaxNukeRAM())
            self.highestListValueCB.setChecked(False)

        else:
            self.monitor.axis_y.setRange(0, getListMaxY() + 50)
            self.maximumCacheCB.setChecked(False)
            
            


if __name__ == "__main__":
    mmWidget = MainPanel()
    mmWidget.show()



