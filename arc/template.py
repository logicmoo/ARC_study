import collections
from copy import deepcopy
from typing import Literal, TypeAlias, TypedDict
from arc.actions import Action

from arc.definitions import Constants as cst
from arc.object import Object, ObjectPath
from arc.generator import Generator, Transform
from arc.types import BaseObjectPath, PropertyPath
from arc.util import logger
from arc.util.common import all_equal

log = logger.fancy_logger("Template", level=20)

Unknown: TypeAlias = Literal["?"]
Variables: TypeAlias = set[ObjectPath]

Environment: TypeAlias = dict[ObjectPath, int]
MatchInventory: TypeAlias = dict[ObjectPath, list[Object]]


class CommonProperties(TypedDict, total=False):
    row: int | Unknown
    col: int | Unknown
    color: int | Unknown
    row_bound: int | Unknown
    col_bound: int | Unknown


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

    # @property
    # def holes(self) -> int:
    #     """How many container objects are missing.

    #     These should be plugged by valid scene matches.
    #     """
    #     # The, odd, null case is when the root object has children but no structure
    #     # is identified
    #     if tuple([]) in self.variables and self.variables[tuple([])] == {"children"}:
    #         return -1
    #     child_vars = {
    #         key: val for key, val in self.variables.items() if "children" in val
    #     }
    #     return len(child_vars)

    @staticmethod
    def _init_structure() -> StructureDef:
        return {
            "props": {},
            "generator": tuple([]),
            "children": [],
        }

    def _display_node(self, path: BaseObjectPath) -> list[str]:
        depth = len(path)
        indent = "  " * depth
        node = self.get_base(path, self.structure)
        args = [f"{arg} = {val}" for arg, val in node["props"].items()]
        if gen := node["generator"]:
            args.append(f"generator = {gen}")
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
            return node["props"].get(path.property, cst.DEFAULT[path.property])

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
            else:
                log.warning("Need to implement Generator value insertions")

    # def generate(self, env: Environment, matches: MatchInventory) -> Object:
    #     """Create an Object representing the template."""

    #     # Use the environment to fill in any variables.
    #     structure = deepcopy(self.structure)
    #     for obj_path, val in env.items():
    #         obj_args = self.get_base(obj_path.base, structure)
    #         if not isinstance(obj_path.property, str):
    #             continue
    #         obj_args["props"][obj_path.property] = val

    #     # Eliminate any paths contained in the matches
    #     log.info(f"Generating with {len(matches)} matches:")
    #     for path, _ in sorted(matches.items(), reverse=True):
    #         log.info(f"  -> {path}")
    #         if path:
    #             self.get_base(path.base[:-1], structure)["children"].pop(path.base[-1])

    #     # Create an Object based on the StructureDef
    #     frame: Object = self._generate(structure)

    #     # Lastly, add any transformed objects into the frame
    #     for path, objs in sorted(matches.items()):
    #         if not path:
    #             if len(objs) != 1:
    #                 log.warning("Multiple Objects inserted at frame root")
    #             return objs[0]

    #         target = frame.get_path(path.base[:-1])
    #         if target:
    #             target.children.extend(objs)

    #     return frame

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
            # otherwise, we insert a generic variable for "children"
            else:
                variables.add(ObjectPath(base))
        return structure, variables

    @staticmethod
    def compare_properties(
        objs: list["Object"],
    ) -> tuple[StructureDef, set[PropertyPath]]:
        struc = Template._init_structure()
        vars: set[PropertyPath] = set([])

        # Basic properties
        for prop in ["row", "col", "color", "row_bound", "col_bound"]:
            cts = collections.Counter([getattr(obj, prop) for obj in objs])
            if len(cts) == 1:
                if (val := next(iter(cts))) != cst.DEFAULT[prop]:
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
