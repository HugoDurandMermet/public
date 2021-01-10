from PySide2 import QtWidgets, QtCore, QtGui, QtCharts
import nuke
from package.api.funcstore import nk_value, ram_percentage, find_multiplier


class Callout(QtWidgets.QGraphicsItem):
    def __init__(self, chart):
        """Class to be used as our custom graphical tooltip within the monitor chart.
        @param (QChart) chart:
        The chart this tooltip will be featured on.
        @return (None):
        No return value.
        """
        QtWidgets.QGraphicsItem.__init__(self, chart)
        self._chart = chart
        self._text = ""
        self._text_rect = QtCore.QRectF()
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
        painter.drawText(self._text_rect, self._text)

    def set_text(self, text):
        self._text = text
        metrics = QtGui.QFontMetrics(self._font)
        self._text_rect = QtCore.QRectF(metrics.boundingRect(
            QtCore.QRect(0, -25, 0, 0), QtCore.Qt.AlignRight, self._text))
        self._text_rect.translate(5, 5)
        self.prepareGeometryChange()
        self._rect = self._text_rect.adjusted(-5, -5, 5, 5)

    def set_anchor(self, point):
        self._anchor = QtCore.QPointF(point)

    def update_geometry(self):
        self.prepareGeometryChange()
        self.setPos(self._chart.mapToPosition(
            self._anchor) + QtCore.QPointF(10, -50))


class ColorSettings(QtWidgets.QHBoxLayout):
    def __init__(self, label, signal, target):
        """Creates a set of widgets to set the color of a specific part of the Monitor chart within the main panel.
        @param (str) label:
        The label of the target these settings are created for.
        @param (QSignal) signal:
        A signal redirecting to the function in charge of opening the color dialog.
        @param (str) target:
        The target name used by the color dialog function.
        @return (None):
        No return value.
        """
        super(ColorSettings, self).__init__(label, signal, target)
        color_label = self.create_sublabel(label)
        color_button = QtWidgets.QPushButton('Open color dialog')
        color_button.clicked.connect(lambda: signal(target))
        self.addWidget(color_label, 4, QtCore.Qt.AlignLeft)
        self.addWidget(color_button, 1, QtCore.Qt.AlignRight)


class CustomAxis(QtCharts.QValueAxis):
    def __init__(self, text):
        """ A subclass of the QValueAxis to be featured in the Monitor chart.
        @param (str) text:
        The name of the axis title.
        @return (None):
        No return value.
        """
        super(CustomAxis, self).__init__(text)
        self.setTitleText(text)
        self.setTitleBrush(QtGui.QBrush(QtGui.QColor("lightGrey")))
        self.setTitleFont(QtGui.QFont("Calibri", 14, QtGui.QFont.Bold))
        self.setLabelsFont(QtGui.QFont("Calibri", 10, QtGui.QFont.Bold))
        self.setLabelsColor(QtGui.QColor("grey"))


class CustomPushButton(QtWidgets.QPushButton):
    def __init__(self, text, tooltip):
        """ A subclass of the QPushButton to be featured in the Monitor chart.
        @param (str) text:
        The text displayed on the Push Button.
        @param (str) tooltip:
        The text displayed on the tooltip.
        @return (None):
        No return value.
        """
        super(CustomPushButton, self).__init__(text, tooltip)
        self.setText(text)
        self.setToolTip(tooltip)
        self.setCheckable(False)
        self.toggle()


class Monitor(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        """Main widget for the monitor and its chart.
        """
        super(Monitor, self).__init__(parent)
        self._max_sample = 20
        self.mem_list = [0 for x in list(range(self._max_sample + 1))]
        self.dt_list = ["---" for y in list(range(self._max_sample + 1))]

        self.setScene(QtWidgets.QGraphicsScene(self))

        self.setDragMode(QGraphicsView.NoDrag)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self._chart = QtCharts.QChart()
        self._chart.setBackgroundBrush(QtGui.QBrush(QtGui.QColor("black")))
        self._chart.setTitle("Hover the points to display individual values.")
        self._chart.legend().hide()

        self.upperSeries = QtCharts.QLineSeries()
        self.pointsSeries = QtCharts.QScatterSeries()
        self.upperSeries.setColor(QtGui.QColor("cyan"))
        self.pointsSeries.setColor(QtGui.QColor("cyan"))
        self.pointsSeries.setBorderColor(QtGui.QColor("transparent"))
        self.pointsSeries.setPointLabelsFormat("@yPoint")
        self.pointsSeries.setPointLabelsColor(QtGui.QColor("white"))
        self.pointsSeries.setPointLabelsClipping(False)
        self.pointsSeries.setMarkerSize(10)

        self._chart.addSeries(self.upperSeries)
        self._chart.addSeries(self.pointsSeries)

        self.axis_x = CustomAxis("Number of samples")
        self._chart.addAxis(self.axis_x, QtCore.Qt.AlignBottom)
        self.axis_y = CustomAxis("Memory (in MB)")
        self._chart.addAxis(self.axis_y, QtCore.Qt.AlignLeft)
        self._chart.setAcceptHoverEvents(True)

        self.axis_x.setRange(0, 20)
        self.axis_y.setRange(0, 50)

        self.axis_x.setMinorTickCount(4)
        self.axis_y.applyNiceNumbers()

        self.attach_axis(self.upperSeries)
        self.attach_axis(self.pointsSeries)
        self.append_series()

        self.areaSeries = QtCharts.QAreaSeries(self.upperSeries)
        self.areaPen = QtGui.QPen(Qt.cyan)
        self.areaPen.setWidth(3)
        self.areaSeries.setPen(self.areaPen)

        self._chart.addSeries(self.areaSeries)
        self.attach_axis(self.areaSeries)

        self.set_hlcb_area_gradient()

        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.scene().addItem(self._chart)

        self._coordX = self.create_coord()
        self._coordY = self.create_coord()
        self._callouts = []
        self._tooltip = Callout(self._chart)
        self.pointsSeries.hovered.connect(self.tooltip)

        self.setMouseTracking(True)

    def attach_axis(self, series):
        series.attachAxis(self.axis_x)
        series.attachAxis(self.axis_y)

    def append_series(self):
        for index, value in enumerate(self.mem_list):
            self.upperSeries.append(index, value)
            self.pointsSeries.append(index, value)

    @property
    def chart(self):
        return self._chart

    def create_coord(self):
        """ Creates coordinates to be used for the tooltip.
        """
        coord = QtWidgets.QGraphicsSimpleTextItem(self._chart)
        coord.setPos(self._chart.size().width() / 2 - 50, self._chart.size().height())
        return coord

    def define_tick_count(self):
        """Set new count for ticks and minor ticks on the monitor chart.
        """
        tick_count_num = find_multiplier(self.max_sample) + 1
        self.axis_x.setTickCount(tick_count_num)
        minor_tick_count_num = (self.max_sample / tick_count_num)
        self.axis_x.setMinorTickCount(minor_tick_count_num)

    def keepCallout(self):
        """ Creates a graphical tooltip for the points series.
        """
        self._callouts.append(self._tooltip)
        self._tooltip = Callout(self._chart)

    @property
    def max_sample(self):
        return self._max_sample

    @max_sample.setter
    def max_sample(self, new_sample):
        if new_sample < 1:
            nuke.message("You need to enter a value higher than one.")
        else:
            self._max_sample = new_sample

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
        
    def set_hlcb_area_gradient(self):
        """Method to be invoked if user chooses to tick the "Highest Value" check box on the main panel settings.
        Attributes an area gradient going from green (when the ram being used at the lowest) to red (when the ram used
        is at its highest).
         """
        area_gradient = QtGui.QLinearGradient(QtCore.QPointF(0, 0), QtCore.QPointF(0, 1))
        total_by_usage = nuke.memory('usage') / nuke.memory('max_usage')
        area_gradient.setColorAt(0.0, QtGui.QColor(255, 0, 0, 180))
        area_gradient.setColorAt((total_by_usage * 0.5), QtGui.QColor(255, 255, 0, 120))
        area_gradient.setColorAt(total_by_usage, QtGui.QColor(0, 255, 0, 60))
        area_gradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
        self.areaSeries.setBrush(area_gradient)
        
    def set_mccb_area_gradient(self):
        """Method to be invoked if user chooses to tick the "Maximum Cache" check box on the main panel settings.
        Attributes an area gradient going from green (when the ram being used at the lowest) to red (when the ram used
        is at its highest).
         """
        area_gradient = QtGui.QLinearGradient(QtCore.QPointF(0, 0), QtCore.QPointF(0, 1))
        area_gradient.setColorAt(0.0, QtGui.QColor(255, 0, 0, 180))
        area_gradient.setColorAt(0.5, QtGui.QColor(255, 255, 0, 120))
        area_gradient.setColorAt(1, QtGui.QColor(0, 255, 0, 60))
        area_gradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
        self.areaSeries.setBrush(area_gradient)

    def tooltip(self, point, state):
        """ Method invoked when the cursor hovers one of the members of the points series. Instantiate the Callout
        class.
        @param (QPoint) point:
        Receives the point hovered by the cursor.
        @param (QSignal) state:
        Connection signal.
        @return (None):
        No return value.
        """
        if self._tooltip == 0:
            self._tooltip = Callout(self._chart)

        if state:
            self._tooltip.set_text("{0:s}\nAt sample: {1:.2f} \nMemory used: {2:.2f}MB \nTotal RAM usage: {3:.2f}% "
                                   .format(self.dt_list[int(point.x())], point.x(), point.y(),
                                           ram_percentage(point.y())))
            self._tooltip.set_anchor(point)
            self._tooltip.setZValue(11)
            self._tooltip.update_geometry()
            self._tooltip.show()
        else:
            self._tooltip.hide()


class Separator(QtWidgets.QFrame):
    """Creates a simple separating line widget to be used later on in the main window
    """
    def __init__(self):
        super(Separator, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class SubLabel(QtWidgets.QLabel):
    def __init__(self, text, font):
        """A QLabel subclassed for more convenience.
        @param (str) text:
        The label's text.
        @param (QFont) font:
        The label's QFont.
        @return (None):
        No return value.
        """
        self.setText(text)
        self.setFont(font)


class Worker(QtCore.QObject):
    def __init__(self, function, interval):
        """This will be the main class behind the monitor auto update using a QTimer
        @param (func) function:
        The function this worker will repeat.
        @param (int) interval:
        The interval between two functions reps.
        @return (None):
        No return value.
        """
        super(Worker, self).__init__()
        self._function = function
        self._timer = QtCore.QTimer(self, interval=interval, timeout=self.execute)

    @property
    def running(self):
        """Warns if a worker is already running or not.
        @return (bool) self._timer.isActive():
        True if a worker is currently running.
        """
        return self._timer.isActive()

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.stop()

    def execute(self):
        self._function()
