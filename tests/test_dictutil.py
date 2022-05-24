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

    result = dictutil.dict_val2set([{1: 2, 3: 4}, {1: 3}])
    assert result == {1: {2, 3}, 3: {4}}

    result = dictutil.dict_popset(result, [{1: 4, 1: 2}, {3: 4}])
    assert result == {1: {3}}
