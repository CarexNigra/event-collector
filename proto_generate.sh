#!/bin/sh

set -e

PWD=$(pwd)

mkdir -p gen_protoc

python -m grpc_tools.protoc \
    -I="${PWD}/proto" \
    --python_out="${PWD}" \
    --pyi_out="${PWD}" \
    $(find "${PWD}/proto/events" -name "*.proto")

find "${PWD}/events/" -type d -exec touch {}/__init__.py ';'