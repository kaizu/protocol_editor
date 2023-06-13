from nodes import BasicNode


class ObjectInputNode(BasicNode):
    """
    A node class with 1 output.
    """

    # unique node identifier.
    __identifier__ = 'nodes.sample'

    # initial default node name.
    NODE_NAME = 'ObjectInput'

    def __init__(self):
        super(ObjectInputNode, self).__init__()

        self.add_object_output('out')

class DataInputNode(BasicNode):
    """
    A node class with 1 output.
    """

    # unique node identifier.
    __identifier__ = 'nodes.sample'

    # initial default node name.
    NODE_NAME = 'DataInput'

    def __init__(self):
        super(DataInputNode, self).__init__()

        self.add_data_output('out')

class ObjectOutputNode(BasicNode):
    """
    A node class with 1 input.
    """

    # unique node identifier.
    __identifier__ = 'nodes.sample'

    # initial default node name.
    NODE_NAME = 'ObjectOutput'

    def __init__(self):
        super(ObjectOutputNode, self).__init__()

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
