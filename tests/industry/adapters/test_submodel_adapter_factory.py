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

import unittest
from types import SimpleNamespace

from tractusx_sdk.industry.adapters.submodel_adapter_factory import (
    SubmodelAdapterFactory,
    SubmodelAdapterType,
)
from tractusx_sdk.industry.adapters.submodel_adapters import FileSystemAdapter


class TestSubmodelAdapterFactory(unittest.TestCase):

    def tearDown(self):
        SubmodelAdapterFactory.unregister_adapter("external_builder")
        SubmodelAdapterFactory.unregister_adapter("external_class")

    def test_get_file_system_success(self):
        adapter = SubmodelAdapterFactory.get_file_system(root_path="./submodels")

        self.assertIsNotNone(adapter)
        self.assertIsInstance(adapter, FileSystemAdapter)
        self.assertEqual(adapter.root_path, "./submodels")

    def test_from_config_success(self):
        adapter = SubmodelAdapterFactory.from_config(
            {
                "type": "file_system",
                "root_path": "./submodels",
            }
        )

        self.assertIsInstance(adapter, FileSystemAdapter)
        self.assertEqual(adapter.root_path, "./submodels")

    def test_from_config_custom_type_key_success(self):
        adapter = SubmodelAdapterFactory.from_config(
            {
                "adapter": SubmodelAdapterType.FILE_SYSTEM,
                "root_path": "./custom-submodels",
            },
            type_key="adapter",
        )

        self.assertIsInstance(adapter, FileSystemAdapter)
        self.assertEqual(adapter.root_path, "./custom-submodels")

    def test_from_config_missing_type_key(self):
        with self.assertRaises(ValueError):
            SubmodelAdapterFactory.from_config(
                {
                    "root_path": "./submodels",
                }
            )

    def test_from_config_unsupported_type(self):
        with self.assertRaises(ValueError):
            SubmodelAdapterFactory.from_config(
                {
                    "type": "unsupported",
                    "root_path": "./submodels",
                }
            )

    def test_from_config_unknown_builder_key(self):
        with self.assertRaises(ValueError):
            SubmodelAdapterFactory.from_config(
                {
                    "type": "file_system",
                    "root_path": "./submodels",
                    "unknown": "value",
                }
            )

    def test_adapter_type_listings_before_and_after_external_registration(self):
        self.assertNotIn("file_system", SubmodelAdapterFactory.get_registered_adapter_types())
        self.assertIn("file_system", SubmodelAdapterFactory.get_available_adapter_types())

        class ExternalBuilder:
            def build(self):
                return SimpleNamespace()

        SubmodelAdapterFactory.register_adapter(
            adapter_type="external_builder",
            builder_factory=ExternalBuilder,
        )

        self.assertIn("external_builder", SubmodelAdapterFactory.get_registered_adapter_types())
        self.assertIn("external_builder", SubmodelAdapterFactory.get_available_adapter_types())
        self.assertIn("file_system", SubmodelAdapterFactory.get_available_adapter_types())

    def test_register_external_builder_and_create_from_config(self):
        class ExternalBuilder:
            def __init__(self):
                self._data = {}

            def base_url(self, base_url: str):
                self._data["base_url"] = base_url
                return self

            def api_key(self, api_key: str):
                self._data["api_key"] = api_key
                return self

            def build(self):
                return SimpleNamespace(**self._data)

        SubmodelAdapterFactory.register_adapter(
            adapter_type="external_builder",
            builder_factory=ExternalBuilder,
        )

        adapter = SubmodelAdapterFactory.from_config(
            {
                "type": "external_builder",
                "base_url": "https://example.org",
                "api_key": "token",
            }
        )

        self.assertEqual(adapter.base_url, "https://example.org")
        self.assertEqual(adapter.api_key, "token")

    def test_register_external_adapter_class_and_create_from_config(self):
        class ExternalAdapter:
            @classmethod
            def builder(cls):
                class _Builder:
                    def __init__(self):
                        self._data = {}

                    def root_path(self, root_path: str):
                        self._data["root_path"] = root_path
                        return self

                    def build(self):
                        return SimpleNamespace(source="external_class", **self._data)

                return _Builder()

        SubmodelAdapterFactory.register_adapter(
            adapter_type="external_class",
            adapter_class=ExternalAdapter,
        )

        adapter = SubmodelAdapterFactory.from_config(
            {
                "type": "external_class",
                "root_path": "./outside",
            }
        )

        self.assertEqual(adapter.source, "external_class")
        self.assertEqual(adapter.root_path, "./outside")
