from arc.object import Object
from arc.generator import Generator

# def test_props():
#     background = Object(0, 0, 0, gens=["R9", "C9"], name="BG")
#     rectangle = Object(0, 0, 1, gens=["R4", "C9"], name="Rect")
#     square = Object(gens=["R4", "C4"], name="Square")
#     stripes = Object(0, 0, 1, gens=["RR4", "C9"], name="Lines")
#     squares = Object(0, 0, 1, children=[square], gens=["RC1"])
#     checkers = Object(0, 0, 1, gens=["rr4", "dd4", "rd1"])
#     board1 = Object(children=[background], name="blank")
#     board2 = Object(children=[background, rectangle], name="Split")
#     board3 = Object(children=[background, stripes], name="Stripes")
#     board4 = Object(children=[background, checkers], name="Checkers")
#     board5 = Object(children=[background, squares], name="Squares")
#     boards = [board1, board2, board3, board4, board5]
#     assert boards == sorted(boards, key=lambda x: x.props)
#     return boards
