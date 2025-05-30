# Copyright 2024-2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of NVIDIA CORPORATION nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from argparse import Namespace

import genai_perf.export_data.data_exporter_factory as factory
from genai_perf.config.input.config_command import ConfigCommand
from genai_perf.export_data.console_exporter import ConsoleExporter
from genai_perf.export_data.csv_exporter import CsvExporter
from genai_perf.export_data.exporter_config import ExporterConfig
from genai_perf.export_data.json_exporter import JsonExporter
from genai_perf.inputs.input_constants import ModelSelectionStrategy, Subcommand
from genai_perf.subcommand.common import get_extra_inputs_as_dict
from tests.test_utils import create_default_exporter_config


class TestOutputReporter:
    stats = {
        "request_latency": {
            "unit": "ms",
            "avg": 1,
            "p99": 2,
            "p95": 3,
            "p90": 4,
            "p75": 5,
            "p50": 6,
            "p25": 7,
            "max": 8,
            "min": 9,
            "std": 0,
        },
    }
    config = ConfigCommand({"model_name": "gpt2_vllm"})
    config.endpoint.model_selection_strategy = ModelSelectionStrategy.ROUND_ROBIN
    config.subcommand = Subcommand.PROFILE

    exporter_config = create_default_exporter_config(
        stats=stats,
        config=config,
    )
    f = factory.DataExporterFactory()

    def test_return_json_exporter(self) -> None:
        exporter_list = self.f.create_data_exporters(self.exporter_config)
        assert any(isinstance(exporter, JsonExporter) for exporter in exporter_list)

    def test_return_csv_exporter(self) -> None:
        exporter_list = self.f.create_data_exporters(self.exporter_config)
        assert any(isinstance(exporter, CsvExporter) for exporter in exporter_list)

    def test_return_console_exporter(self) -> None:
        exporter_list = self.f.create_data_exporters(self.exporter_config)
        assert any(isinstance(exporter, ConsoleExporter) for exporter in exporter_list)
