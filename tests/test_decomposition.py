import pytest
from arc import ARC


@pytest.fixture(scope="module")
def decomposition_samples() -> ARC:
    return ARC(idxs={8, 10, 16, 17, 30})


# NOTE: This test is a little ambiguous, as the red object
# might reasonably be a rectangle missing 2 points, or a line trace.
def test_8(decomposition_samples: ARC):
    board = decomposition_samples.tasks[8].cases[0].input
    board.decompose()
    child_names = sorted([kid.id for kid in board.rep.children])
    assert child_names == [
        "Cluster(2x4)@(2, 0, 2)",
        "Rect(14x9)@(0, 0, 0)",
        "Rect(2x2)@(10, 3, 8)",
    ]


def test_10(decomposition_samples: ARC):
    board = decomposition_samples.tasks[10].cases[0].input
    board.decompose()
    child_names = sorted([kid.id for kid in board.rep.children])
    assert child_names == [
        "Line(3x1)@(6, 7, 5)",
        "Line(6x1)@(3, 3, 5)",
        "Line(8x1)@(1, 1, 5)",
        "Line(9x1)@(0, 5, 5)",
        "Rect(9x9)@(0, 0, 0)",
    ]


def test_16(decomposition_samples: ARC):
    board = decomposition_samples.tasks[16].cases[0].input
    board.decompose()
    child_names = sorted([kid.id for kid in board.rep.children])
    assert child_names == ["Cell(1x3)@(0, 0, 10)"]
    grandchild_names = sorted([kid.id for kid in board.rep.children[0]])
    assert grandchild_names == [
        "Dot@(0, 0, 3)",
        "Dot@(0, 1, 1)",
        "Dot@(0, 2, 2)",
    ]

    hier_repr = str(board).replace(" ", "").split("\n")
    assert hier_repr == [
        "[Tile]Pattern(3x3)@(0,0,10)(1ch,9pts,15p)",
        "Generating(V:2)",
        "[Cell]Cell(1x3)@(0,0,10)(3ch,3pts,10p)",
        "Dot@(0,0,3)",
        "Dot@(0,1,1)",
        "Dot@(0,2,2)",
    ]

    # Repeating call with an empty processing queue should do nothing
    board.decompose()
    child_names = sorted([kid.id for kid in board.rep.children])
    assert child_names == ["Cell(1x3)@(0, 0, 10)"]
    grandchild_names = sorted([kid.id for kid in board.rep.children[0]])
    assert grandchild_names == [
        "Dot@(0, 0, 3)",
        "Dot@(0, 1, 1)",
        "Dot@(0, 2, 2)",
    ]

    # Initializing and allowing no processes should leave the board in raw state
    board.decompose(characteristic="", init=True)
    assert board.current == ""
    assert board.proc_q == [""]

    # Only allowing Processes.Background gives a different result
    board.decompose(characteristic="B", init=True)
    child_names = sorted([kid.id for kid in board.rep.children])
    assert child_names == [
        "Line(3x1)@(0, 1, 1)",
        "Rect(3x2)@(0, 1, 2)",
        "Rect(3x3)@(0, 0, 3)",
    ]


def test_17(decomposition_samples: ARC):
    board = decomposition_samples.tasks[17].cases[0].input
    board.decompose(max_iter=3)
    child_names = sorted([kid.id for kid in board.rep.children])
    assert child_names == [
        "Cluster(15x17)@(4, 3, 0)",
        "Pattern(21x21)@(0, 0, 10)",
    ]


def test_30(decomposition_samples: ARC):
    board = decomposition_samples.tasks[30].cases[0].input
    board.decompose()
    child_names = sorted([kid.id for kid in board.rep.children])
    assert child_names == [
        "Rect(2x2)@(0, 1, 2)",
        "Rect(2x2)@(1, 7, 1)",
        "Rect(2x2)@(2, 4, 4)",
        "Rect(5x10)@(0, 0, 0)",
    ]
