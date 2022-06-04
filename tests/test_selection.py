from arc.labeler import Labeler
from arc.generator import Generator
from arc.object import Object


def test_labeling():
    dot1 = Object(1, 1, 1)
    dot2 = Object(2, 2, 2)
    line_l4 = Object(generator=Generator.from_codes(("V*3",)))
    line_l5 = Object(generator=Generator.from_codes(("V*4",)))

    obj_groups = [[dot1, dot2], [line_l4, line_l5]]
    labels = Labeler(obj_groups).labels
    assert labels[dot1.uid]["category"] == "Dot"
    assert labels[line_l5.uid]["category"] == "Line"

    assert labels[line_l5.uid]["size-rank"] == 1
    assert labels[line_l4.uid]["size-rank"] == 2
    assert labels[dot1.uid]["size-rank"] == None
    assert labels[dot2.uid]["size-rank"] == None
