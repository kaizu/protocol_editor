from NodeGraphQt import BaseNode


class SLabNode(BaseNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'SLab.nodes'

    # initial default node name.
    NODE_NAME = 'SLab'

    def __init__(self):
        super(SLabNode, self).__init__()

        # create node inputs.
        self.add_input('in', multi_input=True)

        # create node outputs.
        self.add_output('out', multi_output=True)

        # create QLineEdit text input widget.
        self.add_text_input('operation_type', 'Type', 'SLab', tab='widgets')
        self.add_text_input('duration', 'Duration (min)', '10', tab='widgets')


class TransporterNode(BaseNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'SLab.nodes'

    # initial default node name.
    NODE_NAME = 'Transporter'

    def __init__(self):
        super(TransporterNode, self).__init__()

        # create node inputs.
        self.add_input('in', multi_input=True)

        # create node outputs.
        self.add_output('out', multi_output=True)

        # create QLineEdit text input widget.
        self.add_text_input('duration', 'Duration (min)', '2', tab='widgets')