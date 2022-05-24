"""The set of global constants used in the codebase.

Most of these shouldn't change, but some of them dictate how certain
operations will perform (such as batch size during decomposition).
"""


class Constants:
    # Data loading
    N_TRAIN = 400
    FOLDER_TRAIN = "data/training"
    FOLDER_EVAL = "data/evaluation"

    # Data specification
    N_COLORS = 12
    NULL_COLOR = 10  # Default color and treated as transparent
    NEGATIVE_COLOR = 11  # 'Cuts out' the point from the parent
    MARKED_COLOR = -2  # Used for grid methods, such as flood fill
    MAX_ROWS = 30
    MAX_COLS = 30

    DEFAULT_ROW = 0
    DEFAULT_COL = 0
    DEFAULT_COLOR = NULL_COLOR

    # Processing
    MAX_DIST = 10000
    MAX_BLOBS = 10
    CHILD_DIST = 2  # TODO: Additional measure of distance when comparing children?
    DEFAULT_MAX_ITER = 100  # Default maximum rounds of decomposition

    STEPS_BASE: list[tuple[int, int]] = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    STEPS_DIAG: list[tuple[int, int]] = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    ALL_STEPS = STEPS_BASE + STEPS_DIAG

    # Information
    DOT_PROPS = 1  # 'entropic weight' of a single point
    NON_DOT_PROPS = 2  # 'entropic weight' of a container object
    CUTOUT_PROPS = 5

    cname = {
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
        11: "Cutout",
    }

    # Set of tasks that engage in significant compute at present, and are not
    # under consideration for finding a solution. We filter these out to
    # save time on larger runs.
    blacklist = {
        54,
        74,
        77,
        80,
        110,
        118,
        162,
        165,
        175,
        205,
        208,
        243,
        255,
        265,
        303,
    }
