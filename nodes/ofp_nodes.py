from nodes import BasicNode


class SaveArtifactsNode(BasicNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'SaveArtifacts'

    def __init__(self):
        super(SaveArtifactsNode, self).__init__()

        # create node inputs.
        self.add_data_input('in', multi_input=True)

        # create QLineEdit text input widget.
        self.add_text_input('artifact_name', 'Name', 'name', tab='widgets')


class DiscardNode(BasicNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'Discard'

    def __init__(self):
        super(DiscardNode, self).__init__()

        # create node outputs.
        self.add_object_input('in', multi_input=True)


class SupplyLiquidNode(BasicNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'SupplyLiquid'

    def __init__(self):
        super(SupplyLiquidNode, self).__init__()

        # create node outputs.
        self.add_object_output('out', multi_output=True)

        # create the QComboBox menu.
        items = ['Pure Water', 'Red', 'Blue', 'Yellow']
        self.add_combo_menu('liquid_type', 'Type', items=items)


class NumberInputNode(BasicNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'NumberInput'

    def __init__(self):
        super(NumberInputNode, self).__init__()

        # create node outputs.
        self.add_data_output('value')

        # create the QComboBox menu.
        items = ['Integer', 'Float']
        self.add_combo_menu('value_type', 'Type', items=items)

        # create QLineEdit text input widget.
        self.add_text_input('value', 'Value', '0', tab='widgets')


class SupplyContainerSingleNode(BasicNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'SupplyContainerSingle'

    def __init__(self):
        super(SupplyContainerSingleNode, self).__init__()

        # create node outputs.
        self.add_object_output('out', multi_output=True)

        # create the QComboBox menu.
        items = ['1.5mL Tube', '300uL Well']
        self.add_combo_menu('container_type', 'Type', items=items)


class SupplyContainerArrayNode(BasicNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'SupplyContainerArray'

    def __init__(self):
        super(SupplyContainerArrayNode, self).__init__()

        # create node outputs.
        self.add_object_output('out', multi_output=True)

        # create the QComboBox menu.
        items = ['1.5mL Tube', '300uL Well']
        self.add_combo_menu('container_type', 'Type', items=items)

        # create QLineEdit text input widget.
        self.add_text_input('array_size', 'Size', '96', tab='widgets')


class DispenseLiquidNode(BasicNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'DispenseLiquid'

    def __init__(self):
        super(DispenseLiquidNode, self).__init__()

        # create node inputs.
        self.add_data_input('quantity')
        self.add_object_input('from')
        self.add_object_input('to')

        # create node outputs.
        self.add_object_output('from')
        self.add_object_output('to')

        # create the QComboBox menu.
        items = ['uL', 'mL']
        self.add_combo_menu('unit', 'Unit', items=items)


class MeasureAbsorbanceNode(BasicNode):
    """
    A node class with 2 inputs and 2 outputs.
    """

    # unique node identifier.
    __identifier__ = 'OFP.nodes'

    # initial default node name.
    NODE_NAME = 'MeasureAbsorbance'

    def __init__(self):
        super(MeasureAbsorbanceNode, self).__init__()

        # create node inputs.
        self.add_object_input('in')

        # create node outputs.
        self.add_object_output('out')
        self.add_data_output('absorbance')
