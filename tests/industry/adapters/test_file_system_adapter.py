#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 DRÄXLMAIER Group
# (represented by Lisa Dräxlmaier GmbH)
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

import tempfile
import unittest
from pathlib import Path

from tractusx_sdk.industry.adapters.submodel_adapters import FileSystemAdapter


class TestFileSystemAdapter(unittest.TestCase):

    def test_write_auto_creates_missing_parent_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(root_path=temp_dir)

            adapter.write("nested/folder/file.json", {"hello": "world"})

            written_file = Path(temp_dir) / "nested" / "folder" / "file.json"
            self.assertTrue(written_file.exists())

    def test_delete_removes_empty_parent_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(root_path=temp_dir)

            adapter.write("nested/folder/file.json", {"hello": "world"})
            adapter.delete("nested/folder/file.json")

            nested_folder = Path(temp_dir) / "nested" / "folder"
            nested_root = Path(temp_dir) / "nested"
            self.assertFalse(nested_folder.exists())
            self.assertFalse(nested_root.exists())
            self.assertTrue(Path(temp_dir).exists())

    def test_delete_keeps_parent_folder_when_other_files_exist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(root_path=temp_dir)

            adapter.write("nested/folder/file1.json", {"id": 1})
            adapter.write("nested/folder/file2.json", {"id": 2})

            adapter.delete("nested/folder/file1.json")

            nested_folder = Path(temp_dir) / "nested" / "folder"
            remaining_file = nested_folder / "file2.json"
            self.assertTrue(nested_folder.exists())
            self.assertTrue(remaining_file.exists())
