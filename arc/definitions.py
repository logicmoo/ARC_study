"""The set of global constants used in the codebase.

Most of these shouldn't change, but some of them dictate how certain
operations will perform (such as batch size during decomposition).
"""


class Constants:
    # Data loading
    N_TRAIN = 400
    FOLDER_TRAIN = "data/training"

    # Data specification
    N_COLORS = 11
    NULL_COLOR = 10
    MARKED_COLOR = -1
    MAX_ROWS = 30
    MAX_COLS = 30

    # Processing
    MAX_DIST = 10000
    BATCH = 10  # Number of decomposition candidates to keep in a round
    MAX_ITER = 10  # Maximum rounds of decomposition

    STEPS_BASE = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    STEPS_DIAG = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    ALL_STEPS = STEPS_BASE + STEPS_DIAG

    # Information
    DOT_PROPS = 1  # 'entropic weight' of a single point
    NON_DOT_PROPS = 2  # 'entropic weight' of a container object

    cname = {
        -1: "Trans",
        0: "Black",
        1: "Blue",
        2: "Red",
        3: "Green",
        4: "Yellow",
        5: "Gray",
        6: "Magenta",
        7: "Orange",
        8: "SkyBlue",
        9: "Brown",
        10: "Trans",
    }
