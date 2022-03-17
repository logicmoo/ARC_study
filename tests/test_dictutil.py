from arc.util import dictutil


def test_dict_logic():
    left_dict = {1: 2, "a": "b", (1, 2): [3, 4, 5]}
    right_dict = {1: None, "b": "b", (1, 2): [3, 4, 5]}
    result = dictutil.dict_and(left_dict, right_dict)
    assert result == {(1, 2): [3, 4, 5]}

    result = dictutil.dict_and_group([left_dict, right_dict, {}])
    assert result == {}

    result = dictutil.dict_xor(left_dict, right_dict)
    assert result == {1: 2, "a": "b", "b": "b"}
