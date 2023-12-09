#!/bin/sh

set -e

PWD=$(pwd)

# mkdir -p gen_protoc && python -m grpc_tools.protoc \
#     --proto_path="${PWD}/proto" \
#     --python_out="${PWD}/gen_protoc" \
#     --grpc_python_out="${PWD}/gen_protoc" \
#     $(find "${PWD}/proto" -name "*.proto")

# find "${PWD}/gen_protoc/*" -type d -exec touch {}/__init__.py ';'

mkdir -p gen_protoc

python -m grpc_tools.protoc \
    -I="${PWD}/proto" \
    --python_out="${PWD}/gen_protoc" \
    "${PWD}/proto/events/test_events.proto"