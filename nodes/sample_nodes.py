from nodes import BasicNode


class SampleNode(BasicNode):
    """
    A node base class.
    """

    # unique node identifier.
    __identifier__ = 'nodes.sample'

    # initial default node name.
    NODE_NAME = 'Sample'

    def __init__(self):
        super(SampleNode, self).__init__()
        self.add_text_input('station', '', tab='widgets')

class ObjectInputNode(SampleNode):
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

class DataOutputNode(SampleNode):
    """
    A node class with 1 input.
    """

    # unique node identifier.
    __identifier__ = 'nodes.sample'

    # initial default node name.
    NODE_NAME = 'DataOutput'

    def __init__(self):
        super(DataOutputNode, self).__init__()

        self.add_data_input('in')

class ObjectOutputNode(SampleNode):
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

class UniNode(SampleNode):
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

class BiNode(SampleNode):
    """
    A node class with 2 input and 2 output.
    """

    # unique node identifier.
    __identifier__ = 'nodes.sample'

    # initial default node name.
    NODE_NAME = 'Bi'

    def __init__(self):
        super(BiNode, self).__init__()

        self.add_object_input('in1')
        self.add_object_input('in2')
        self.add_object_output('out1')
        self.add_object_output('out2')

class MeasurementNode(SampleNode):
    """
    A node class with 1 input and 2 output.
    """

    # unique node identifier.
    __identifier__ = 'nodes.sample'

    # initial default node name.
    NODE_NAME = 'Measurement'

    def __init__(self):
        super(MeasurementNode, self).__init__()

        self.add_object_input('in')
        self.add_object_output('out')
        self.add_data_output('value')