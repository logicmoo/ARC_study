from arc.viz import Layout, PlotDef
from arc.object import Object, ObjectDelta
from arc.scene import Scene
from arc.task import Task


def tree_layout(obj: Object) -> Layout:
    objs = [obj]
    layout: Layout = []
    while objs:
        layout.append([{"grid": obj.grid, "name": obj._id} for obj in objs])
        objs = [
            kid for obj in objs for kid in obj.children if not kid.category == "Dot"
        ]
    return layout


def task_layout(task: Task, **kwargs) -> Layout:
    layout: Layout = [[], []]
    for scene_idx, scene in enumerate(task.cases):
        layout[0].append(
            {"grid": scene.input.rep.grid, "name": f"Case {scene_idx}: Input"}
        )
        layout[1].append(
            {"grid": scene.output.rep.grid, "name": f"Case {scene_idx}: Output"}
        )
    for scene_idx, scene in enumerate(task.tests):
        layout[0].append(
            {"grid": scene.input.rep.grid, "name": f"Test {scene_idx}: Input"}
        )
        layout[1].append(
            {"grid": scene.output.rep.grid, "name": f"Test {scene_idx}: Output"}
        )
    return layout


def scene_layout(scene: Scene) -> Layout:
    inp_obj, out_obj = scene.input.rep, scene.output.rep
    left: PlotDef = {"grid": inp_obj.grid, "name": "Input"}
    right: PlotDef = {"grid": out_obj.grid, "name": "Output"}
    return [[left, right]]


def match_layout(scene: Scene) -> Layout:
    layout: Layout = []
    for delta in scene._path:
        inp, out, trans = delta.right, delta.left, delta.transform
        left: PlotDef = {"grid": inp.grid, "name": inp.category}
        right: PlotDef = {"grid": out.grid, "name": str(trans.items())}
        layout.append([left, right])
    return layout
