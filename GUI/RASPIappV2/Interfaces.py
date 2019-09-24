'''
    Set op modules (classes) used for the toolbox for easier handling.
'''


class uc2Button:
    '''
    General interface for Script-Classes based on buttons
    '''
    # parameters --------------------------------------------
    active = False
    control_group = None
    config = None
    name = None
    uniid = None
    # fuctions ----------------------------------------------

    def __init__(self, control_group=None, uniid=uniid, name=name, config=config):
        self.control_group = control_group
        self.uniid = uniid
        self.name = name
        self.config = config

    def __repr__(self):
        print("Control Group={}\nConfig={}".format(
            self.control_group, self.config))

    def __change_activation(self):
        self.control_group.change_activation_status(self)
        self.active = !False


class uc2ControlGroup:
    '''
    To control and isolate the different behaviour of buttons and their functions from a set of similars.
    '''
    # parameters --------------------------------------------
    name = None
    child_list = []
    activation_rules_map = []
    # fuctions ----------------------------------------------

    def __init__(self, name=None, child_list=[], activation_rules_map=[]):
        self.name = name
        self.child_list = child_list
        self.activation_rules_map = activation_rules_map

    def child_add(self, child_new=None):
        self.child_list.append(child_new)

    def child_remove(self, child_remove=None):
        self.child_list.remove(child_remove)

    def __change_activation(self, caller):
        '''
        Changes the activation status of a 'caller' according to the Control-groups activation_rules_map
        '''
        if caller.active
