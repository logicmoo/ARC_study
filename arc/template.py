import collections
from copy import deepcopy
from typing import Literal, TypeAlias, TypedDict
from arc.actions import Actions

from arc.definitions import Constants as cst
from arc.object import Object, ObjectPath
from arc.generator import Generator
from arc.types import BaseObjectPath
from arc.util import logger
from arc.util.common import all_equal

log = logger.fancy_logger("Template", level=20)

Unknown: TypeAlias = Literal["?"]
Variables: TypeAlias = set[ObjectPath]


class CommonProperties(TypedDict, total=False):
    row: int | Unknown
    col: int | Unknown
    color: int | Unknown
    row_bound: int | Unknown
    col_bound: int | Unknown


class StructureDef(TypedDict):
    props: CommonProperties
    children: list["StructureDef"]


class Template:
    """Represent the output specification of the Task."""

    def __init__(
        self, structure: StructureDef | None = None, variables: Variables | None = None
    ) -> None:
        self.structure: StructureDef = structure or Template._init_structure()
        self.variables: Variables = variables or set([])

        # Used during Object generation
        self.frame: StructureDef = Template._init_structure()

    def __repr__(self) -> str:
        structure: str = "\n  ".join(self._display_node(tuple([])))
        variables: str = "\n  ".join(map(str, self.variables))
        return f"\nFrame:\n  {structure}\nVariables:\n  {variables}"

    def __bool__(self) -> bool:
        return True

    @classmethod
    def from_outputs(
        cls, objs: list[Object], base: BaseObjectPath = tuple([])
    ) -> "Template":
        """Return the specification for the common elements among Objects."""
        structure, variables = Template.recursive_compare(objs, base)
        return cls(structure, variables)

    @property
    def props(self) -> int:
        """Measure of the Template complexity, based on Variables.

        The goal of a good Template representation is to minimize how
        many variables require insertion to generate the output.
        """
        return len(self.variables)

    @staticmethod
    def _init_structure() -> StructureDef:
        return {
            "props": {},
            "children": [],
        }

    def _display_node(self, path: BaseObjectPath) -> list[str]:
        depth = len(path)
        indent = "  " * depth
        node = self.get_base(path, self.structure)
        args = [f"{arg} = {val}" for arg, val in node["props"].items()]
        if ObjectPath(path) in self.variables:
            args.append("children = ?")
        line = f"{indent}({', '.join(args)})"
        display: list[str] = [line]
        for idx in range(len(node["children"])):
            display.extend(self._display_node(path + (idx,)))
        return display

    @staticmethod
    def get_base(base: BaseObjectPath, root: StructureDef) -> StructureDef:
        node: StructureDef = root
        if not base:
            return node
        for child_idx in base:
            try:
                node = node["children"][child_idx]
            except:
                log.warning(f"Can't access base path {base}")
        return node

    @staticmethod
    def get_value(path: ObjectPath, root: StructureDef) -> int | None:
        node: StructureDef = Template.get_base(path.base, root)
        if node and isinstance(path.property, str):
            return node["props"].get(path.property, cst.DEFAULT.get(path.property, 0))

    def init_frame(self) -> None:
        self.frame: StructureDef = deepcopy(self.structure)

    def apply_object(self, path: ObjectPath, object: Object) -> None:
        obj_def, _ = Template.recursive_compare([object], tuple([]))
        if not path:
            self.frame = obj_def
            return

        target = self.get_base(path.base[:-1], self.frame)
        if target:
            target["children"][path.base[-1]] = obj_def

    def apply_variable(self, path: ObjectPath, value: int) -> None:
        target = self.get_base(path.base, self.frame)
        if target:
            if isinstance(path.property, str):
                target["props"][path.property] = value

    @classmethod
    def generate(cls, structure: StructureDef) -> Object:
        children: list[Object] = [
            cls.generate(child_struc) for child_struc in structure["children"]
        ]
        # Get core properties
        props = {
            key: val
            for key, val in structure["props"].items()
            if val != "?" and len(key) > 1
        }
        gens = {
            key: val
            for key, val in structure["props"].items()
            if val != 0 and len(key) == 1
        }
        if "?" in gens.values():
            generator = None
        else:
            generator = Generator.from_codes(
                tuple(f"{key}*{val}" for key, val in gens.items())
            )

        return Object(children=children, generator=generator, **props)

    @staticmethod
    def recursive_compare(
        objs: list["Object"], base: BaseObjectPath
    ) -> tuple[StructureDef, Variables]:
        structure = Template._init_structure()
        variables: Variables = set([])

        # Get the info present at this level
        common, vars = Template.compare_properties(objs)
        structure.update(common)
        for var in vars:
            variables.add(ObjectPath(base, var))

        # Look at each child via recursion
        child_structures: list[StructureDef] = []
        child_variables: Variables = set([])
        dot_ct = 0
        child_match: bool = True
        for idx, kid_group in enumerate(zip(*[obj.children for obj in objs])):
            # TODO This could require multiple schemas of child-checking
            # as there could be a common child that's not at a constant layer
            # or constant depth.
            kid_structure, kid_variables = Template.recursive_compare(
                list(kid_group), base=base + (idx,)
            )
            child_structures.append(kid_structure)
            child_variables |= kid_variables
            if not all_equal(kid_group):
                child_match = False
            if any([kid.category == "Dot" for kid in kid_group]):
                dot_ct += 1
        # Only include dot children if there's a limited number, or they all match
        if child_structures or child_variables:
            # If the child structures meets regularity constraints, use them
            if dot_ct <= 5 or child_match:
                structure["children"] = child_structures
                variables |= child_variables
            # otherwise, we insert a BaseObjectPath only for "children"
            else:
                variables.add(ObjectPath(base))
        return structure, variables

    @staticmethod
    def compare_properties(objs: list["Object"]) -> tuple[StructureDef, set[str]]:
        struc = Template._init_structure()
        vars: set[str] = set([])

        # Basic properties. cst.DEFAULT contains each with a default value
        for prop in cst.DEFAULT:
            cts = collections.Counter([getattr(obj, prop) for obj in objs])
            if len(cts) == 1:
                if (val := next(iter(cts))) != cst.DEFAULT[prop]:
                    struc["props"][prop] = val
            else:
                struc["props"][prop] = "?"
                vars.add(prop)  # type: ignore (prop is seen as generic 'str')

        # Access generating codes in the objects
        for code in Actions.map:
            cts = collections.Counter([obj.codes[code] for obj in objs])
            if len(cts) == 1:
                if (val := next(iter(cts))) != 0:
                    struc["props"][code] = val
            else:
                struc["props"][code] = "?"
                vars.add(code)  # type: ignore (prop is seen as generic 'str')

        return struc, vars
