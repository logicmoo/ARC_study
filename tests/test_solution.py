from arc.actions import Actions
from arc.node import VarNode
from arc.node_selection import Criterion, SelectionNode
from arc.node_transform import TransformNode
from arc.scene import Scene
from arc.solution import Solution
from arc.template import Template
from arc.types import SceneData


def test_simple_transform_task():
    # Translate one Dot (color is 1 or 2) down on black 3x3
    data0: SceneData = {
        "input": [[1, 0, 0], [0, 0, 0], [0, 0, 0]],
        "output": [[0, 0, 0], [1, 0, 0], [0, 0, 0]],
    }
    data1: SceneData = {
        "input": [[0, 2, 0], [0, 0, 0], [0, 0, 0]],
        "output": [[0, 0, 0], [0, 2, 0], [0, 0, 0]],
    }
    cases = [Scene(data0, 0), Scene(data1, 1)]

    cases[0].decompose()
    cases[1].decompose()
    assert cases[0].props == 25
    assert cases[1].props == 27

    template = Template.from_outputs([cases[0].output.rep, cases[1].output.rep])
    cases[0].link("B", template.variables)
    cases[1].link("B", template.variables)
    assert cases[0].dist == 3
    assert cases[1].dist == 3

    solution = Solution(characteristic="B", attention=1, template=template)
    solution.bundle(cases)
    solution.create_nodes(cases)

    # We expect 1 SelectionNode
    assert len(solution.root.children) == 1
    child = solution.root[0]
    assert isinstance(child, SelectionNode)
    assert child.criteria == [Criterion("category", {"Dot"})]
    assert len(child.children) == 1
    grandchild = child[0]
    assert isinstance(grandchild, TransformNode)
    assert grandchild.action == Actions.Vertical
    assert grandchild.arg_info == (1,)

    # Test case: a dot with different color and initial position
    data2: SceneData = {
        "input": [[0, 0, 0], [0, 3, 0], [0, 0, 0]],
        "output": [[0, 0, 0], [0, 0, 0], [0, 3, 0]],
    }
    test = Scene(data2, 0)
    gen_result = solution.generate(test)
    assert gen_result == test.output.rep


def test_simple_variable_task():
    # Color the output based on input dot color
    data0: SceneData = {
        "input": [[1, 2, 2, 2]],
        "output": [[1, 1], [1, 1]],
    }
    data1: SceneData = {
        "input": [[4, 3, 3, 3]],
        "output": [[4, 4], [4, 4]],
    }
    cases = [Scene(data0, 0), Scene(data1, 1)]

    cases[0].decompose()
    cases[1].decompose()
    # Realistically, these decompositions shouldn't involve a match, but it ends up
    # being rather easy to scale + paint between a variety of objects.
    assert cases[0].props == 11
    assert cases[1].props == 11

    template = Template.from_outputs([cases[0].output.rep, cases[1].output.rep])
    cases[0].link("I", template.variables)
    cases[1].link("I", template.variables)
    # Should be a single variable link each
    assert cases[0].dist == 2
    assert cases[1].dist == 2

    solution = Solution(characteristic="B", attention=1, template=template)
    solution.bundle(cases)
    solution.create_nodes(cases)

    # We expect 1 SelectionNode
    assert len(solution.root.children) == 1
    child = solution.root[0]
    assert isinstance(child, SelectionNode)
    assert child.criteria == [Criterion("category", {"Dot"})]
    assert len(child.children) == 1
    grandchild = child[0]
    assert isinstance(grandchild, VarNode)
    assert grandchild.property == "color"

    # Test case: a dot with different color and initial position
    data2: SceneData = {
        "input": [[6, 1, 1, 1]],
        "output": [[6, 6], [6, 6]],
    }
    test = Scene(data2, 0)
    gen_result = solution.generate(test)
    assert gen_result == test.output.rep
