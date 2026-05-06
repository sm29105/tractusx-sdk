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

from enum import StrEnum
from importlib import import_module
from typing import Any, Callable, Mapping

class SubmodelAdapterType(StrEnum):
    """
    Enum for different adapter types. Each adapter type corresponds to a specific implementation,
    and must correspond exactly to the prefix of the adapter class it is associated with.
    """
    FILE_SYSTEM = "FileSystem"

class SubmodelAdapterFactory:
    """
    Factory for creating and extending submodel adapters.

    The factory supports two creation paths:
    - Built-in adapters discovered from the SDK adapter module.
    - External adapters registered at runtime via ``register_adapter``.

    Adapters are instantiated through their builder interface and can be
    configured from key-value mappings via ``from_config``.

    Example:
        Create a built-in adapter from configuration::

            adapter = SubmodelAdapterFactory.from_config(
                {
                    "type": "file_system",
                    "root_path": "./submodels",
                }
            )
    """
    _registered_builders: dict[str, Callable[[], Any]] = {}

    @staticmethod
    def _normalize_type_key(adapter_type: str | SubmodelAdapterType) -> str:
        """
        Normalize an adapter type identifier into a registry-safe key.

        Examples:
            >>> SubmodelAdapterFactory._normalize_type_key("file_system")
            'file_system'
            >>> SubmodelAdapterFactory._normalize_type_key(SubmodelAdapterType.FILE_SYSTEM)
            'file_system'
            >>> SubmodelAdapterFactory._normalize_type_key(" File-System ")
            'file_system'
            >>> SubmodelAdapterFactory._normalize_type_key("Custom Adapter")
            'custom_adapter'
            >>> SubmodelAdapterFactory._normalize_type_key("")
            ValueError: adapter_type must be a non-empty string or SubmodelAdapterType

        :param adapter_type: Adapter type as enum or string.
        :return: Lowercase normalized key using underscores.
        :raises ValueError: If the input is empty or invalid.
        """
        if isinstance(adapter_type, SubmodelAdapterType):
            return adapter_type.name.lower()

        if not isinstance(adapter_type, str) or not adapter_type.strip():
            raise ValueError("adapter_type must be a non-empty string or SubmodelAdapterType")

        return adapter_type.strip().replace("-", "_").replace(" ", "_").lower()

    @staticmethod
    def _to_adapter_type(adapter_type: str | SubmodelAdapterType) -> SubmodelAdapterType | None:
        """
        Resolve a built-in adapter type from enum or string input.

        :param adapter_type: Adapter type as enum name/value or string.
        :return: Matching built-in enum value, or ``None`` if no built-in type matches.
        """
        if isinstance(adapter_type, SubmodelAdapterType):
            return adapter_type

        normalized = SubmodelAdapterFactory._normalize_type_key(adapter_type).upper()

        try:
            return SubmodelAdapterType[normalized]
        except KeyError:
            for value in SubmodelAdapterType:
                if value.value.lower() == adapter_type.strip().lower():
                    return value
            return None

    @staticmethod
    def register_adapter(
            adapter_type: str,
            builder_factory: Callable[[], Any] | None = None,
            adapter_class: Any = None,
            overwrite: bool = False,
    ) -> None:
        """
        Register an external adapter type.

        Provide either ``builder_factory`` (returns a builder) or ``adapter_class``
        exposing a callable ``builder`` classmethod.

        :param adapter_type: External adapter type key.
        :param builder_factory: Callable returning a builder instance.
        :param adapter_class: Adapter class exposing ``builder()``.
        :param overwrite: Whether to overwrite an existing external registration.
        :raises ValueError: If registration parameters are invalid.
        :raises TypeError: If callable requirements are not met.

        Example:
            Register a custom adapter class and use it with ``from_config``::

                class ExternalAdapter:
                    @classmethod
                    def builder(cls):
                        return cls._Builder()

                SubmodelAdapterFactory.register_adapter(
                    adapter_type="external",
                    adapter_class=ExternalAdapter,
                )
        """
        if not builder_factory and adapter_class is None:
            raise ValueError("Either builder_factory or adapter_class must be provided")

        if builder_factory and adapter_class is not None:
            raise ValueError("Provide only one of builder_factory or adapter_class")

        adapter_key = SubmodelAdapterFactory._normalize_type_key(adapter_type)
        if adapter_key in SubmodelAdapterFactory._registered_builders and not overwrite:
            raise ValueError(f"Adapter type '{adapter_type}' is already registered")

        if builder_factory is not None:
            if not callable(builder_factory):
                raise TypeError("builder_factory must be callable")
            SubmodelAdapterFactory._registered_builders[adapter_key] = builder_factory
            return

        class_builder = getattr(adapter_class, "builder", None)
        if not callable(class_builder):
            raise TypeError("adapter_class must expose a callable builder classmethod")
        SubmodelAdapterFactory._registered_builders[adapter_key] = class_builder

    @staticmethod
    def unregister_adapter(adapter_type: str) -> None:
        """
        Unregister a previously registered external adapter type.

        :param adapter_type: External adapter type key.

        Example:
            Remove a runtime registration::

                SubmodelAdapterFactory.unregister_adapter("external")
        """
        adapter_key = SubmodelAdapterFactory._normalize_type_key(adapter_type)
        SubmodelAdapterFactory._registered_builders.pop(adapter_key, None)

    @staticmethod
    def get_registered_adapter_types() -> list[str]:
        """
        Return all currently registered external adapter type keys.

        This method only reports adapters registered at runtime through
        ``register_adapter``. Built-in adapters declared in
        ``SubmodelAdapterType`` are intentionally excluded.

        :return: Sorted list of registered adapter keys.

        Example:
            Inspect current registrations::

                types = SubmodelAdapterFactory.get_registered_adapter_types()
        """
        return sorted(SubmodelAdapterFactory._registered_builders.keys())

    @staticmethod
    def get_available_adapter_types() -> list[str]:
        """
        Return all available adapter type keys.

        This method combines:
        - Built-in adapter types from ``SubmodelAdapterType``.
        - External adapter types registered via ``register_adapter``.

        Built-in and external values are normalized to the same lowercase
        underscore style.

        :return: Sorted list of all available adapter keys.

        Example:
            Inspect all available adapters::

                types = SubmodelAdapterFactory.get_available_adapter_types()
        """
        builtins = [item.name.lower() for item in SubmodelAdapterType]
        externals = SubmodelAdapterFactory.get_registered_adapter_types()
        return sorted(set(builtins + externals))

    @staticmethod
    def _get_adapter_builder(
            adapter_type: str | SubmodelAdapterType,
    ):
        """
        Resolve and return a builder for a built-in or registered adapter type.

        :param adapter_type: Adapter type identifier.
        :return: Builder instance for the resolved adapter.
        :raises ValueError: If the type is unknown.
        :raises AttributeError: If the built-in adapter class cannot be resolved.
        :raises ImportError: If the built-in adapter module cannot be imported.
        """
        adapter_type_enum = SubmodelAdapterFactory._to_adapter_type(adapter_type)

        if adapter_type_enum is None:
            adapter_key = SubmodelAdapterFactory._normalize_type_key(adapter_type)
            if adapter_key in SubmodelAdapterFactory._registered_builders:
                return SubmodelAdapterFactory._registered_builders[adapter_key]()

            allowed = SubmodelAdapterFactory.get_available_adapter_types()
            raise ValueError(
                f"Unsupported adapter type '{adapter_type}'. Allowed values: {', '.join(sorted(set(allowed)))}"
            )

        adapter_module = ".".join(__name__.split(".")[0:-1])
        module_name = f"{adapter_module}.submodel_adapters"
        adapter_class_name = f"{adapter_type_enum.value}Adapter"

        try:
            module = import_module(module_name)
            adapter_class = getattr(module, adapter_class_name)
            return adapter_class.builder()
        except AttributeError as attr_exception:
            raise AttributeError(
                f"Failed to import adapter class {adapter_class_name} for module {module_name}"
            ) from attr_exception
        except ImportError as import_exception:
            raise ImportError(
                f"Failed to import module {module_name}. Ensure that the required packages are installed and the PYTHONPATH is set correctly."
            ) from import_exception

    @staticmethod
    def from_config(config: Mapping[str, Any], type_key: str = "type"):
        """
        Create a submodel adapter from key-value configuration.

        The adapter type is derived from ``config[type_key]`` and all remaining keys are
        passed to builder methods with the same name.

        :param config: Configuration map used to construct the adapter.
        :param type_key: Key containing the adapter type value.
        :return: Constructed adapter instance.
        :raises TypeError: If ``config`` is not a mapping.
        :raises ValueError: If config validation or builder key resolution fails.

        Examples:
            Use the default type key::

                adapter = SubmodelAdapterFactory.from_config(
                    {
                        "type": "file_system",
                        "root_path": "./submodels",
                    }
                )

            Use a custom type key::

                adapter = SubmodelAdapterFactory.from_config(
                    {
                        "adapter": "file_system",
                        "root_path": "./submodels",
                    },
                    type_key="adapter",
                )
        """
        if not isinstance(config, Mapping):
            raise TypeError("config must be a mapping")

        if not type_key or not isinstance(type_key, str):
            raise ValueError("type_key must be a non-empty string")

        if type_key not in config:
            raise ValueError(f"Missing required config key '{type_key}'")

        adapter_type = config[type_key]
        builder = SubmodelAdapterFactory._get_adapter_builder(adapter_type=adapter_type)

        for key, value in config.items():
            if key == type_key:
                continue

            builder_method = getattr(builder, key, None)
            if not callable(builder_method):
                raise ValueError(f"Unsupported config key '{key}' for adapter type '{adapter_type}'")

            builder_method(value)

        return builder.build()
    
    @staticmethod
    def get_file_system(root_path: str = "./submodel"):
        """
        Create a file system submodel adapter.

        :param root_path: Root directory for submodel storage.
        :return: Built file system adapter instance.

        Example:
            Create the default file system adapter::

                adapter = SubmodelAdapterFactory.get_file_system("./submodels")
        """
        return SubmodelAdapterFactory.from_config(
            {
                "type": SubmodelAdapterType.FILE_SYSTEM,
                "root_path": root_path,
            }
        )
