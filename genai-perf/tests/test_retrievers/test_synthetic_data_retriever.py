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

from pathlib import Path
from unittest.mock import patch

import pytest
from genai_perf.config.input.config_command import ConfigCommand
from genai_perf.inputs.input_constants import DEFAULT_SYNTHETIC_FILENAME
from genai_perf.inputs.inputs_config import InputsConfig
from genai_perf.inputs.retrievers.synthetic_data_retriever import SyntheticDataRetriever
from genai_perf.tokenizer import get_empty_tokenizer

IMPORT_PREFIX = "genai_perf.inputs.retrievers.synthetic_data_retriever"


class TestSyntheticDataRetriever:

    @patch(
        f"{IMPORT_PREFIX}.SyntheticPromptGenerator.create_synthetic_prompt",
        return_value="test prompt",
    )
    @pytest.mark.parametrize(
        "batch_size_text, num_dataset_entries",
        [
            (1, 3),
            (2, 2),
        ],
    )
    def test_synthetic_default(self, mock_prompt, batch_size_text, num_dataset_entries):
        """
        Test default synthetic data generation where only text is generated.
        """
        config = ConfigCommand({"model_name": "test_model"})
        config.input.num_dataset_entries = num_dataset_entries
        config.input.batch_size = batch_size_text

        inputs_config = InputsConfig(
            config=config,
            tokenizer=get_empty_tokenizer(),
            output_directory=Path("output"),
        )
        synthetic_retriever = SyntheticDataRetriever(inputs_config)
        dataset = synthetic_retriever.retrieve_data()

        file_data = dataset.files_data[DEFAULT_SYNTHETIC_FILENAME]
        assert len(file_data.rows) == num_dataset_entries

        for row in file_data.rows:
            assert len(row.texts) == batch_size_text
            assert len(row.images) == 0  # No images should be generated
            assert len(row.audios) == 0  # No audio should be generated
            assert all(text == "test prompt" for text in row.texts)

    @patch(
        f"{IMPORT_PREFIX}.SyntheticPromptGenerator.create_synthetic_prompt",
        return_value="test prompt",
    )
    @patch(
        f"{IMPORT_PREFIX}.SyntheticImageGenerator.create_synthetic_image",
        return_value="data:image/jpeg;base64,test_base64_encoding",
    )
    @patch(
        f"{IMPORT_PREFIX}.SyntheticAudioGenerator.create_synthetic_audio",
        return_value="wav,test_base64_encoding",
    )
    @pytest.mark.parametrize(
        "num_dataset_entries, image_width_height, audio_length",
        [
            (200, 10, 10),  # Text and image
            (300, 0, 10),  # Text and audio
            (400, 10, 10),  # Text, image, and audio
        ],
    )
    def test_synthetic_multi_modal(
        self,
        mock_prompt,
        mock_image,
        mock_audio,
        num_dataset_entries,
        image_width_height,
        audio_length,
    ):
        """
        Test synthetic data generation where text, image, and audio are generated.
        Assume single batch size for all modalities.
        """
        config = ConfigCommand({"model_name": "test_model"})
        config.input.num_dataset_entries = num_dataset_entries
        # Set image and audio sizes to non-zero values
        # to ensure they are generated
        config.input.image.width.mean = image_width_height
        config.input.image.height.mean = image_width_height
        config.input.audio.length.mean = audio_length

        inputs_config = InputsConfig(
            config=config,
            tokenizer=get_empty_tokenizer(),
            output_directory=Path("output"),
        )
        synthetic_retriever = SyntheticDataRetriever(inputs_config)
        dataset = synthetic_retriever.retrieve_data()

        file_data = dataset.files_data[DEFAULT_SYNTHETIC_FILENAME]
        assert len(file_data.rows) == num_dataset_entries

        for row in file_data.rows:
            assert len(row.texts) == 1
            assert row.texts[0] == "test prompt"

            if synthetic_retriever._include_image:
                assert len(row.images) == 1
                assert row.images[0] == "data:image/jpeg;base64,test_base64_encoding"
            if synthetic_retriever._include_audio:
                assert len(row.audios) == 1
                assert row.audios[0] == "wav,test_base64_encoding"

    @patch(
        f"{IMPORT_PREFIX}.SyntheticPromptGenerator.create_synthetic_prompt",
        return_value="test prompt",
    )
    @patch(
        f"{IMPORT_PREFIX}.SyntheticImageGenerator.create_synthetic_image",
        return_value="data:image/jpeg;base64,test_base64_encoding",
    )
    @patch(
        f"{IMPORT_PREFIX}.SyntheticAudioGenerator.create_synthetic_audio",
        return_value="wav,test_base64_encoding",
    )
    @pytest.mark.parametrize(
        "batch_size_text, batch_size_image, batch_size_audio, num_dataset_entries",
        [
            (1, 1, 1, 3),  # All single batch size
            (2, 1, 1, 2),  # Text batch size >1
            (1, 2, 1, 3),  # Image batch size >1
            (1, 1, 2, 4),  # Audio batch size >1
            (3, 2, 1, 5),  # Text and image batch size >1
            (3, 1, 2, 6),  # Text and audio batch size >1
            (1, 2, 3, 7),  # Image and audio batch size >1
            (3, 3, 3, 8),  # Text, image, and audio batch size >1
        ],
    )
    def test_synthetic_batched_multi_modal(
        self,
        mock_prompt,
        mock_image,
        mock_audio,
        batch_size_text,
        batch_size_image,
        batch_size_audio,
        num_dataset_entries,
    ):
        """
        Test synthetic data generation when both text and image are generated.
        Assume different batch sizes for text and image.
        """
        config = ConfigCommand({"model_name": "test_model"})
        config.input.num_dataset_entries = num_dataset_entries
        config.input.batch_size = batch_size_text
        config.input.image.batch_size = batch_size_image
        config.input.audio.batch_size = batch_size_audio
        # Set image and audio sizes to non-zero values
        # to ensure they are generated
        config.input.image.width.mean = 10
        config.input.image.height.mean = 10
        config.input.audio.length.mean = 5

        inputs_config = InputsConfig(
            config=config,
            tokenizer=get_empty_tokenizer(),
            output_directory=Path("output"),
        )
        synthetic_retriever = SyntheticDataRetriever(inputs_config)
        dataset = synthetic_retriever.retrieve_data()

        file_data = dataset.files_data[DEFAULT_SYNTHETIC_FILENAME]
        assert len(file_data.rows) == num_dataset_entries

        for row in file_data.rows:
            assert len(row.texts) == batch_size_text
            assert len(row.images) == batch_size_image
            assert len(row.audios) == batch_size_audio
            assert all(text == "test prompt" for text in row.texts)
            assert all(
                image == "data:image/jpeg;base64,test_base64_encoding"
                for image in row.images
            )
            assert all(audio == "wav,test_base64_encoding" for audio in row.audios)

    @patch(
        f"{IMPORT_PREFIX}.SyntheticPromptGenerator.create_synthetic_prompt",
        return_value="test prompt",
    )
    @pytest.mark.parametrize(
        "input_filenames, num_dataset_entries",
        [
            (["file1.jsonl"], 2),
            (["file1.jsonl", "file2.jsonl"], 4),
        ],
    )
    def test_synthetic_multiple_files(
        self, mock_prompt, input_filenames, num_dataset_entries
    ):
        """
        Test synthetic data generation when multiple synthetic files are specified.
        """
        config = ConfigCommand({"model_name": "test_model"})
        config.input.num_dataset_entries = num_dataset_entries
        config.input.synthetic_files = input_filenames

        inputs_config = InputsConfig(
            config=config,
            tokenizer=get_empty_tokenizer(),
            output_directory=Path("output"),
        )
        synthetic_retriever = SyntheticDataRetriever(inputs_config)
        dataset = synthetic_retriever.retrieve_data()

        assert len(dataset.files_data) == len(input_filenames)
        for filename in input_filenames:
            assert filename in dataset.files_data

        for file_data in dataset.files_data.values():
            assert len(file_data.rows) == num_dataset_entries

            for row in file_data.rows:
                assert len(row.texts) == 1
                assert len(row.images) == 0  # No images should be generated
                assert len(row.audios) == 0  # No audio should be generated
                assert row.texts[0] == "test prompt"

    @patch(
        f"{IMPORT_PREFIX}.SyntheticPromptGenerator.create_synthetic_prompt",
        return_value="test prompt",
    )
    @patch(f"{IMPORT_PREFIX}.SyntheticPromptGenerator.create_prefix_prompts_pool")
    @patch(
        f"{IMPORT_PREFIX}.SyntheticPromptGenerator.get_random_prefix_prompt",
        return_value="prompt prefix",
    )
    @pytest.mark.parametrize(
        "num_prefix_prompts, prefix_prompt_length, num_dataset_entries",
        [
            (1, 123, 20),
            (5, 456, 30),
        ],
    )
    def test_synthetic_with_prefix_prompts(
        self,
        mock_random_prefix_prompt,
        mock_create_prefix_prompts_pool,
        mock_create_synthetic_prompt,
        num_prefix_prompts,
        prefix_prompt_length,
        num_dataset_entries,
    ):
        config = ConfigCommand({"model_name": "test_model"})
        config.input.num_dataset_entries = num_dataset_entries
        config.input.prefix_prompt.num = num_prefix_prompts
        config.input.prefix_prompt.length = prefix_prompt_length

        config = InputsConfig(
            config=config,
            tokenizer=get_empty_tokenizer(),
            output_directory=Path("output"),
        )

        synthetic_retriever = SyntheticDataRetriever(config)
        dataset = synthetic_retriever.retrieve_data()

        file_data = dataset.files_data[DEFAULT_SYNTHETIC_FILENAME]
        assert len(file_data.rows) == num_dataset_entries

        # Ensure the prompt prefix pool was created exactly once
        mock_create_prefix_prompts_pool.assert_called_once()

        # Validate that every text in the dataset has the right prefix
        for row_index, row in enumerate(file_data.rows):
            expected_prefix = "prompt prefix "
            for text_index, text in enumerate(row.texts):
                assert text.startswith(
                    expected_prefix
                ), f"Row {row_index}, text {text_index}: text does not start with '{expected_prefix}'. Actual: '{text}'"

    @patch(
        f"{IMPORT_PREFIX}.uuid.uuid4",
        side_effect=[
            f"session_{i}" for i in range(10)
        ],  # Generate predictable session IDs
    )
    @patch(
        f"{IMPORT_PREFIX}.SyntheticPromptGenerator.create_synthetic_prompt",
        return_value="test prompt",
    )
    @patch(f"{IMPORT_PREFIX}.SyntheticPromptGenerator.create_prefix_prompts_pool")
    @patch(
        f"{IMPORT_PREFIX}.SyntheticPromptGenerator.get_random_prefix_prompt",
        return_value="prompt prefix",
    )
    @pytest.mark.parametrize(
        "num_sessions, session_turns_mean, session_turns_stddev",
        [
            (2, 3, 0),  # 2 sessions, 3 turns each (no variance)
            # (3, 2, 1),  # 3 sessions, ~2 turns per session with variance
        ],
    )
    def test_synthetic_multi_turn_sessions_with_prefix_prompts(
        self,
        mock_random_prefix_prompt,
        mock_create_prefix_prompts_pool,
        mock_create_synthetic_prompt,
        mock_uuid,
        num_sessions,
        session_turns_mean,
        session_turns_stddev,
    ):
        session_turn_delay_ms = 50

        config = ConfigCommand({"model_name": "test_model"})
        config.input.prefix_prompt.num = 3
        config.input.prefix_prompt.length = 20
        config.input.sessions.num = num_sessions
        config.input.sessions.turn_delay.mean = session_turn_delay_ms
        config.input.sessions.turn_delay.stddev = 0
        config.input.sessions.turns.mean = session_turns_mean
        config.input.sessions.turns.stddev = session_turns_stddev

        config = InputsConfig(
            config=config,
            tokenizer=get_empty_tokenizer(),
            output_directory=Path("output"),
        )
        synthetic_retriever = SyntheticDataRetriever(config)
        dataset = synthetic_retriever.retrieve_data()

        assert len(dataset.files_data[DEFAULT_SYNTHETIC_FILENAME].rows) > num_sessions

        sessions = {}
        for row in dataset.files_data[DEFAULT_SYNTHETIC_FILENAME].rows:
            session_id = row.payload_metadata.get("session_id")
            assert (
                session_id is not None
            ), "Session ID should be assigned to each multi-turn entry."

            if session_id not in sessions:
                sessions[session_id] = []

            sessions[session_id].append(row)

        for session_id, session_turns in sessions.items():
            assert (
                len(session_turns) >= 1
            ), f"Session {session_id} should have at least one turn."

            for i, turn in enumerate(session_turns):
                assert (
                    len(turn.texts) > 0
                ), f"Session {session_id}, turn {i} should have at least one text."
                expected_prefix = (
                    "prompt prefix " if i == 0 else ""
                )  # Only first turn gets prefix

                for text_index, text in enumerate(turn.texts):
                    assert text.startswith(expected_prefix), (
                        f"Session {session_id}, turn {i}, text {text_index} "
                        f"does not start with expected prefix '{expected_prefix}'. Got: '{text}'"
                    )

                # All turns except the last should have a delay
                if i < len(session_turns) - 1:
                    assert turn.payload_metadata, (
                        f"Session {session_id}, turn {i} should have payload "
                        f"metadata."
                    )
                    assert (
                        "delay" in turn.payload_metadata
                    ), f"Session {session_id}, turn {i} should have a delay."
                    assert turn.payload_metadata["delay"] == session_turn_delay_ms, (
                        f"Session {session_id}, turn {i} should have a delay of "
                        "{session_turn_delay_ms} ms."
                    )

        mock_create_prefix_prompts_pool.assert_called_once()
