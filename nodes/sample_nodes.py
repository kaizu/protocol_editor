from nodes import BasicNode


class InputNode(BasicNode):
    """
    A node class with 1 output.
    """

    # unique node identifier.
    __identifier__ = 'nodes.sample'

    # initial default node name.
    NODE_NAME = 'Input'

    def __init__(self):
        super(InputNode, self).__init__()

        self.add_object_output('out')

class OutputNode(BasicNode):
    """
    A node class with 1 input.
    """

    # unique node identifier.
    __identifier__ = 'nodes.sample'

    # initial default node name.
    NODE_NAME = 'Output'

    def __init__(self):
        super(OutputNode, self).__init__()

        self.add_object_input('in')

class UniNode(BasicNode):
    """
    A node class with 1 input and 1 output.
    """

    # unique node identifier.
    __identifier__ = 'nodes.sample'

    # initial default node name.
    NODE_NAME = 'Uni'

    def __init__(self):
        super(UniNode, self).__init__()

        self.add_object_input('in')
        self.add_object_output('out')
