# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2022 CONTACT Software GmbH
# https://www.contact-software.com
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


"""Module providing configurations for the debugpy plugin for spin"""

from csspin import config

defaults = config(
    opts=[
        "--listen localhost:5678",
        "--wait-for-client",
    ],
    requires=config(
        spin=["csspin_python.python"],
        python=["debugpy"],
    ),
)
