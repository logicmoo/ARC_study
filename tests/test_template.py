from arc.generator import Generator
from arc.object import Object, ObjectPath
from arc.template import Template


def test_dot_structure() -> None:
    dot_1 = Object(0, 0, 0)
    dot_2 = Object(1, 1, 1)
    template = Template.from_outputs([dot_1, dot_2])
    assert template.structure == {
        "children": [],
        "props": {
            "row": "?",
            "col": "?",
            "color": "?",
        },
    }
    assert template.variables == {
        ObjectPath(property="col"),
        ObjectPath(property="color"),
        ObjectPath(property="row"),
    }

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
            },
            {
                "props": {"row": 3, "color": "?"},
                "children": [],
            },
            {
                "props": {"row": 5, "color": "?"},
                "children": [],
            },
        ],
        "props": {},
    }
    assert template.variables == {
        ObjectPath((0,), "color"),
        ObjectPath((1,), "color"),
        ObjectPath((2,), "color"),
    }


def test_generator_structure() -> None:
    line_1 = Object(1, 1, 1, generator=Generator.from_codes(("V*5",)))
    line_2 = Object(2, 1, 1, generator=Generator.from_codes(("V*6",)))

    template = Template.from_outputs([line_1, line_2])
    assert template.structure == {
        "children": [],
        "props": {"row": "?", "col": 1, "color": 1, "V": "?"},
    }
    assert template.variables == {ObjectPath(property="V"), ObjectPath(property="row")}
