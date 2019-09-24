# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------
# Class function override and mangeling example


class Minortest:
    def __init__(self, myiter):
        self.list = []
        self.__update(myiter)

    def __update(self, myiter):
        for item in myiter:
            self.list.append(item)
        print("I was called from Minortest.")


class MinortestSub(Minortest):
    def __update(self, myiter):
        for item in myiter:
            self.list.append(item)
            self.list.append(item)
        print("I was called from MinortestSub.")


# Test code
myiter = [1, 2, 3, 4]
a = Minortest(myiter)
b = MinortestSub(myiter)

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------
# Buttons and Control-Group test (and ignore input-error catching)


class uc2ControlGroup:
    # param
    child_list = []
    name = None

    def __init__(self, name=None, child_list=[]):
        self.name = name
        self.child_list = child_list

    def add_childs(self, child_list=[]):
        for child in child_list:
            self.child_list.append(child)

    def remove_childs(self, child_list=[]):
        for child in child_list:
            self.child_list.remove(child)

    def __repr__(self):
        for myc in range(0, len(self.child_list)):
            print("My Child[{}] is: {}".format(myc, self.child_list[myc]))

    def __str__(self):

        return '. '.join(['List name={}'.format(name), [str(x) for x in child_list]])


class uc2Button:
    # param
    name = None
    uniid = None
    control_group = None
    # func

    def __init__(self, name=None, uniid=None, control_group=None):
        self.name = name
        self.uniid = uniid
        self.control_group = control_group

    def __str__(self):
        return '. '.join([str(self.name), str(self.uniid), str(self.control_group)])


class uc2Identifier:
    # param
    nbr = 0
    identified_list = []

    # fucn
    def __init__(self, nbr=0, identified_list=[]):
        self.nbr = nbr
        self.identified_list = identified_list

    def get_new_uniid(self):
        self.nbr += 1
        return self.nbr


# Test code
cg_lights = uc2ControlGroup(name="cg_lights", child_list=[])
uc2i = uc2Identifier(nbr=0)
button_cus = uc2Button(
    name="Custom", uniid=uc2i.get_new_uniid, control_group="cg_lights")
button_qDPC = uc2Button(
    name="qDPC", uniid=uc2i.get_new_uniid, control_group="cg_lights")
button_fluo = uc2Button(
    name="Fluo", uniid=uc2i.get_new_uniid, control_group="cg_lights")

print(cg_lights)
print("Now adding the elements")
cg_lights.add_childs([button_cus, button_fluo, button_qDPC])
print(cg_lights)


# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------
# playing with map, zip
def myfunc(a=1, b=1):
    return (a*b)/(a+b)


a = [1, 2, 3, 4, 5]
b = [9, 8, 7, 5, 4]

c = map(myfunc, a, b)
print(list(c))

# same with lambda
d = map(lambda x, y: (x*y)/(x+y), a, b)
print(list(d))
