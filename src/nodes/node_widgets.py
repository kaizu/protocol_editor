from NodeGraphQt import NodeBaseWidget

from PySide2.QtGui import QPixmap
import PySide2.QtWidgets


class DoubleSpinBoxWidget(NodeBaseWidget):

    def __init__(self, parent=None, name='', label='', minimum=-999, maximum=+999, decimals=0):
        super(DoubleSpinBoxWidget, self).__init__(parent, name, label)
        
        box = PySide2.QtWidgets.QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setDecimals(decimals)
        self.set_custom_widget(box)

        # connect up the signals & slots.
        self.wire_signals()

    def wire_signals(self):
        widget = self.get_custom_widget()
        widget.valueChanged.connect(self.on_value_changed)

    @property
    def type_(self):
        return 'DoubleSpinBoxWidget'

    def get_value(self):
        """
        Returns the widgets current text.

        Returns:
            str: current text.
        """
        return self.get_custom_widget().value()

    def set_value(self, text=''):
        """
        Sets the widgets current text.

        Args:
            text (str): new text.
        """
        value = int(text)
        if value != self.get_value():
            self.get_custom_widget().setValue(value)
            self.on_value_changed()

class LabelWidget(NodeBaseWidget):

    def __init__(self, parent=None, name='', label=''):
        super(LabelWidget, self).__init__(parent, name, label)
        
        label = PySide2.QtWidgets.QLabel()
        pixmap = QPixmap('C:\\Users\\kaizu\\Documents\\Python Scripts\\protocol_editor\\nodes\\cat.jpg')
        label.setPixmap(pixmap)
        self.set_custom_widget(label)

    @property
    def type_(self):
        return 'LabelWidget'

    def get_value(self):
        """
        Returns the widgets current text.

        Returns:
            str: current text.
        """
        # return self.get_custom_widget().pixmap().toImage()
        return ""

    def set_value(self, text=''):
        """
        Sets the widgets current text.

        Args:
            text (str): new text.
        """
        # self.on_value_changed()
        pass

    def set_image(self, img):
        pixmap = QPixmap(img)
        self.get_custom_widget().setPixmap(pixmap)

class PushButtonWidget(NodeBaseWidget):

    def __init__(self, parent=None, name='', label='', text="Push"):
        super(PushButtonWidget, self).__init__(parent, name, label)
        
        button = PySide2.QtWidgets.QPushButton(text)
        self.set_custom_widget(button)

        # connect up the signals & slots.
        self.wire_signals()

    def wire_signals(self):
        widget = self.get_custom_widget()
        widget.clicked.connect(self.on_button_clicked)
        # widget.valueChanged.connect(self.on_value_changed)

    def on_button_clicked(self, *args, **kwargs):
        print("Saluton!")
    
    @property
    def type_(self):
        return 'PushButtonWidget'

    def get_value(self):
        """
        Returns the widgets current text.

        Returns:
            str: current text.
        """
        return ''

    def set_value(self, value=''):
        """
        Sets the widgets current text.

        Args:
            text (str): new text.
        """
        if value != self.get_value():
            # self.get_custom_widget().setValue(value)
            # self.on_value_changed()
            pass

# class MyNodeLineEdit(NodeBaseWidget):

#     def __init__(self, parent=None, name='', label='', text=''):
#         super(MyNodeLineEdit, self).__init__(parent, name, label)
#         bg_color = ViewerEnum.BACKGROUND_COLOR.value
#         text_color = tuple(map(lambda i, j: i - j, (255, 255, 255),
#                                bg_color))
#         style_dict = {
#             'QLabel': {
#                 'background': 'rgba({0},{1},{2},20)'.format(*bg_color),
#                 'border': '1px solid rgb({0},{1},{2})'
#                           .format(*ViewerEnum.GRID_COLOR.value),
#                 'border-radius': '3px',
#                 'color': 'rgba({0},{1},{2},150)'.format(*text_color),
#             }
#         }
#         stylesheet = ''
#         for css_class, css in style_dict.items():
#             style = '{} {{\n'.format(css_class)
#             for elm_name, elm_val in css.items():
#                 style += '  {}:{};\n'.format(elm_name, elm_val)
#             style += '}\n'
#             stylesheet += style
#         ledit = QtWidgets.QLabel()
#         ledit.setStyleSheet(stylesheet)
#         ledit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
#         ledit.setFixedWidth(300)
#         ledit.setText(text)
#         self.set_custom_widget(ledit)
#         # self.widget().setMaximumWidth(300)

#     @property
#     def type_(self):
#         return 'MyLineEditNodeWidget'

#     def get_value(self):
#         """
#         Returns the widgets current text.

#         Returns:
#             str: current text.
#         """
#         return str(self.get_custom_widget().text())

#     def set_value(self, text=''):
#         """
#         Sets the widgets current text.

#         Args:
#             text (str): new text.
#         """
#         if text != self.get_value():
#             self.get_custom_widget().setText(text)
#             self.on_value_changed()

# class IONode(BuiltinNode):

#     __identifier__ = "builtins"

#     NODE_NAME = "IONode"

#     def __init__(self):
#         super(IONode, self).__init__()

#         widget = MyNodeLineEdit(self.view, name="mywidget", text="Saluton, \nMondo!")
#         self.add_custom_widget(widget, tab='widgets')
#         # self.add_text_input("mywidget", tab="widgets")
#         self.add_input_w_traits("in1", PortTraitsEnum.DATA)

#     def _execute(self, input_tokens):
#         value = input_tokens["in1"]
#         # value = input_tokens["in1"]["value"]
#         self.set_property("mywidget", str(value), push_undo=False)
#         return {}