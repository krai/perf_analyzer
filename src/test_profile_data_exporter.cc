// Copyright 2023-2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions
// are met:
//  * Redistributions of source code must retain the above copyright
//    notice, this list of conditions and the following disclaimer.
//  * Redistributions in binary form must reproduce the above copyright
//    notice, this list of conditions and the following disclaimer in the
//    documentation and/or other materials provided with the distribution.
//  * Neither the name of NVIDIA CORPORATION nor the names of its
//    contributors may be used to endorse or promote products derived
//    from this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS"" AND ANY
// EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
// PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
// CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
// EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
// PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
// PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
// OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#include <rapidjson/document.h>

#include "doctest.h"
#include "mock_profile_data_exporter.h"
#include "profile_data_exporter.h"

namespace triton { namespace perfanalyzer {

TEST_CASE("profile_data_exporter: ConvertToJson")
{
  using std::chrono::nanoseconds;
  using std::chrono::system_clock;
  using std::chrono::time_point;

  MockProfileDataExporter exporter{};

  ProfileDataCollector::InferenceLoadMode infer_mode{4, 0.0};
  uint64_t sequence_id{1};

  auto clock_epoch{time_point<system_clock>()};
  auto request_timestamp{clock_epoch + nanoseconds(1)};
  auto response_timestamp1{clock_epoch + nanoseconds(2)};
  auto response_timestamp2{clock_epoch + nanoseconds(3)};

  // Request inputs
  const std::string in_buf1{"abc123"};
  const int32_t in_buf2{456};
  const bool in_buf3{true};
  const std::string in_buf4{"{\"abc\":\"def\"}"};

  RequestRecord::RequestInput request_input;
  request_input.insert(
      {"in_key1",
       RecordData(
           std::vector<uint8_t>(in_buf1.begin(), in_buf1.end()), "BYTES")});
  request_input.insert(
      {"in_key2",
       RecordData(
           std::vector<uint8_t>(
               reinterpret_cast<const uint8_t*>(&in_buf2),
               reinterpret_cast<const uint8_t*>(&in_buf2) + sizeof(in_buf2)),
           "INT32")});
  request_input.insert(
      {"in_key3",
       RecordData(
           std::vector<uint8_t>(
               reinterpret_cast<const uint8_t*>(&in_buf3),
               reinterpret_cast<const uint8_t*>(&in_buf3) + sizeof(in_buf3)),
           "BOOL")});
  request_input.insert(
      {"in_key4",
       RecordData(
           std::vector<uint8_t>(in_buf4.begin(), in_buf4.end()), "JSON")});

  // Response outputs
  std::vector<std::string> out_bufs{"abc", "def", "ghi", "jkl"};

  RequestRecord::ResponseOutput response_output1;
  response_output1.insert(
      {"out_key1",
       RecordData(
           std::vector<uint8_t>(out_bufs[0].begin(), out_bufs[0].end()),
           "BYTES")});
  response_output1.insert(
      {"out_key2",
       RecordData(
           std::vector<uint8_t>(out_bufs[1].begin(), out_bufs[1].end()),
           "BYTES")});

  RequestRecord::ResponseOutput response_output2;
  response_output2.insert(
      {"out_key3",
       RecordData(
           std::vector<uint8_t>(out_bufs[2].begin(), out_bufs[2].end()),
           "BYTES")});
  response_output2.insert(
      {"out_key4",
       RecordData(
           std::vector<uint8_t>(out_bufs[3].begin(), out_bufs[3].end()),
           "BYTES")});

  RequestRecord request_record{
      request_timestamp,
      std::vector<time_point<system_clock>>{
          response_timestamp1, response_timestamp2},
      {request_input},
      {response_output1, response_output2},
      0,
      false,
      sequence_id,
      false};
  std::vector<RequestRecord> requests{request_record};
  std::vector<uint64_t> window_boundaries{1, 5, 6};

  ProfileDataCollector::Experiment experiment;
  experiment.mode = infer_mode;
  experiment.requests = requests;
  experiment.window_boundaries = window_boundaries;
  std::vector<ProfileDataCollector::Experiment> experiments{experiment};

  std::string version{"1.2.3"};
  cb::BackendKind service_kind = cb::BackendKind::TRITON;
  std::string endpoint{""};

  exporter.ConvertToJson(experiments, version, service_kind, endpoint);

  std::string json{R"(
      {
        "experiments" : [
          {
            "experiment" : {
              "mode" : "concurrency",
              "value" : 4
            },
            "requests" : [
              {
                "timestamp" : 1,
                "sequence_id" : 1,
                "request_inputs" : {"in_key1":"abc123","in_key2":456,"in_key3":true,"in_key4":"{\"abc\":\"def\"}"},
                "response_timestamps" : [ 2, 3 ],
                "response_outputs" : [ {"out_key1":"abc","out_key2":"def"}, {"out_key3":"ghi","out_key4":"jkl"} ]
              }
            ],
            "window_boundaries" : [ 1, 5, 6 ]
          }
        ],
        "version" : "1.2.3",
        "service_kind": "triton",
        "endpoint": ""
      }
      )"};


  rapidjson::Document expected_document;
  expected_document.Parse(json.c_str());

  // FIXME (TMA-1339): Look into the testing the order of things in the json
  const rapidjson::Value& expected_experiment{
      expected_document["experiments"][0]["experiment"]};
  const rapidjson::Value& expected_request{
      expected_document["experiments"][0]["requests"][0]};
  const rapidjson::Value& expected_windows{
      expected_document["experiments"][0]["window_boundaries"]};
  const rapidjson::Value& expected_version{expected_document["version"]};


  const rapidjson::Value& actual_experiment{
      exporter.document_["experiments"][0]["experiment"]};
  const rapidjson::Value& actual_request{
      exporter.document_["experiments"][0]["requests"][0]};
  const rapidjson::Value& actual_windows{
      exporter.document_["experiments"][0]["window_boundaries"]};
  const rapidjson::Value& actual_version{exporter.document_["version"]};

  CHECK(actual_experiment["mode"] == expected_experiment["mode"]);
  CHECK(actual_experiment["value"] == expected_experiment["value"]);

  CHECK(actual_request["timestamp"] == expected_request["timestamp"]);
  CHECK(actual_request["sequence_id"] == expected_request["sequence_id"]);


  CHECK(
      actual_request["request_inputs"]["in_key1"] ==
      expected_request["request_inputs"]["in_key1"]);
  CHECK(
      actual_request["request_inputs"]["in_key2"] ==
      expected_request["request_inputs"]["in_key2"]);
  CHECK(
      actual_request["request_inputs"]["in_key3"] ==
      expected_request["request_inputs"]["in_key3"]);
  auto act_inkey_4 = actual_request["request_inputs"]["in_key4"].GetString();
  auto exp_inkey_4 = expected_request["request_inputs"]["in_key4"].GetString();
  CHECK(std::string{act_inkey_4} == std::string{exp_inkey_4});

  CHECK(
      actual_request["response_timestamps"][0] ==
      expected_request["response_timestamps"][0]);
  CHECK(
      actual_request["response_timestamps"][1] ==
      expected_request["response_timestamps"][1]);
  CHECK(
      actual_request["response_outputs"][0] ==
      expected_request["response_outputs"][0]);
  CHECK(
      actual_request["response_outputs"][1] ==
      expected_request["response_outputs"][1]);

  CHECK(actual_windows[0] == expected_windows[0]);
  CHECK(actual_windows[1] == expected_windows[1]);
  CHECK(actual_windows[2] == expected_windows[2]);

  CHECK(actual_version == expected_version);
}

TEST_CASE("profile_data_exporter: AddDataToJSON")
{
  MockProfileDataExporter exporter{};
  rapidjson::Value json;

  SUBCASE("Test bytes")
  {
    const std::string data{"abc123"};
    std::vector<uint8_t> buf(data.begin(), data.end());
    exporter.AddDataToJSON(json, buf, "BYTES");
    CHECK(json == "abc123");
  }

  SUBCASE("Test json")
  {
    const std::string data{"{\"abc\":\"def\"}"};
    std::vector<uint8_t> buf(data.begin(), data.end());
    exporter.AddDataToJSON(json, buf, "JSON");
    CHECK(json == "{\"abc\":\"def\"}");
  }

  SUBCASE("Test bool")
  {
    const bool data[3] = {true, false, true};
    std::vector<uint8_t> buf(
        reinterpret_cast<const uint8_t*>(data),
        reinterpret_cast<const uint8_t*>(data) + sizeof(data));
    exporter.AddDataToJSON(json, buf, "BOOL");
    CHECK(json[0].GetBool() == true);
    CHECK(json[1].GetBool() == false);
    CHECK(json[2].GetBool() == true);
  }

  SUBCASE("Test uint8")
  {
    const uint8_t data[3] = {1, 2, 3};
    std::vector<uint8_t> buf(
        reinterpret_cast<const uint8_t*>(data),
        reinterpret_cast<const uint8_t*>(data) + sizeof(data));
    exporter.AddDataToJSON(json, buf, "UINT8");
    CHECK(json[0].GetUint() == 1);
    CHECK(json[1].GetUint() == 2);
    CHECK(json[2].GetUint() == 3);
  }

  SUBCASE("Test uint16")
  {
    const uint16_t data[3] = {4, 5, 6};
    std::vector<uint8_t> buf(
        reinterpret_cast<const uint8_t*>(data),
        reinterpret_cast<const uint8_t*>(data) + sizeof(data));
    exporter.AddDataToJSON(json, buf, "UINT16");
    CHECK(json[0].GetUint() == 4);
    CHECK(json[1].GetUint() == 5);
    CHECK(json[2].GetUint() == 6);
  }

  SUBCASE("Test uint32")
  {
    const uint32_t data[3] = {7, 8, 9};
    std::vector<uint8_t> buf(
        reinterpret_cast<const uint8_t*>(data),
        reinterpret_cast<const uint8_t*>(data) + sizeof(data));
    exporter.AddDataToJSON(json, buf, "UINT32");
    CHECK(json[0].GetUint() == 7);
    CHECK(json[1].GetUint() == 8);
    CHECK(json[2].GetUint() == 9);
  }

  SUBCASE("Test uint64")
  {
    const uint64_t data[3] = {10, 11, 12};
    std::vector<uint8_t> buf(
        reinterpret_cast<const uint8_t*>(data),
        reinterpret_cast<const uint8_t*>(data) + sizeof(data));
    exporter.AddDataToJSON(json, buf, "UINT64");
    CHECK(json[0].GetUint64() == 10);
    CHECK(json[1].GetUint64() == 11);
    CHECK(json[2].GetUint64() == 12);
  }

  SUBCASE("Test int8")
  {
    const int8_t data[3] = {1, -2, 3};
    std::vector<uint8_t> buf(
        reinterpret_cast<const uint8_t*>(data),
        reinterpret_cast<const uint8_t*>(data) + sizeof(data));
    exporter.AddDataToJSON(json, buf, "INT8");
    CHECK(json[0].GetInt() == 1);
    CHECK(json[1].GetInt() == -2);
    CHECK(json[2].GetInt() == 3);
  }

  SUBCASE("Test int16")
  {
    const int16_t data[3] = {4, -5, 6};
    std::vector<uint8_t> buf(
        reinterpret_cast<const uint8_t*>(data),
        reinterpret_cast<const uint8_t*>(data) + sizeof(data));
    exporter.AddDataToJSON(json, buf, "INT16");
    CHECK(json[0].GetInt() == 4);
    CHECK(json[1].GetInt() == -5);
    CHECK(json[2].GetInt() == 6);
  }

  SUBCASE("Test int32")
  {
    const int32_t data[3] = {7, -8, 9};
    std::vector<uint8_t> buf(
        reinterpret_cast<const uint8_t*>(data),
        reinterpret_cast<const uint8_t*>(data) + sizeof(data));
    exporter.AddDataToJSON(json, buf, "INT32");
    CHECK(json[0].GetInt() == 7);
    CHECK(json[1].GetInt() == -8);
    CHECK(json[2].GetInt() == 9);
  }

  SUBCASE("Test int64")
  {
    const int64_t data[3] = {10, -11, 12};
    std::vector<uint8_t> buf(
        reinterpret_cast<const uint8_t*>(data),
        reinterpret_cast<const uint8_t*>(data) + sizeof(data));
    exporter.AddDataToJSON(json, buf, "INT64");
    CHECK(json[0].GetInt64() == 10);
    CHECK(json[1].GetInt64() == -11);
    CHECK(json[2].GetInt64() == 12);
  }

  SUBCASE("Test fp32")
  {
    const float data[3] = {1.0, -2.0, 3.0};
    std::vector<uint8_t> buf(
        reinterpret_cast<const uint8_t*>(data),
        reinterpret_cast<const uint8_t*>(data) + sizeof(data));
    exporter.AddDataToJSON(json, buf, "FP32");
    CHECK(json[0].GetFloat() == 1.0);
    CHECK(json[1].GetFloat() == -2.0);
    CHECK(json[2].GetFloat() == 3.0);
  }

  SUBCASE("Test fp64")
  {
    const double data[3] = {4.0, -5.0, 6.0};
    std::vector<uint8_t> buf(
        reinterpret_cast<const uint8_t*>(data),
        reinterpret_cast<const uint8_t*>(data) + sizeof(data));
    exporter.AddDataToJSON(json, buf, "FP64");
    CHECK(json[0].GetDouble() == 4.0);
    CHECK(json[1].GetDouble() == -5.0);
    CHECK(json[2].GetDouble() == 6.0);
  }
}


TEST_CASE("profile_data_exporter: AddExperiment")
{
  MockProfileDataExporter exporter{};

  ProfileDataCollector::Experiment raw_experiment;
  rapidjson::Value entry(rapidjson::kObjectType);
  rapidjson::Value experiment(rapidjson::kObjectType);

  SUBCASE("Concurrency mode")
  {
    ProfileDataCollector::InferenceLoadMode infer_mode{15, 0.0};
    raw_experiment.mode = infer_mode;

    exporter.AddExperiment(entry, experiment, raw_experiment);
    CHECK(entry.HasMember("experiment"));
    CHECK(
        std::string(entry["experiment"]["mode"].GetString()) == "concurrency");
    CHECK(entry["experiment"]["value"].GetUint64() == 15);
  }

  SUBCASE("Request rate mode")
  {
    ProfileDataCollector::InferenceLoadMode infer_mode{0, 23.5};
    raw_experiment.mode = infer_mode;

    exporter.AddExperiment(entry, experiment, raw_experiment);
    CHECK(entry.HasMember("experiment"));
    CHECK(
        std::string(entry["experiment"]["mode"].GetString()) == "request_rate");
    CHECK(entry["experiment"]["value"].GetDouble() == 23.5);
  }
}

TEST_CASE("profile_data_exporter: OutputToFile")
{
  MockProfileDataExporter exporter{};
  std::string file_path;

  SUBCASE("Empty file path")
  {
    file_path = "";
    CHECK_THROWS_WITH_AS(
        exporter.OutputToFile(file_path),
        "failed to open file for outputting raw profile data",
        PerfAnalyzerException);
  }

  SUBCASE("With file path")
  {
    file_path = "/tmp/test-" + GetRandomString(4) + ".json";
    CHECK_NOTHROW(exporter.OutputToFile(file_path));
    CHECK(IsFile(file_path));

    std::remove(file_path.c_str());
    CHECK(!IsFile(file_path));
  }
}

TEST_CASE("profile_data_exporter: AddServiceKind")
{
  MockProfileDataExporter exporter{};
  exporter.ClearDocument();

  cb::BackendKind service_kind;
  std::string json{""};

  SUBCASE("Backend kind: TRITON")
  {
    service_kind = cb::BackendKind::TRITON;
    json = R"({ "service_kind": "triton" })";
  }

  SUBCASE("Backend kind: TENSORFLOW_SERVING")
  {
    service_kind = cb::BackendKind::TENSORFLOW_SERVING;
    json = R"({ "service_kind": "tfserving" })";
  }

  SUBCASE("Backend kind: TORCHSERVE")
  {
    service_kind = cb::BackendKind::TORCHSERVE;
    json = R"({ "service_kind": "torchserve" })";
  }

  SUBCASE("Backend kind: TRITON_C_API")
  {
    service_kind = cb::BackendKind::TRITON_C_API;
    json = R"({ "service_kind": "triton_c_api" })";
  }

  SUBCASE("Backend kind: OPENAI")
  {
    service_kind = cb::BackendKind::OPENAI;
    json = R"({ "service_kind": "openai" })";
  }

  exporter.AddServiceKind(service_kind);
  rapidjson::Document expected_document;
  expected_document.Parse(json.c_str());

  const rapidjson::Value& expected_kind{expected_document["service_kind"]};
  const rapidjson::Value& actual_kind{exporter.document_["service_kind"]};
  CHECK(actual_kind == expected_kind);
}

TEST_CASE("profile_data_exporter: AddEndpoint")
{
  MockProfileDataExporter exporter{};
  exporter.ClearDocument();

  std::string endpoint{""};
  std::string json{""};

  SUBCASE("Endpoint: OpenAI Chat Completions")
  {
    endpoint = "v1/chat/completions";
    json = R"({ "endpoint": "v1/chat/completions" })";
  }

  SUBCASE("Endpoint: OpenAI Completions")
  {
    endpoint = "v1/completions";
    json = R"({ "endpoint": "v1/completions" })";
  }

  exporter.AddEndpoint(endpoint);
  rapidjson::Document expected_document;
  expected_document.Parse(json.c_str());

  const rapidjson::Value& expected_endpoint{expected_document["endpoint"]};
  const rapidjson::Value& actual_endpoint{exporter.document_["endpoint"]};
  CHECK(actual_endpoint == expected_endpoint);
}

}}  // namespace triton::perfanalyzer
