
# --------------------------------------------------------------
#  expressionsLibrary.py
#  Version: 6.0.0
#  Author: Hugo Durand-Mermet
#
#  Last Modified by: Hugo Durand-Mermet
#  Last Updated: November 17th, 2020
# --------------------------------------------------------------

# --------------------------------------------------------------
#  USAGE:
#
#  Right click on a knob and click on Expressions Library will open
#  a QTreeWidget panel filled with pre-stored TCL expressions.
#  Click on Generate to set the expression you've chosen in the
#  currently selected Knob. 
# --------------------------------------------------------------

# --------------------------------------------------------------
#  ROOM FOR IMPROVEMENT: 
#
# - Create a search bar to filter out items. Might need to convert
# the whole panel into a QTreeView to achieve that. 
# - Add settings to link expression to another node / knob with a
# a pulldown menu displaying what's in the script. Will take a lot
# of work, especially since my items are implemented recursively.
# - Look up for Matrix expressions. 
# - I might need at some point to separate Knob targetting 
# expressions, and Nodes targetting expressions.
# - What would be the cherry on top, is a panel on the right,
# playing an example of the expression, even though I have no idea
# how this can be achievable. 
# --------------------------------------------------------------

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------
#  INSTRUCTIONS: 
#
#  -Save this py script in /.nuke or your favourite folder. Make sure the folder path has been saved in the init.py script.
#  -In your menu.py script, add the following line: 
#
#  nuke.menu('Animation').addCommand('Expressions Library', 'import expressionsLibrary;el_widget = expressionsLibrary.ExpressionsLibraryWidget();el_widget.show()')
#
# -This script has been tested on a free trial version of Nuke12.2v3. If you have an older or a custom version of Nuke, it's possible this script doesn't work as
#  expected, especially since it relies on modules to import. If that is the case, don't hesitate to reach out to me through my GitHub. 
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------




from PySide2.QtCore import *
from PySide2 import *
from PySide2.QtWidgets import *
from PySide2.QtCharts import *
from PySide2.QtGui import *


from functools import partial
import nuke
from nukescripts import panels



    
class LibraryTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent, column, text):
        QtWidgets.QTreeWidgetItem.__init__(self, parent)
        self.text = text
        self.column = column
        if self.text != None:
            self.setText(self.column, self.text)

        

class LibraryTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        QtWidgets.QTreeWidget.__init__(self, parent)
        self.listItems = ["Expression", "Description", "Generate", "Quick Example"]
        self._target_knob = nuke.thisKnob()
        self.setColumnCount(len(self.listItems))
        self.setColumnWidth(0, 400)
        self.setColumnWidth(1, 600)
        self.setColumnWidth(2, 100)
        self.setColumnWidth(3, 100)
        self.setHeaderLabels(self.listItems)
        
        # In case you want to add another category, don't forget to start its name by the prefix self._category
        # so it can be dynamically picked up by the self._categories list down below.
        self._category_mathematical_functions = LibraryTreeWidgetItem(parent, 0, "Mathematical Functions")
        self._category_waves = LibraryTreeWidgetItem(parent, 0, "Waves")
        self._category_conditions = LibraryTreeWidgetItem(parent, 0, "Conditions")
        self._category_general_commands = LibraryTreeWidgetItem(parent, 0, "General Commands")
        
        self._brush_categories = QBrush(QColor("white"))
        self._font_categories = QFont("Calibri", 12, QFont.Bold)
        self._font_categories.setItalic(True) 
        self._font_expressions = QFont("Calibri", 10, QFont.Bold)
        self._font_descriptions = QFont("Calibri", 9)
        
        
        # If you have to add another dictionary or edit one of the following, escaping the curly brackets by doubling them isn't required. 
        # However don't forget to escape quotes and double quotes if they're part of the expression. 
        self._waves_dic = {"random((frame+offset)/WaveLength)*(maxVal-minVal) + minVal" : ["Random wave", "random((frame)/10)"],
                           "(noise((frame+offset)/waveLength)+1)/2 * (maxVal-minVal) + minVal": ["Noise wave", "(noise((frame)/10)+1)/2"],
                           "(sin(2*pi*(frame+offset)/waveLength)+1)/2 * (maxVal-minVal) + minVal": ["Sine wave", "(sin(2*pi*(frame)/24)+1)/2"],
                           "(asin(sin(2*pi*(frame+offset)/waveLength))/pi+0.5) * (maxVal-minVal) + minVal": ["Triangle wave", "(asin(sin(2*pi*(frame)/24))/pi+0.5)"],
                           "int(sin(2*pi*(frame+offset)/waveLength)+1) * (maxVal-minVal) + minVal": ["Square wave", "int(sin(2*pi*(frame)/24)+1)"],
                           "((frame+offset) % waveLength)/waveLength * (maxVal-minVal) + minVal": ["Sawtooth wave", "((frame) % 24)/24"],
                           "sin((pi*(frame+offset)/(2*waveLength)) % (pi/2)) * (maxVal-minVal) + minVal": ["Sawtooth (parabolic) wave", "sin((pi*(frame)/(2*24)) % (pi/2))"],
                           "cos((pi*(frame+offset)/(2*waveLength)) % (pi/2)) * (maxVal-minVal) + minVal": ["Sawtooth (parabolic reversed) wave", "cos((pi*(frame)/(2*24)) % (pi/2))"],
                           "(exp(2*pi*((frame+offset) % waveLength)/waveLength)-1)/exp(2*pi) * (maxVal-minVal) + minVal": ["Sawtooth (exponential) wave", "(exp(2*pi*((frame) % 24)/24)-1)/exp(2*pi)"],
                           "abs(sin(pi*(frame + offset)/waveLength))* (maxVal-minVal) + minVal" : ["Bounce wave", "abs(sin(pi*(frame)/24))"],
                           ("((frame+(offset+waveLength)) % (waveLength+blipLength)/(waveLength))" 
                            "*(waveLength/blipLength) - (waveLength/blipLength) >= 0 ? maxVal : minVal"): ["Blip", "((frame+20) % (20+5)/(20)) *(20/5) - (20/5) >= 0 ? 1 : 0"],
                           ("((int((frame+offset) % waveLength)) >= 0 ? ((int((frame+offset) % waveLength))" 
                           "<= (0+(blipLength-1)) ? ((sin(pi*((frame+offset) % waveLength)/blipLength)/2+1/2) *" 
                           "(2*maxVal-2*minVal) + (2*minVal-maxVal)) : minVal)  : minVal)") : ["Sineblip", ("((int(frame % 20)) >= 0 ? ((int(frame % 20)) <= (5-1) ?" 
                                                                                                            "((sin(pi*(frame % 20)/5)/2+1/2) * (2*1-2*0) + (2*0-1)) : 0)  : 0)")]}
        
        self._conditions_dic = { "value_1  ==  value_2  ?  if  :  else" : ["Checks if value_1 and value_2 are equal or not. If yes, returns if value, if not, returns else value", "frame == 1010 ? 50 : 100"],
                                "value_1  !=  value_2  ?  if  :  else" : ["Checks if value_1 and value_2 are equal or not. If not, returns if value, if yes, returns else value", "frame != 1010 ? 50 : 100"],
                                "value_1  >  value_2  ?  if  :  else" : ["Checks if value_1 is greater than value_2. If yes, returns if value, if not, returns else value", "frame > 1010 ? 50 : 100"],
                                "value_1  <  value_2  ?  if  :  else" : ["Checks if value_1 is less than value_2. If yes, returns if value, if not, returns else value", "frame == 1010 ? 50 : 100"],
                                "value_1  >=  value_2  ?  if  :  else" : ["Checks if value_1 is greater than or equal to value_2. If yes, returns if value, if not, returns else value", "frame > 1010 ? 50 : 100"],
                                "value_1  <=  value_2  ?  if  :  else" : ["Checks if value_1 is less than or equal to value_2. If yes, returns if value, if not, returns else value", "frame == 1010 ? 50 : 100"],
                                "{value_1  +  value_2  ==  value_3 } ? {return if } : {return else }" : [("If the sum of value_1 and value_2 equals to value_3, returns if value." 
                                                                                                                "If not, returns else value."), "[if {[value Blur11.size]+[value Blur12.size]==10} {return \"500\"} {return \"10\"}]"],
                                "{value_1  -  value_2  ==  value_3 } ? {return if } : {return else }" : [("If value_2 substracted from value_1 equals to value_3, returns if value." 
                                                                                                                "If not, returns else value."), "[if {[value Blur11.size]-[value Blur12.size]==10} {return \"500\"} {return \"10\"}]"],
                                "{value_1  *  value_2  ==  value_3 } ? {return if } : {return else }" : [("If value_1 multiplied by value_2 equals to value_3, returns if value." 
                                                                                                                "If not, returns else value."), "[if {[value Blur11.size]*[value Blur12.size]==10} {return \"500\"} {return \"10\"}]"],
                                "{value_1  /  value_2  ==  value_3 } ? {return if } : {return else }" : [("If value_1 divided by value_2 equals to value_3, returns if value." 
                                                                                                                "If not, returns else value."), "[if {[value Blur11.size]/[value Blur12.size]==10} {return \"500\"} {return \"10\"}]"],
                                "{value_1  %  value_2  ==  value_3 } ? {return if } : {return else }" : [("If the remainder of an integer division between value_2 and value_1 equals to value_3, returns if value." 
                                                                                                                "If not, returns else value."), "[if {[value Blur11.size]%[value Blur12.size]==10} {return \"500\"} {return \"10\"}]"],
                                "condition_1  &&  condition_2  ?  if  :  else" : ["If both conditions are true, returns if value. If not, returns else value", "frame < 1010 && [value mix] == .5 ? 50 : 100"],
                                "condition_1  ||  condition_2  ?  if  :  else" : ["If any of the two conditions is true, returns if value. If not, returns else value", "frame < 1010 || [value mix] == .5 ? 50 : 100"]
                                
                      }
        
        self._general_commands_dic = { "[value  knob_name]" : "Returns the current value of a knob",
                                       "frame == value" : "Set the frame at the value number",
                                       "inrange(frame, value_1, value_2)" : "Returns True (=1) when current frame is in range",
                                       "[exists  knob_or_node_name]" : "Returns True ( =1 ) if the named knob or node exists.",
                                       "[knob  knob_name  new_value]": "Will set a new value for the specified knob",
                                       "[setkey  knob_name  frame number  new_value]": "Set a key for a knob on a specified frame with specified new value",
                                       "$gui" : "Returns False when Nuke is running, but remains True for rendering"                      
            
        }
        
        self._math_functions_dic = {"abs (x)" : "Returns the absolute value of the floating-point number x.",
                                    "acos (x)": "Calculates the arc cosine of x; that is the value whose cosine is x.",
                                    "asin (x)": "Calculates the arc sine of x; that is the value whose sine is x.",
                                    "atan (x)": "Calculates the arc tangent of x; that is the value whose tangent is x.The return value is between -PI/2 and PI/2.",
                                    "atan2 (x, y)": "Calculates the arc tangent of the two variables x and y. This function is useful to calculate the angle between two vectors.",
                                    "ceil (x)" : "Round x up to the nearest integer.",
                                    "clamp (x, min, max)": "Return x clamped to [min ... max].",
                                    "cos (x)": "Returns the cosine of x.",
                                    "cosh (x)": "Returns the hyperbolic cosine of x, which is defined mathematically as (exp(x) + exp(-x)) / 2.",
                                    "curve (frame)": "Returns the y value of the animation curve at the given frame.",
                                    "degrees (x)" : "Convert the angle x from radians into degrees.",
                                    "exp (x)": "Returns the value of e (the base of natural logarithms) raised to the power of x.",
                                    "exponent (x)": "Exponent of x.",
                                    "fBm (x, y, z, octaves, lacunarity, gain)": ("Fractional Brownian Motion. This is the sum of octaves calls to noise(). " 
                                    "For each of them the input point is multiplied by pow(lacunarity,i) and the result is multiplied by pow(gain,i). " 
                                    "For normal use, lacunarity should be greater than 1 and gain should be less than 1."),
                                    "fabs (x)": "Returns the absolute value of the floating-point number x.",
                                    "false ()": "Always returns 0",
                                    "floor (x)": "Round x down to the nearest integer.",
                                    "fmod (x, y)": "Computes the remainder of dividing x by y. The return value is x - n y, where n is the quotient of x / y, rounded towards zero to an integer.",
                                    "frame ()": "Return the current frame number.",
                                    "from_byte (color component)": "Converts an sRGB pixel value to a linear value.",
                                    "from_rec709f (color component)": "Converts a rec709 byte value to a linear brightness",
                                    "from_sRGB (color component)": "Converts an sRGB pixel value to a linear value.",
                                    "hypot (x, y)": "Returns the sqrt(x*x + y*y). This is the length of the hypotenuse of a right-angle triangle with sides of length x and y.",
                                    "int (x)": "Round x to the nearest integer not larger in absolute value.",
                                    "ldexp (x)": "Returns the result of multiplying the floating-point number x by 2 raised to the power exp.",
                                    "lerp (a, b, x)": "Returns a point on the line f(x) where f(0)==a and f(1)==b. Matches the lerp function in other shading languages.",
                                    "log (x)": "Returns the natural logarithm of x.",
                                    "log10 (x)": "Returns the base-10 logarithm of x.",
                                    "logb (x)": "Same as exponent().",
                                    "mantissa (x)": ("Returns the normalized fraction. If the argument x is not zero, the normalized fraction is x times a power of two, "
                                    "and is always in the range 1/2 (inclusive) to 1 (exclusive). If x is zero, then the normalized fraction is zero and exponent() Returns zero."),
                                    "max (x, y, ... )": "Return the greatest of all values.",
                                    "min (x, y, ... )": "Return the smallest of all values.",
                                    "mix (a, b, x)": "Same as lerp().",
                                    "noise (x, y, z)": ("Creates a 3D Perlin noise value. This produces a signed range centerd on zero. The absolute maximum range is from -1.0 to 1.0. "
                                    "This produces zero at all integers, so you should rotate the coordinates somewhat (add a fraction of y and z to x, etc.) " 
                                    "if you want to use this for random number generation."),
                                    "pi ()": "Returns the value for pi (3.141592654...).",
                                    "pow (x, y)": "Returns the value of x raised to the power of y.",
                                    "pow2 (x)": "Returns the value of x raised to the power of 2.",
                                    "radians (x)": "Convert the angle x from degrees into radians.",
                                    "random (x, y, z)": ("Creates a pseudo random value between 0 and 1. It always generates the same value for the same x, y and z. "
                                    "Calling random with no arguments creates a different value on every invocation."),
                                    "rint (x)": "Round x to the nearest integer.",
                                    "sin (x)": "Returns the sine of x.",
                                    "sinh (x)": "Returns the hyperbolic sine of x, which is defined mathematically as (exp(x) - exp(-x)) / 2.",
                                    "smoothstep (a, b, x)": ("Returns 0 if x is less than a, returns 1 if x is greater or equal to b, returns a smooth cubic interpolation otherwise. "
                                    "Matches the smoothstep function in other shading languages."),
                                    "sqrt (x)": "Returns the non-negative square root of x.",
                                    "step (a, x)": "Returns 0 if x is less than a, returns 1 otherwise. Matches the step function other shading languages.",
                                    "tan (x)": "Returns the tangent of x.",
                                    "tanh (x)": "Returns the hyperbolic tangent of x, which is defined mathematically as sinh(x) / cosh(x).",
                                    "to_byte (color component)": "Converts a floating point pixel value to an 8-bit value that represents that number in sRGB space.",
                                    "to_rec709f (color component)": ("Converts a floating point pixel value to an 8-bit value that represents that brightness in the rec709 standard when " 
                                    "that standard is mapped to the 0-255 range."),
                                    "to_sRGB (color component)": "Converts a floating point pixel value to an 8-bit value that represents that number in sRGB space.",                                    
                                    "true ()": "Always Returns 1.",
                                    "trunc (x)": "Round x to the nearest integer not larger in absolute value.",
                                    "turbulence (x, y, z, octaves, lucanarity, gain)" : "This is the same as fBm() except the absolute value of the noise() function is used.",
                                    "value (frame)": "Evaluates the y value for an animation at the given frame.",
                                    "x ()": "Return the current frame number.",
                                    "y (frame)": "Evaluates the y value for an animation at the given frame."
                                                  }



    
        self._math_functions_items = self.create_items_list(self._category_mathematical_functions, self._math_functions_dic, False)
        self._wave_items = self.create_items_list(self._category_waves, self._waves_dic, True)
        self._conditions_items = self.create_items_list(self._category_conditions, self._conditions_dic, True)
        self._general_commands_items = self.create_items_list(self._category_general_commands, self._general_commands_dic, False)
            


            
        self._categories = [getattr(self, name) for name in self.__dict__ if name.startswith('_category')]

        for category in self._categories: 
            category.setForeground(0,self._brush_categories)
            category.setFont(0, self._font_categories)
        
        
            
        
        self.addTopLevelItems(self._categories)
        self.addTopLevelItems(self._math_functions_items)
        self.addTopLevelItems(self._wave_items)
        self.addTopLevelItems(self._conditions_items)
        self.addTopLevelItems(self._general_commands_items)
        
        # If you need to increase the height or width of the TreeWidget items, I'd advised to do it here. 
        # So far, this is what gave me the best results.
        self.setStyleSheet("""QTreeView::item { border-bottom: 1px solid rgb(80, 80, 80); 
                                                border-right: 1px solid rgb(80, 80, 80);
                                                height: 50px;
                                                padding: 0px 0;}
                                                """)
        self.sortItems(0, QtCore.Qt.AscendingOrder)
        self.setSortingEnabled(True)




    def create_items_list(self, _parent, _dic, _listSignal): 
        self._parent = _parent
        self._dic = _dic
        self._tempList = []
        
        # As we have dictionaries where there is just one value per key, and other with a list of values, I've implemented an additional 
        # attribute when calling the self.create_items_list function, based on Boolean values. If True, this means the function will adapt
        # for a list of values, and implement a second PushButton for self._dic.get(key)[1]. If False, the function will just implement
        # the usual pushButton for self._dic.get(key) and not add a second one.
        
        self._listSignal = _listSignal
        for key in self._dic.keys(): 
            if self._listSignal == True:
                descriptionText= self._dic.get(key)[0]
            else: 
                descriptionText= self._dic.get(key)     
            item = LibraryTreeWidgetItem(self._parent, 0, key)
            # Even though this wasn't necessary, I've chosen to use QLabel to display the text provided, as QLabel can implement WordWrap.
            expression_label = QLabel(key)
            expression_label.setWordWrap(True)
            expression_label.setFont(self._font_expressions)
            expression_label.setStyleSheet("QLabel { background-color : rgb(50, 52, 69); color : rgb(34, 163, 189); }")
            
            description_label = QLabel(descriptionText)
            description_label.setWordWrap(True)
            description_label.setFont(self._font_descriptions)
            self.setItemWidget(item, 0, expression_label)
            self.setItemWidget(item, 1, description_label)
            pushButton = QPushButton("Generate")
            buttonSize = QSize(80, 35)
            pushButton.setFixedSize(buttonSize)
            pushButton.setCheckable(False)
            pushButton.toggle()
            pushButton.clicked.connect(partial(self.generate_expression, key))
            pushWidget = QWidget()
            pushLayout = QHBoxLayout()
            pushWidget.setLayout(pushLayout)
            pushLayout.addWidget(pushButton)
            self.setItemWidget(item, 2, pushWidget)
            if self._listSignal == True:
                secondPushButton = QPushButton("Quick Example")
                secondButtonSize = QSize(100, 35)
                secondPushButton.setFixedSize(secondButtonSize)
                secondPushButton.setCheckable(False)
                secondPushButton.toggle()
                secondPushButton.clicked.connect(partial(self.generate_expression, self._dic.get(key)[1]))
                secondPushWidget = QWidget()
                secondPushLayout = QHBoxLayout()
                secondPushWidget.setLayout(secondPushLayout)
                secondPushLayout.addWidget(secondPushButton)
                self.setItemWidget(item, 3, secondPushWidget)
            self._tempList.append(item)

            
        return self._tempList
    

    def generate_expression(self, key):
        expression = key
        self._target_knob.setExpression(expression)



class ExpressionsLibraryWidget(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self._knob = nuke.thisKnob()
        self.setWindowTitle("Expressions Library")
        self.resize(1300, 550)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.treeWidget = LibraryTreeWidget()
        self.layout.addWidget(self.treeWidget)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        
if __name__ == "__main__":
    elWidget = ExpressionsLibraryWidget()
    elWidget.show()
