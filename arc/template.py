import collections
import copy
from typing import TypeAlias, TypedDict

from arc.definitions import Constants as cst
from arc.object import Object
from arc.generator import Generator
from arc.util import logger

log = logger.fancy_logger("Template", level=30)

ObjectPath: TypeAlias = tuple[int, ...]
Variables: TypeAlias = dict[ObjectPath, list[str]]


class CommonProperties(TypedDict, total=False):
    row: int
    col: int
    color: int
    generator: list[str]


class StructureDef(TypedDict, total=False):
    row: int
    col: int
    color: int
    generator: list[str]
    children: list["StructureDef"]


class Template:
    """Represent the output specification of the Task."""

    def __init__(self, structure: StructureDef, variables: Variables) -> None:
        self.structure: StructureDef = structure
        self.variables: Variables = variables

    def __repr__(self) -> str:
        return "\n".join(self._display_node(tuple([])))

    def _display_node(self, path: ObjectPath) -> list[str]:
        depth = len(path)
        indent = "  " * depth
        node = self.get_node(path)
        args = [f"{arg} = {val}" for arg, val in node.items() if arg != "children"]

        line = f"{indent}({', '.join(args)})"
        display: list[str] = [line]
        for idx in range(len(node.get("children", []))):
            display.extend(self._display_node(path + (idx,)))
        return display

    def get_node(self, path: ObjectPath) -> StructureDef:
        node: StructureDef = self.structure
        if not path:
            return node
        for child_idx in path:
            try:
                node = node.get("children", [])[child_idx]
            except:
                log.warning(f"Can't access path {path}")
        return node

    @classmethod
    def from_outputs(cls, objs: list[Object], path: ObjectPath) -> "Template":
        """Return the specification for the common elements among Objects."""
        structure, variables = Template.recursive_compare(objs, path)
        return cls(structure, variables)

    def generate(self) -> Object:
        """Create an Object representing the template."""
        return self._generate(copy.deepcopy(self.structure))

    def _generate(self, structure: StructureDef) -> "Object":
        children = [
            self._generate(child_struc) for child_struc in structure.pop("children", [])
        ]
        generator = None
        if gen_codes := structure.pop("generator", None):
            # TODO Fix the typing for codes output and input
            generator = Generator.from_codes(gen_codes)  # type: ignore
        return Object(children=children, generator=generator, **structure)  # type: ignore

    @staticmethod
    def recursive_compare(
        objs: list["Object"], path: ObjectPath
    ) -> tuple[StructureDef, Variables]:
        structure: StructureDef = {}
        variables: Variables = collections.defaultdict(list)

        # Get the info present at this level
        common, vars = Template.compare_properties(objs)
        structure.update(common)  # type: ignore
        variables[path] = vars

        # Look at each child via recursion
        child_structures: list[StructureDef] = []
        child_variables: Variables = collections.defaultdict(list)
        dot_ct = 0
        child_match: bool = True
        for idx, kid_group in enumerate(zip(*[obj.children for obj in objs])):
            # TODO This could require multiple schemas of child-checking
            # as there could be a common child that's not at a constant layer
            # or constant depth.
            kid_structure, kid_variables = Template.recursive_compare(
                list(kid_group), path=path + (idx,)
            )
            child_structures.append(kid_structure)
            child_variables.update(kid_variables)
            if not all([kid == kid_group[0] for kid in kid_group[1:]]):  # type: ignore
                child_match = False
            if any([kid.category == "Dot" for kid in kid_group]):
                dot_ct += 1
        # Only include dot children if there's a limited number, or they all match
        if child_structures or child_variables:
            # If the child structures meets regularity constraints, use them
            if dot_ct <= 5 or child_match:
                structure["children"] = child_structures
                variables.update(child_variables)
            # otherwise, we insert a generic variable for "children"
            else:
                variables[path] = ["children"]
        return structure, variables

    @staticmethod
    def compare_properties(objs: list["Object"]) -> tuple[CommonProperties, list[str]]:
        common_props: CommonProperties = {}
        vars: list[str] = []
        for prop, default in [
            ("row", cst.DEFAULT_ROW),
            ("col", cst.DEFAULT_COL),
            ("color", cst.DEFAULT_COLOR),
        ]:
            cts = collections.Counter([getattr(obj, prop) for obj in objs])
            if len(cts) == 1:
                if (val := next(iter(cts))) != default:
                    common_props[prop] = val
            else:
                vars.append(prop)

        cts = collections.Counter(
            [getattr(obj.generator, "codes", tuple([])) for obj in objs]
        )
        # TODO We need to check for more than just the exact generator
        if len(cts) == 1 and (val := next(iter(cts))) != tuple():
            common_props["generator"] = next(iter(cts))
        return common_props, vars
