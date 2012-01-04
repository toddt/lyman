from argparse import Namespace
from nipype.testing import assert_equal, assert_true

from nipype.pipeline.engine import Workflow, Node, MapNode
from nipype.interfaces.utility import IdentityInterface
from nipype.interfaces.io import DataGrabber

from .. import main


def make_simple_workflow():

    wf = Workflow(name="test")

    node1 = Node(IdentityInterface(fields=["foo"]), name="node1")
    node2 = MapNode(IdentityInterface(fields=["foo"]),
                    name="node2", iterfield=["foo"])
    node3 = Node(IdentityInterface(fields=["foo"]), name="node3")

    wf.connect([
        (node1, node2, [("foo", "foo")]),
        (node2, node3, [("foo", "foo")]),
        ])

    return wf, node1, node2, node3


def test_input_wrapper():

    wf, node1, node2, node3 = make_simple_workflow()

    s_list = ['s1', 's2']
    s_node = main.make_subject_source(s_list)

    g_node = Node(DataGrabber(in_fields=["foo"],
                              out_fields=["bar"]),
                  name="g_node")

    iw = main.InputWrapper(wf, s_node, g_node, node1)

    yield assert_equal, iw.wf, wf
    yield assert_equal, iw.subj_node, s_node
    yield assert_equal, iw.grab_node, g_node
    yield assert_equal, iw.in_node, node1

    iw.connect_inputs()

    g = wf._graph
    yield assert_true, s_node in g.nodes()
    yield assert_true, g_node in g.nodes()
    yield assert_true, (s_node, g_node) in g.edges()


def test_make_subject_source():

    subj_list = ['s1', 's2', 's3']
    node = main.make_subject_source(subj_list)
    iterable_name, iterable_val = node.iterables
    yield assert_equal, iterable_name, "subject_id"
    yield assert_equal, iterable_val, subj_list


def test_find_mapnodes():

    wf = make_simple_workflow()[0]
    mapnodes = main.find_mapnodes(wf)
    yield assert_equal, mapnodes, ["node2"]


def test_find_nested_workflows():

    wf, node1, node2, node3 = make_simple_workflow()
    inner_wf = make_simple_workflow()[0]

    wf.connect(node3, "foo", inner_wf, "node1.foo"),

    workflows = main.find_nested_workflows(wf)

    yield assert_equal, workflows, [inner_wf]


def test_determine_engine():

    plugin_dict = dict(linear="Linear",
                       multiproc="MultiProc",
                       ipython="IPython",
                       torque="PBS")

    for arg, plugin_str in plugin_dict.items():
        args = Namespace(plugin=arg)
        if arg == "multiproc":
            args.nprocs = 4
        plugin, plugin_args = main.determine_engine(args)
        yield assert_equal, plugin, plugin_str

        if arg == "multiproc":
            yield assert_equal, plugin_args, dict(n_procs=4)


def test_find_contrast_number():

    contrasts = ["foo", "bar", "buz"]

    for i, contrast in enumerate(contrasts, 1):
        yield assert_equal, main.find_contrast_number(contrast, contrasts), i
