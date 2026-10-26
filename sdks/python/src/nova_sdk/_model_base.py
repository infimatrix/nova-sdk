"""Base class for typed response models.

Models are dataclasses with attribute access (``tenant.name``) that also behave as
read-only mappings (``tenant["name"]``) over the original response payload, so code
written against the raw ``dict`` responses of earlier SDK versions keeps working.
The untouched payload is always available as ``model.raw``.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar, TypeVar

M = TypeVar("M", bound="NovaModel")


@dataclass(eq=False)
class NovaModel(Mapping[str, Any]):
    """Common behaviour for generated API models."""

    #: field name -> (model class name, is_list) for nested model parsing
    _nested: ClassVar[dict[str, tuple[str, bool]]] = {}
    #: python attribute name -> JSON key, when they differ
    _aliases: ClassVar[dict[str, str]] = {}

    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls: type[M], data: Any) -> M:
        """Build a model from an API payload. Unknown keys are kept in ``raw``."""
        if isinstance(data, cls):
            return data
        if isinstance(data, NovaModel):
            data = data.raw
        if not isinstance(data, Mapping):
            raise TypeError(f"Cannot build {cls.__name__} from {type(data).__name__}")
        payload = dict(data)
        kwargs: dict[str, Any] = {}
        module = sys.modules[cls.__module__]
        for attr in cls.__dataclass_fields__:
            if attr == "raw":
                continue
            key = cls._aliases.get(attr, attr)
            if key not in payload:
                continue
            value = payload[key]
            nested = cls._nested.get(attr)
            if nested is not None and value is not None:
                model_cls = getattr(module, nested[0])
                if nested[1]:
                    value = [
                        model_cls.from_dict(v) if isinstance(v, Mapping) else v
                        for v in value
                    ]
                elif isinstance(value, Mapping):
                    value = model_cls.from_dict(value)
            kwargs[attr] = value
        return cls(raw=payload, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Return a shallow copy of the raw API payload."""
        return dict(self.raw)

    # -- read-only Mapping protocol over the raw payload ---------------------
    def __getitem__(self, key: str) -> Any:
        return self.raw[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.raw)

    def __len__(self) -> int:
        return len(self.raw)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, NovaModel):
            return self.raw == other.raw
        if isinstance(other, Mapping):
            return self.raw == dict(other)
        return NotImplemented

    __hash__ = None  # type: ignore[assignment]


def parse_model(model: type[M], data: Any) -> M | Any:
    """Parse ``data`` into ``model`` when it is a JSON object, else return it unchanged."""
    if isinstance(data, Mapping):
        return model.from_dict(data)
    return data
