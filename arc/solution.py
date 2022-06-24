import uuid
from collections import defaultdict

from arc.actions import Action, Actions, Pairwise
from arc.link import ObjectDelta, VariableLink
from arc.node import Node, RootNode, TerminalNode, VarNode
from arc.node_selection import SelectionNode
from arc.node_transform import TransformNode
from arc.object import Object, ObjectPath
from arc.object_types import Cache, LinkGroup, ObjectGroup
from arc.scene import Scene
from arc.template import Template
from arc.util import logger

log = logger.fancy_logger("Solution", level=20)


class Solution:
    """Contain the information needed to convert an input board to a correct output.

    A solution is a directed graph of transformation nodes that takes a raw input board
    and can create the correct output board. Each solution is presumed to have
    decomposition as the first node/step in the process. The result of decomposition
    is then fed into 1+ nodes organized in 1+ layers.
    """

    def __init__(
        self,
        characteristic: str = "",
        attention: int | None = None,
        template: Template | None = None,
    ) -> None:
        self.characteristic: str = characteristic
        self.template: Template = template or Template()

        # Used during 'bundle()'
        self.bundled: dict[str, list[ObjectDelta]] = defaultdict(list)
        self.var_targets: dict[ObjectPath, list[VariableLink]] = defaultdict(list)

        # Created during 'create_nodes()'
        self.nodes: dict[uuid.UUID, Node] = {}
        self.root: RootNode = RootNode(attention)
        self.terminus: TerminalNode = TerminalNode(self.template.init_structure(), {})

    def __repr__(self) -> str:
        msg: list[str] = [f"Decomposition characteristic: {self.characteristic}"]
        msg += [f"Level attention: {self.root.level_attention}"]
        msg.append(self.root.tree())
        msg.append(str(self.template))
        return "\n".join(msg)

    def bundle(self, cases: list[Scene]) -> None:
        """Bundle object transforms together from the Scene link maps.

        This aims to approximately identify the SolutionNodes we need.
        """
        self.bundled: dict[str, list[ObjectDelta]] = defaultdict(list)
        self.var_targets: dict[ObjectPath, list[VariableLink]] = defaultdict(list)
        for case in cases:
            for path, link in case.link_map.items():
                if isinstance(link, ObjectDelta):
                    self.bundled[link.transform.char].append(link)
                else:
                    self.var_targets[path].append(link)

    def create_nodes(self, cases: list[Scene]) -> bool:
        inputs = [
            self.root.apply({uuid.uuid4(): [case.input.rep]}, {}) for case in cases
        ]
        caches: list[Cache] = []

        self.terminus: TerminalNode = TerminalNode(self.template.structure, {})
        self.nodes = {self.root.uid: self.root, self.terminus.uid: self.terminus}

        for path, links in self.var_targets.items():
            selection: ObjectGroup = [[link.left] for link in links]
            if selection_node := SelectionNode.from_data(inputs, selection):
                self.root.adopt(selection_node)
                self.nodes[selection_node.uid] = selection_node
            property = links[0].property
            if var_node := VarNode.from_property(property, selection):
                selection_node.adopt(var_node)
                var_node.adopt(self.terminus)
                self.terminus.path_map[var_node.uid] = {path}
                self.nodes[var_node.uid] = var_node

        for code, transform_group in self.bundled.items():
            if len(code) > 1:
                log.info(f"Skip (code > 1), e.g. Link 0 {transform_group[0]}")
                continue

            # The link node is a list of lists of ObjectDeltas related to the transform
            link_node: list[list[ObjectDelta]] = []
            for case in cases:
                case_node = [
                    delta for delta in transform_group if delta.tag == case.idx
                ]
                link_node.append(case_node)
            link_node = list(filter(None, link_node))
            selection = [[delta.left for delta in group] for group in link_node]
            if selection_node := SelectionNode.from_data(inputs, selection):
                self.root.adopt(selection_node)
                self.nodes[selection_node.uid] = selection_node
                caches: list[Cache] = []
                for case in cases:
                    cache: Cache = ({uuid.uuid4(): [case.input.rep]}, {})
                    self.root.apply(*cache)
                    selection_node.apply(*cache)
                    caches.append(cache)
            else:
                return False

            candidate_nodes: list[TransformNode] = []
            base_action = Actions.map[code]
            paths = {ObjectPath(delta.base) for delta in transform_group}
            action_queue = [base_action]
            while action_queue:
                action = action_queue.pop(0)
                # NOTE In general, we cannot have a situation where an action with more
                # args non-trivially replaces an action with fewer.
                if action.n_args > base_action.n_args:
                    continue
                log.debug(f"Attempting Solution node for action '{action}'")
                if issubclass(action, Pairwise):
                    if trans_node := TransformNode.from_pairwise_action(
                        action, link_node, inputs
                    ):
                        candidate_nodes.append(trans_node)
                else:
                    if trans_node := TransformNode.from_action(action, link_node):
                        candidate_nodes.append(trans_node)

                action_queue.extend(action.__subclasses__())

            if node := self.choose_node(
                candidate_nodes, selection_node, caches, link_node
            ):
                if node.action == Action:
                    # Don't add Identity operations
                    selection_node.disown(node)
                    selection_node.adopt(self.terminus)
                    self.terminus.path_map[selection_node.uid] = paths
                else:
                    node.adopt(self.terminus)
                    self.terminus.path_map[node.uid] = paths
                    self.nodes[node.uid] = node
                    if node.secondary:
                        self.nodes[node.secondary.uid] = node.secondary
            else:
                return False
        return True

    def choose_node(
        self,
        candidate_nodes: list[TransformNode],
        selection_node: SelectionNode,
        caches: list[Cache],
        link_node: LinkGroup,
    ) -> TransformNode | None:
        log.info(" --- Candidate nodes:")
        for node in candidate_nodes:
            log.info(node)
        for trans in sorted(candidate_nodes, key=lambda x: x.props):
            valid = True
            selection_node.adopt(trans)
            if trans.secondary:
                self.root.adopt(trans.secondary)
            for cache, deltas in zip(caches, link_node):
                self.root.propagate(*cache)
                result = cache[0].get(trans.uid, None)
                if not result:
                    valid = False
                    selection_node.disown(trans)
                    if trans.secondary:
                        self.root.disown(trans.secondary)
                    break
                result = sorted(result)
                rights = sorted([delta.right for delta in deltas])
                if result != rights:
                    log.info("Mismatch between inputs and ouptuts:")
                    log.info(result)
                    log.info(rights)
                    valid = False
                    selection_node.disown(trans)
                    if trans.secondary:
                        self.root.disown(trans.secondary)
                    break
            if valid:
                log.info(f"Choosing: {trans}")
                return trans

    def generate(self, scene: Scene) -> Object:
        """Create the test output."""
        log.info(f"Generating scene: {scene.idx}")
        if self.characteristic:
            log.info(f"  Decomposing with characteristic: {self.characteristic}")
            scene.input.decompose(characteristic=self.characteristic)
        else:
            log.info(f"  Decomposing without characteristic")
            scene.input.decompose()

        self.cache: Cache = ({uuid.uuid4(): [scene.input.rep]}, {})
        self.root.propagate(*self.cache)
        return self.cache[0][self.terminus.uid][0]


# def subdivide_groups(selection: LinkGroup) -> list[LinkGroup]:
#     if not all([len(group) >= 2 for group in selection]):
#         log.info("Insufficient group sizes to subdivide selection")
#         return []
#     if len(set([len(group) for group in selection])) != 1:
#         log.info("Different group sizes in selection, won't subdivide")
#         return []

#     # Begin with a single element per group, nucleated from the first group
#     new_selections: list[LinkGroup] = [[[delta]] for delta in selection[0]]
#     for src_group in selection[1:]:
#         # TODO Try greedily minimizing distance from obj to target group for now
#         for delta in src_group:
#             best_dist = 1000
#             chosen = 0
#             for idx, target in enumerate(new_selections):
#                 dist = sum(
#                     [
#                         Inventory.invert(delta.left, tgt_delta.left).dist
#                         for group in target
#                         for tgt_delta in group
#                     ]
#                 )
#                 if dist < best_dist:
#                     best_dist = dist
#                     chosen = idx
#             new_selections[chosen].append([delta])

#     return new_selections
