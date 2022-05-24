from arc.generator import Generator
from arc.object import Object
from arc.template import Template


def test_dot_structure() -> None:
    dot_1 = Object(0, 0, 0)
    dot_2 = Object(1, 1, 1)
    template = Template.from_outputs([dot_1, dot_2])
    assert template.structure == {
        "children": [],
        "generator": tuple([]),
        "props": {
            "row": "?",
            "col": "?",
            "color": "?",
        },
    }
    assert template.variables == {tuple([]): {"row", "col", "color"}}

    dots_1 = [Object(i, 0, 1) for i in range(1, 6, 2)]
    ctr_1 = Object(children=dots_1)
    dots_2 = [Object(i, 0, 2) for i in range(1, 6, 2)]
    ctr_2 = Object(children=dots_2)

    template = Template.from_outputs([ctr_1, ctr_2])
    assert template.structure == {
        "children": [
            {
                "props": {"row": 1, "color": "?"},
                "children": [],
                "generator": tuple([]),
            },
            {
                "props": {"row": 3, "color": "?"},
                "children": [],
                "generator": tuple([]),
            },
            {
                "props": {"row": 5, "color": "?"},
                "children": [],
                "generator": tuple([]),
            },
        ],
        "generator": tuple([]),
        "props": {},
    }
    assert template.variables == {
        (0,): {"color"},
        (1,): {"color"},
        (2,): {"color"},
    }


def test_generator_structure() -> None:
    line_1 = Object(1, 1, 1, generator=Generator.from_codes(("R*5",)))
    line_2 = Object(2, 1, 1, generator=Generator.from_codes(("R*6",)))

    template = Template.from_outputs([line_1, line_2])
    assert template.structure == {
        "children": [],
        "generator": ("R*?",),
        "props": {"row": "?", "col": 1, "color": 1},
    }
    assert template.variables == {tuple([]): {(0,), "row"}}
