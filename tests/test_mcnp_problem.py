from unittest import TestCase

import montepy

from montepy.mcnp_problem import MCNP_Problem


class testMCNP_problem(TestCase):
    def test_problem_init(self):
        problem = MCNP_Problem("tests/inputs/test.imcnp")
        self.assertEqual(problem.input_file, "tests/inputs/test.imcnp")
        self.assertEqual(problem.mcnp_version, (6, 2, 0))

    def test_problem_str(self):
        file_name = "tests/inputs/test.imcnp"
        problem = MCNP_Problem(file_name)
        self.assertTrue(f"MCNP problem for: {file_name}" in str(problem))
