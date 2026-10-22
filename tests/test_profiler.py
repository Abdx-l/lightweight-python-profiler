import unittest
from profiler import Profiler, folded, svg


def add_one(x):
    return x + 1


class ProfileTests(unittest.TestCase):
    def test_capture_and_restore_hook(self):
        import sys
        before = sys.getprofile()
        p = Profiler()
        self.assertEqual(p.run(add_one, 4), 5)
        self.assertIs(sys.getprofile(), before)
        self.assertTrue(any("add_one" in k for k in p.stacks))

    def test_render_escapes_labels(self):
        self.assertEqual(folded({"root;child": 3}), "root;child 3\n")
        self.assertIn("&lt;bad&gt;", svg({"root;<bad>": 3}))

