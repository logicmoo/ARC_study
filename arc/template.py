import collections
from copy import deepcopy
from typing import Literal, TypeAlias, TypedDict
from arc.actions import Action

from arc.definitions import Constants as cst
from arc.object import Object
from arc.generator import Generator, Transform
from arc.types import ObjectPath
from arc.util import logger
from arc.util.common import all_equal

log = logger.fancy_logger("Template", level=30)

GeneratorPath: TypeAlias = tuple[int] | tuple[int, int]
PropertyPath: TypeAlias = str | GeneratorPath
Unknown: TypeAlias = Literal["?"]
Variables: TypeAlias = dict[ObjectPath, set[PropertyPath]]

Environment: TypeAlias = dict[tuple[ObjectPath, PropertyPath], int]
MatchInventory: TypeAlias = dict[ObjectPath, Object]


class CommonProperties(TypedDict, total=False):
    row: int | Unknown
    col: int | Unknown
    color: int | Unknown


class StructureDef(TypedDict):
    props: CommonProperties
    generator: tuple[str, ...]
    children: list["StructureDef"]


class Template:
    """Represent the output specification of the Task."""

    def __init__(
        self, structure: StructureDef | None = None, variables: Variables | None = None
    ) -> None:
        self.structure: StructureDef = structure or Template._init_structure()
        self.variables: Variables = variables or {}

    def __repr__(self) -> str:
        return "\n".join(self._display_node(tuple([])))

    def __bool__(self) -> bool:
        return True
        # return self.holes == -1

    @classmethod
    def from_outputs(
        cls, objs: list[Object], path: ObjectPath = tuple([])
    ) -> "Template":
        """Return the specification for the common elements among Objects."""
        structure, variables = Template.recursive_compare(objs, path)
        return cls(structure, variables)

    @property
    def props(self) -> int:
        """Measure of the Template complexity, based on Variables.

        The goal of a good Template representation is to minimize how
        many variables require insertion to generate the output.
        """
        return sum(len(var) for var in self.variables.values())

    @property
    def holes(self) -> int:
        """How many container objects are missing.

        These should be plugged by valid scene matches.
        """
        # The, odd, null case is when the root object has children but no structure
        # is identified
        if tuple([]) in self.variables and self.variables[tuple([])] == {"children"}:
            return -1
        child_vars = {
            key: val for key, val in self.variables.items() if "children" in val
        }
        return len(child_vars)

    @staticmethod
    def _init_structure() -> StructureDef:
        return {
            "props": {},
            "generator": tuple([]),
            "children": [],
        }

    def _display_node(self, path: ObjectPath) -> list[str]:
        depth = len(path)
        indent = "  " * depth
        node = self.get_path(path, self.structure)
        args = [f"{arg} = {val}" for arg, val in node["props"].items()]
        if gen := node["generator"]:
            args.append(f"generator = {gen}")
        line = f"{indent}({', '.join(args)})"
        display: list[str] = [line]
        for idx in range(len(node["children"])):
            display.extend(self._display_node(path + (idx,)))
        return display

    @staticmethod
    def get_path(path: ObjectPath, root: StructureDef) -> StructureDef:
        node: StructureDef = root
        if not path:
            return node
        for child_idx in path:
            try:
                node = node.get("children", [])[child_idx]
            except:
                log.warning(f"Can't access path {path}")
        return node

    def generate(self, env: Environment) -> Object:
        """Create an Object representing the template."""

        # Use the environment to fill in any variables.
        structure = deepcopy(self.structure)
        for (obj_path, prop_path), val in env.items():
            obj_args = self.get_path(obj_path, structure)
            if isinstance(prop_path, str):
                obj_args[prop_path] = val
            else:
                idx = prop_path[0]
                gen = obj_args["generator"]
                code = gen[idx]
                if len(prop_path) == 1:
                    # Swap the copies arg (last char) out for the value
                    code = code[:-1] + str(val)
                obj_args["generator"] = gen[:idx] + (code,) + gen[idx:]

        return self._generate(structure)

    @classmethod
    def _generate(cls, structure: StructureDef) -> Object:
        children: list[Object] = [
            cls._generate(child_struc) for child_struc in structure["children"]
        ]
        if "?" in "".join(structure["generator"]):
            generator = None
        else:
            generator = Generator.from_codes(structure["generator"])
        props = {key: val for key, val in structure["props"].items() if val != "?"}
        return Object(children=children, generator=generator, **props)

    @staticmethod
    def recursive_compare(
        objs: list["Object"], path: ObjectPath
    ) -> tuple[StructureDef, Variables]:
        structure = Template._init_structure()
        variables: Variables = collections.defaultdict(set)

        # Get the info present at this level
        common, vars = Template.compare_properties(objs)
        structure.update(common)  # type: ignore
        if vars:
            variables[path] = vars

        # Look at each child via recursion
        child_structures: list[StructureDef] = []
        child_variables: Variables = collections.defaultdict(set)
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
            if not all_equal(kid_group):
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
                variables[path] = {"children"}
        return structure, variables

    @staticmethod
    def compare_properties(
        objs: list["Object"],
    ) -> tuple[StructureDef, set[PropertyPath]]:
        struc = Template._init_structure()
        vars: set[PropertyPath] = set([])

        # Row, Column, and Color are handled simply
        for prop, default in [
            ("row", cst.DEFAULT_ROW),
            ("col", cst.DEFAULT_COL),
            ("color", cst.DEFAULT_COLOR),
        ]:
            cts = collections.Counter([getattr(obj, prop) for obj in objs])
            if len(cts) == 1:
                if (val := next(iter(cts))) != default:
                    struc["props"][prop] = val
            else:
                struc["props"][prop] = "?"
                vars.add(prop)

        ## The Generator requires a few levels of handling
        gen_repr: tuple[str, ...] = tuple([])

        # First, compare length of the Transforms for each object. If there is a
        # mismatch, we should determine the most likely scenario
        if not all_equal([len(obj.generator) for obj in objs]):
            log.warning(f"Mismatch in number of generator transforms: {objs}")
            return struc, vars

        if not objs[0].generator:
            return struc, vars

        trans_repr: list[str] = []

        # Get the list of nth transforms across generators
        transforms: list[list[Transform]] = [obj.generator.transforms for obj in objs]
        for t_idx, trans_cut in enumerate(zip(*transforms)):
            if not all_equal([len(trans) for trans in trans_cut]):
                # TODO Implement
                log.warning(f"Mismatch in length of transform actions: {trans_cut}")
                return struc, vars

            common_actions: str = ""
            # TODO Only support arg-less actions for now, for simplicity
            for a_idx, actions in enumerate(
                zip(*[trans.actions for trans in trans_cut])
            ):
                if not all_equal(actions):
                    vars.add((t_idx, a_idx))
                    common_actions += "?"
                else:
                    common_actions += Action().rev_map[actions[0].__name__]

            trans_repr.append(common_actions)

        common_copies: list[str] = []
        for c_idx, copies_cut in enumerate(
            zip(*[obj.generator.copies for obj in objs])
        ):
            if not all_equal(copies_cut):
                vars.add((c_idx,))
                common_copies.append("?")
            else:
                common_copies.append(str(copies_cut[0]))

        for trans, copies in zip(trans_repr, common_copies):
            gen_repr += (f"{trans}*{copies}",)

        struc["generator"] = gen_repr

        return struc, vars
