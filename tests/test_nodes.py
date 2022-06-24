from arc.actions import Actions
from arc.inventory import Inventory
from arc.node import Node
from arc.node_selection import Criterion, SelectionNode
from arc.node_transform import TransformNode
from arc.object import Object


def test_node_relations():
    node1 = Node()
    node2 = Node()
    node3 = Node()

    node1.adopt(node2)
    assert node1.name == "Node"
    assert node1.children == {node2}
    assert node2.parents == {node1}

    node1.adopt(node2)
    node1.disown(node2)
    assert not node1.children
    assert not node2.parents

    node1.adopt(node2)
    node1.adopt(node3)
    node2.adopt(node3)
    assert node1.level == 0
    assert node2.level == 1
    assert node3.level == 2
    node1.tree()


def test_selection():
    sel_node = SelectionNode([Criterion("color", {1})])
    objs = [Object(color=0), Object(color=1)]
    selected = sel_node.select(objs)
    assert selected == [objs[1]]


def test_selection_node_constructor():
    obj_groups = [
        [Object(color=0), Object(color=1)],
        [Object(color=0), Object(color=1)],
    ]
    selection = [[obj_groups[0][1]], [obj_groups[1][1]]]
    sel_node = SelectionNode.from_data(obj_groups, selection)
    assert sel_node.criteria == [Criterion("color", {1})]


def test_transform_node_constructor():
    link1 = Inventory.invert(Object(0, 0, 0), Object(1, 0, 0))
    link2 = Inventory.invert(Object(2, 0, 0), Object(3, 0, 0))
    link_group = [[link1], [link2]]
    trans_node1 = TransformNode.from_action(Actions.Translate, link_group)
    assert trans_node1
    assert trans_node1.arg_info == (1, 0)

    null_trans_node = TransformNode.from_action(Actions.Zero, link_group)
    assert not null_trans_node

    trans_node2 = TransformNode.from_action(Actions.Vertical, link_group)
    assert trans_node2
    assert trans_node2.arg_info == (1,)
    assert trans_node2 < trans_node1


def test_determine_mapping():
    link1 = Inventory.invert(Object(1, 0, 3), Object(2, 0, 3))
    link2 = Inventory.invert(Object(2, 0, 2), Object(4, 0, 2))
    link3 = Inventory.invert(Object(3, 0, 1), Object(6, 0, 1))
    link_group = [[link1], [link2], [link3]]
    trans_node1 = TransformNode.from_action(Actions.Vertical, link_group)
    assert trans_node1
    assert trans_node1.arg_info == (("color", {3: 1, 2: 2, 1: 3}),)
