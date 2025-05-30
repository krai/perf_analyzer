# Copyright 2024-2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import unittest
from unittest.mock import patch

from genai_perf.checkpoint.checkpoint import Checkpoint
from genai_perf.config.generate.search_parameters import SearchParameters
from genai_perf.config.generate.sweep_objective_generator import SweepObjectiveGenerator
from genai_perf.config.input.config_command import ConfigCommand
from genai_perf.config.run.results import Results
from tests.test_utils import create_run_config


class TestCheckpoint(unittest.TestCase):
    ###########################################################################
    # Setup & Teardown
    ###########################################################################
    def setUp(self):
        self._config = ConfigCommand(user_config={"model_name": "test_model"})
        self._model_search_parameters = {
            "test_model": SearchParameters(config=self._config)
        }

        self._sweep_obj_gen = SweepObjectiveGenerator(
            self._config, self._model_search_parameters
        )

        self._results = Results()
        for count, objective in enumerate(self._sweep_obj_gen.get_objectives()):
            run_config_name = "test_model_run_config_" + str(count)
            run_config = create_run_config(
                run_config_name=run_config_name,
                model_objective_parameters=objective,
                model_name="test_model",
                gpu_power=500 + 10 * count,
                gpu_utilization=50 - count,
                throughput=300 - 10 * count,
                latency=100 - 5 * count,
                input_seq_length=20 + 10 * count,
                output_seq_length=50 + 5 * count,
            )
            self._results.add_run_config(run_config)

        config = ConfigCommand(user_config={"model_name": "test_model"})

        self._checkpoint = Checkpoint(config=config, results=self._results)

    def tearDown(self):
        patch.stopall()

    # TODO: TPA-501: Add mock file I/O and check for empty directory and improperly
    # formatted checkpoint files

    ###########################################################################
    # Checkpoint Tests
    ###########################################################################
    def test_checkpoint_methods(self):
        """
        Checks to ensure checkpoint methods work as intended
        """

        self._checkpoint.create_checkpoint_object()
        self._checkpoint._create_class_from_checkpoint()
        os.remove(self._checkpoint._create_checkpoint_file_path())

        self.assertEqual(self._results, self._checkpoint.results)


if __name__ == "__main__":
    unittest.main()
