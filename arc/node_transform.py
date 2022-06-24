from arc.actions import Action
from arc.labeler import Labeler, all_traits
from arc.link import ObjectDelta
from arc.node import ArgInfo, Node, TransformArgs, VarNode
from arc.node_selection import SelectionNode
from arc.object import Object
from arc.object_types import LinkGroup, ObjectCache, ObjectGroup, VarCache
from arc.types import Args
from arc.util import logger

log = logger.fancy_logger("TransformNode", level=20)


class TransformNode(Node):
    def __init__(
        self,
        action: type[Action],
        arg_info: ArgInfo = tuple(),
        parents: set["Node"] | None = None,
        children: set["Node"] | None = None,
        secondary: "Node | None" = None,
    ) -> None:
        super().__init__(parents or set(), children or set(), secondary)
        self.action = action
        self.arg_info = arg_info

    @property
    def name(self) -> str:
        return f"Transform"

    @property
    def props(self) -> int:
        return 1 + len(self.arg_info)

    @property
    def specs(self) -> list[str]:
        arg_info = "(*)" if self.secondary else self.arg_info
        return [f"{self.action}{arg_info}"]

    def apply(
        self, object_cache: ObjectCache, var_cache: VarCache
    ) -> list[Object] | None:
        input_objects, labeler = self.fetch_inputs(object_cache)

        result: list[Object] = []
        for object in input_objects:
            args: TransformArgs = tuple([])
            if self.secondary:
                if isinstance(self.secondary, VarNode):
                    args = (var_cache[self.secondary.uid],)
                else:
                    args = (object_cache[self.secondary.uid][0],)
            else:
                for arg in self.arg_info:
                    if isinstance(arg, tuple):
                        trait, mapping = arg
                        trait_value = labeler.labels[object.uid].get(trait)
                        log.debug(
                            f"Transforming using {self.action}({trait} mapping {mapping})"
                        )
                        try:
                            # Seems like structural pattern matching confuses type checking
                            args += (mapping[trait_value],)  # type: ignore
                        except KeyError as _:
                            log.info(f"Mapping {mapping} doesn't contain {trait_value}")
                            return None
                    else:
                        args += (arg,)

            result.append(self.action.act(object, *args))

        object_cache[self.uid] = result
        return result

    @classmethod
    def from_action(
        cls,
        action: type[Action],
        link_node: LinkGroup,
    ) -> "TransformNode | None":

        args: ArgInfo = tuple([])
        deltas = [delta for group in link_node for delta in group]
        selection = [[delta.left for delta in group] for group in link_node]

        # TODO NOTE We have a single transform (code len == 1)
        raw_args: set[Args] = set()
        for delta in deltas:
            d_args = delta.transform.args
            if not d_args:
                raw_args.add(tuple([]))
            else:
                raw_args.add(action.rearg(delta.left, *(d_args[0])))

        if len(raw_args) > 1:
            if len(list(raw_args)[0]) > 1:
                log.warning(f"Cannot map multi-args")
                return None
            # Non-null, non-constant action arguments means we need a mapping
            # or a secondary object to provide the value.
            labeler = Labeler(selection)
            arg_mapping = cls.determine_map(deltas, labeler)
            if not arg_mapping[0]:
                return None
            args = (arg_mapping,)
        else:
            if None in raw_args:
                return None
            args = tuple(map(int, raw_args.pop()))

        if args is None or None in args or len(args) > action.n_args:
            return None

        return cls(action, args)

    @staticmethod
    def determine_map(
        delta_list: list[ObjectDelta],
        labeler: Labeler,
    ) -> tuple[str, dict[int, int]]:
        result: tuple[str, dict[int, int]] = ("", {})
        for trait in all_traits:
            trial_map: dict[int, int] = {}
            for delta in delta_list:
                inp = labeler.labels[delta.left.uid][trait]
                # TODO We're assuming a single action with a single arg for now
                if not delta.transform.args or not delta.transform.args[0]:
                    return result
                out = delta.transform.args[0][0]

                if inp in trial_map:
                    # TODO: Handle Labeling with type safety, non-mutation
                    if trial_map[inp] != out:  # type: ignore
                        log.debug(
                            f"Trait {trait} fails at {inp} -> {out} | {trial_map}"
                        )
                        trial_map = {}
                        break
                    else:
                        continue
                trial_map[inp] = out  # type: ignore

            if trial_map:
                log.debug(f"Trait {trait}: {trial_map}")
                if not result[0] or len(trial_map) < len(result[1]):
                    result = (trait, trial_map)
        return result

    @classmethod
    def from_pairwise_action(
        cls,
        action: type[Action],
        link_node: LinkGroup,
        inputs: ObjectGroup,
    ) -> "TransformNode | None":
        log.debug(f"Determining selector for {action}")
        secondaries: list[Object] = []
        for delta_group, candidates in zip(link_node, inputs):
            for delta in delta_group:
                for obj in candidates:
                    # TODO Figure out a better way for an object to not be
                    # matched up with its children
                    if obj in delta.left.children:
                        continue
                    if action.act(delta.left, obj) == delta.right:
                        log.debug(f"Choosing secondary: {obj}")
                        secondaries.append(obj)
                        break
        if len(secondaries) < len(link_node):
            log.info(f"Insufficient secondaries found for {action}")
            return None
        selection_node = SelectionNode.from_data(inputs, [secondaries])
        log.info(f"Pairwise selector for {action}: {selection_node}")
        trans_node = cls(action, arg_info=tuple(), secondary=selection_node)
        selection_node.adopt(trans_node)
        return trans_node
