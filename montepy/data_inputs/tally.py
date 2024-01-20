# Copyright 2024, Battelle Energy Alliance, LLC All Rights Reserved.
import copy

import montepy
from montepy.cells import Cells
from montepy.data_inputs.data_input import DataInputAbstract
from montepy.data_inputs.tally_type import TallyType
from montepy.input_parser.tally_parser import TallyParser
from montepy.input_parser import syntax_node
from montepy.numbered_mcnp_object import Numbered_MCNP_Object
from montepy.surface_collection import Surfaces
from montepy.utilities import *

_TALLY_TYPE_MODULUS = 10


def _number_validator(self, number):
    if number <= 0:
        raise ValueError("number must be > 0")
    if number % _TALL_TYPE_MODULUS != self._type.value:
        raise ValueError(f"Tally Type cannot be changed.")
    if self._problem:
        self._problem.tallies.check_number(number)


class Tally(DataInputAbstract, Numbered_MCNP_Object):
    """ """

    # todo type enforcement
    _parser = TallyParser()

    __slots__ = {"_groups", "_type", "_number", "_old_number", "_include_total"}

    def __init__(self, input=None, other_tally=None):
        self._old_number = None
        self._number = self._generate_default_node(int, -1)
        super().__init__(input)
        if other_tally is not None:
            self._from_other_tally(other_tally)
        if input:
            num = self._input_number
            self._old_number = copy.deepcopy(num)
            self._number = num
            try:
                tally_type = TallyType(self.number % _TALLY_TYPE_MODULUS)
            except ValueError as e:
                raise MalformedInputEror(input, f"Tally Type provided not allowed: {e}")
            groups, has_total = TallyGroup.parse_tally_specification(
                self._tree["tally"]
            )
            self._groups = groups
            self._include_total = has_total

    def _from_other_tally(self, other, deepcopy=False):
        if other._type != self._allowed_type:
            # todo
            pass
        for attr in {"_tree", "_old_number", "_number", "_groups", "_include_total"}:
            setattr(self, attr, getattr(other, attr))

    @classmethod
    def parse_tally_input(cls, input):
        base_tally = cls(input)
        new_class = TALLY_TYPE_CLASS_MAP[base_tally._type]

    @staticmethod
    def _class_prefix():
        return "f"

    @staticmethod
    def _has_number():
        return True

    @staticmethod
    def _has_classifier():
        return 2

    @make_prop_val_node("_old_number")
    def old_number(self):
        """
        The material number that was used in the read file

        :rtype: int
        """
        pass

    @make_prop_val_node("_number", int, validator=_number_validator)
    def number(self):
        """
        The number to use to identify the material by

        :rtype: int
        """
        pass

    def update_pointers(self, data_inputs):
        if self._problem is not None:
            for group in self.groups:
                group.update_pointers(self.problem, *self._obj_type)


class SurfaceTally(Tally):
    _obj_type = (Surfaces, "surface")


class CellTally(Tally):
    _obj_type = (Cells, "cell")


class CellFluxTally(CellTally):
    _allowed_type = TallyType.CELL_FLUX


class TallyGroup:
    __slots__ = {"_objs", "_old_numbers", "_obj_name"}

    def __init__(self, cells=None, nodes=None):
        self._cells = None
        self._old_numbers = []
        self._obj_name = ""

    @staticmethod
    def parse_tally_specification(tally_spec):
        # TODO type enforcement
        ret = []
        in_parens = False
        buff = None
        has_total = False
        for node in tally_spec:
            if in_parens:
                if node.value == ")":
                    in_parens = False
                    buff._append_node(node)
                    ret.append(buff)
                    buff = None
                else:
                    buff._append_node(node)
            else:
                if node.value == "(":
                    in_parens = True
                    buff = TallyGroup()
                    buff._append_node(node)
                else:
                    if (
                        isinstance(node, syntax_node.ValueNode)
                        and node.type == str
                        and node.value.lower() == "t"
                    ):
                        has_total = True
                    else:
                        ret.append(TallyGroup(nodes=[node]))
        return (ret, has_total)

    def _append_node(self, node):
        if not isinstance(node, syntax_node.ValueNode):
            raise ValueError(f"Can only append ValueNode. {node} given")
        self._old_numbers.append(node)

    def append(self, cell):
        self._cells.append(cell)

    def update_pointers(self, problem, ObjContainer, obj_name):
        self._objs = ObjContainer()
        obj_source = getattr(problem, f"{obj_name}s")
        self._obj_name = obj_name
        for number in self._older_numbers:
            try:
                self._objs.append(obj_source[number])
            except KeyError:
                # Todo
                pass


TALLY_TYPE_CLASS_MAP = {
    # TallyType.CURRENT: CurrentTally,
    # TallyTpe.SURFACE_FLUX: SurfaceFluxTally,
    TallyType.CELL_FLUX: CellFluxTally
    # TODO
}
