# common_core

Common Core is a library that provides a set of common utilities for Python projects.

## Contents:
- **Centralized Config metaclass**: 
  - `common_core.config.ConfigMeta`
  - Allows for centralized configuration of a project across multiple modules
  - Merges configuration from multiple sources (e.g. environment variables, config files, etc.)
  - Provides metadata for configuration options (e.g. required, default value, etc.)
  - Can 'lock' a configuration at a parent level to prevent further changes by child classes
  - see `common_core.config.ConfigMeta` for more details and usage.
- **Nested Dataclass**:
  - `common_core.utils.nested_dataclass_factory` 
  - A factory function that creates strongly typed dataclasses with the ability to add child nodes in a structure similar to a doubly linked list.
  - The dataclass pattern is defined by providing the desired Field names and default values to the factory. 
  - The factory then creates a dataclass with the specified fields/default values and enforces the type.
  - Child nodes can be added to the dataclass by calling the `add_child()` method on the parent node.
  - Parent nodes can be accessed from child nodes by calling the `parent` attribute.
  - See `common_core.utils.baseclass.nested_dataclass` for more details and usage.