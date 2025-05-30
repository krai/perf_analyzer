# Copyright 2020-2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

cmake_minimum_required (VERSION 3.18)

find_package(CURL REQUIRED)

# fixme
add_definitions(-DCURL_STATICLIB)

#
# Dependencies
#
include(FetchContent)

FetchContent_Declare(
  repo-common
  GIT_REPOSITORY ${TRITON_REPO_ORGANIZATION}/common.git
  GIT_TAG ${TRITON_COMMON_REPO_TAG}
  GIT_SHALLOW ON
)

set(TRITON_COMMON_ENABLE_PROTOBUF ON)
set(TRITON_COMMON_ENABLE_GRPC ON)

FetchContent_MakeAvailable(repo-common)

add_subdirectory(triton)

if(TRITON_ENABLE_PERF_ANALYZER_C_API)
  add_subdirectory(triton_c_api)
endif() # TRITON_ENABLE_PERF_ANALYZER_C_API

if(TRITON_ENABLE_PERF_ANALYZER_TFS)
  add_subdirectory(tensorflow_serving)
endif() # TRITON_ENABLE_PERF_ANALYZER_TFS

if(TRITON_ENABLE_PERF_ANALYZER_TS)
  add_subdirectory(torchserve)
endif() # TRITON_ENABLE_PERF_ANALYZER_TS

if(TRITON_ENABLE_PERF_ANALYZER_OPENAI)
  add_subdirectory(openai)
endif() # TRITON_ENABLE_PERF_ANALYZER_OPENAI

if(TRITON_ENABLE_PERF_ANALYZER_DGRPC)
  add_subdirectory(dynamic_grpc)
endif() # TRITON_ENABLE_PERF_ANALYZER_DGRPC

set(
  CLIENT_BACKEND_SRCS
  client_backend.cc
)

set(
  CLIENT_BACKEND_HDRS
  client_backend.h
)

if(TRITON_ENABLE_PERF_ANALYZER_C_API)
  set(CAPI_LIBRARY $<TARGET_OBJECTS:triton-c-api-backend-library>)
  set(CAPI_TARGET_LINK_LIBRARY PUBLIC $<TARGET_PROPERTY:triton-c-api-backend-library,LINK_LIBRARIES>)
  set(CAPI_TARGET_INCLUDE_DIRECTORY PRIVATE $<TARGET_PROPERTY:triton-c-api-backend-library,INCLUDE_DIRECTORIES>)
endif() # TRITON_ENABLE_PERF_ANALYZER_C_API

if(TRITON_ENABLE_PERF_ANALYZER_TFS)
  set(TFS_LIBRARY $<TARGET_OBJECTS:tfs-client-backend-library>)
  set(TFS_TARGET_LINK_LIBRARY PUBLIC $<TARGET_PROPERTY:tfs-client-backend-library,LINK_LIBRARIES>)
  set(TFS_TARGET_INCLUDE_DIRECTORY PRIVATE $<TARGET_PROPERTY:tfs-client-backend-library,INCLUDE_DIRECTORIES>)
endif() # TRITON_ENABLE_PERF_ANALYZER_TFS

if(TRITON_ENABLE_PERF_ANALYZER_TS)
  set(TS_LIBRARY $<TARGET_OBJECTS:ts-client-backend-library>)
  set(TS_TARGET_LINK_LIBRARY PUBLIC $<TARGET_PROPERTY:ts-client-backend-library,LINK_LIBRARIES>)
  set(TS_TARGET_INCLUDE_DIRECTORY PRIVATE $<TARGET_PROPERTY:ts-client-backend-library,INCLUDE_DIRECTORIES>)
endif() # TRITON_ENABLE_PERF_ANALYZER_TS

if(TRITON_ENABLE_PERF_ANALYZER_OPENAI)
  set(OPENAI_LIBRARY $<TARGET_OBJECTS:openai-client-backend-library>)
  set(OPENAI_TARGET_LINK_LIBRARY PUBLIC $<TARGET_PROPERTY:openai-client-backend-library,LINK_LIBRARIES>)
  set(OPENAI_TARGET_INCLUDE_DIRECTORY PRIVATE $<TARGET_PROPERTY:openai-client-backend-library,INCLUDE_DIRECTORIES>)
endif() # TRITON_ENABLE_PERF_ANALYZER_OPENAIs

if(TRITON_ENABLE_PERF_ANALYZER_DGRPC)
  set(DGRPC_LIBRARY $<TARGET_OBJECTS:dgrpc-client-backend-library>)
  set(DGRPC_TARGET_LINK_LIBRARY PUBLIC $<TARGET_PROPERTY:dgrpc-client-backend-library,LINK_LIBRARIES>)
  set(DGRPC_TARGET_INCLUDE_DIRECTORY PRIVATE $<TARGET_PROPERTY:dgrpc-client-backend-library,INCLUDE_DIRECTORIES>)
endif() # TRITON_ENABLE_PERF_ANALYZER_DGRPC

add_library(
  client-backend-library
  ${CLIENT_BACKEND_SRCS}
  ${CLIENT_BACKEND_HDRS}
  $<TARGET_OBJECTS:triton-client-backend-library>
  ${CAPI_LIBRARY}
  ${TFS_LIBRARY}
  ${TS_LIBRARY}
  ${OPENAI_LIBRARY}
  ${DGRPC_LIBRARY}
)

target_link_libraries(
  client-backend-library
    PUBLIC
      triton-common-json        # from repo-common
      triton-client-backend-library
      ${TRITON_JSON_STATIC_LIB}
      ${CAPI_TARGET_LINK_LIBRARY}
      ${TFS_TARGET_LINK_LIBRARY}
      ${TS_TARGET_LINK_LIBRARY}
      ${OPENAI_TARGET_LINK_LIBRARY}
      ${DGRPC_TARGET_LINK_LIBRARY}
)

target_include_directories(
  client-backend-library
  PUBLIC
    $<TARGET_PROPERTY:triton-client-backend-library,INCLUDE_DIRECTORIES>
    ${CAPI_TARGET_INCLUDE_DIRECTORY}
    ${TFS_TARGET_INCLUDE_DIRECTORY}
    ${TS_TARGET_INCLUDE_DIRECTORY}
    ${OPENAI_TARGET_INCLUDE_DIRECTORY}
    ${DGRPC_TARGET_INCLUDE_DIRECTORY}
)

