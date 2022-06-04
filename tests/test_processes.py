from arc.grid_methods import grid_equal, gridify
from arc.object import Object
from arc.processes import Reflection, Rotation


def test_reflection_even():
    input_grid = [
        [1, 2, 2, 1],
        [3, 4, 4, 3],
        [3, 4, 4, 3],
        [1, 2, 2, 1],
    ]

    object = Object.from_grid(input_grid)
    result = Reflection().run(object)
    true_grid = gridify([[1, 2], [3, 4]])
    assert result is not None
    assert grid_equal(result.children[0].grid, true_grid)
    assert result.generator.codes == ("M*1", "E*1")


def test_reflection_odd():
    input_grid = [
        [1, 2, 1],
        [3, 4, 3],
        [1, 2, 1],
    ]

    object = Object.from_grid(input_grid)
    result = Reflection().run(object)
    true_grid = gridify([[1, 2], [3, 4]])
    assert result is not None
    assert grid_equal(result.children[0].grid, true_grid)
    assert result.generator.codes == ("m*1", "e*1")


def test_rotation():
    input_grid = [
        [1, 2, 3, 1],
        [3, 4, 4, 2],
        [2, 4, 4, 3],
        [1, 3, 2, 1],
    ]

    object = Object.from_grid(input_grid)
    result = Rotation().run(object)
    true_grid = gridify([[1, 2], [3, 4]])
    assert result is not None
    assert grid_equal(result.children[0].grid, true_grid)
    assert result.generator.codes == ("O*3",)


if __name__ == "__main__":
    test_reflection_even()
    test_reflection_odd()
