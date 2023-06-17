from nodes import SampleNode, PortTraitsEnum


class BuiltinNode(SampleNode):

    def execute(self, sim):
        raise NotImplementedError("Override this")

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
#         self._add_input("in1", PortTraitsEnum.DATA)

#     def execute(self, input_tokens):
#         value = input_tokens["in1"]
#         # value = input_tokens["in1"]["value"]
#         self.set_property("mywidget", str(value), push_undo=False)
#         return {}
    
class SwitchNode(BuiltinNode):

    __identifier__ = "builtins"

    NODE_NAME = "SwtichNode"

    def __init__(self):
        super(SwitchNode, self).__init__()
        # self.__doc = doc
        traits = PortTraitsEnum.OBJECT  # ANY?
        self._add_input("in1", traits)
        self._add_input("cond1", PortTraitsEnum.DATA)
        self._add_output("out1", traits)
        self._add_output("out2", traits)
        self._set_io_mapping("out1", "in1")
        self._set_io_mapping("out2", "in1")
    
    def execute(self, input_tokens):
        dst = "out1" if input_tokens["cond1"]["value"] else "out2"
        return {dst: input_tokens["in1"]}