# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import multiprocessing
import os
import time
from collections import defaultdict

import pytest

try:
    multiprocessing.set_start_method("spawn")
except Exception:
    assert multiprocessing.get_start_method() == "spawn"

CALL_TIMES = defaultdict(lambda: 0.0)


def pytest_sessionfinish(maxprint=50):
    out_str = """
Call times:
===========
"""
    keys = list(CALL_TIMES.keys())
    if len(keys) > 1:
        maxchar = max(*[len(key) for key in keys])
    elif len(keys):
        maxchar = len(keys[0])
    else:
        return
    for i, (key, item) in enumerate(
        sorted(CALL_TIMES.items(), key=lambda x: x[1], reverse=True)
    ):
        spaces = "  " + " " * (maxchar - len(key))
        out_str += f"\t{key}{spaces}{item: 4.4f}s\n"
        if i == maxprint - 1:
            break


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(autouse=True)
def measure_duration(request: pytest.FixtureRequest):
    start_time = time.time()

    def fin():
        duration = time.time() - start_time
        name = request.node.name
        class_name = request.cls.__name__ if request.cls else None
        name = name.split("[")[0]
        if class_name is not None:
            name = "::".join([class_name, name])
        file = os.path.basename(request.path)
        name = f"{file}::{name}"
        CALL_TIMES[name] = CALL_TIMES[name] + duration

    request.addfinalizer(fin)
