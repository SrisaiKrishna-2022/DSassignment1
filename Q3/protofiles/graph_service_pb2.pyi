from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NodeList(_message.Message):
    __slots__ = ("neighbors",)
    NEIGHBORS_FIELD_NUMBER: _ClassVar[int]
    neighbors: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, neighbors: _Optional[_Iterable[str]] = ...) -> None: ...

class SubmitGraphRequest(_message.Message):
    __slots__ = ("client_id", "adjacency")
    class AdjacencyEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: NodeList
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[NodeList, _Mapping]] = ...) -> None: ...
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    ADJACENCY_FIELD_NUMBER: _ClassVar[int]
    client_id: str
    adjacency: _containers.MessageMap[str, NodeList]
    def __init__(self, client_id: _Optional[str] = ..., adjacency: _Optional[_Mapping[str, NodeList]] = ...) -> None: ...

class SubmitGraphResponse(_message.Message):
    __slots__ = ("client_nodes", "client_edges", "union_nodes", "union_edges")
    CLIENT_NODES_FIELD_NUMBER: _ClassVar[int]
    CLIENT_EDGES_FIELD_NUMBER: _ClassVar[int]
    UNION_NODES_FIELD_NUMBER: _ClassVar[int]
    UNION_EDGES_FIELD_NUMBER: _ClassVar[int]
    client_nodes: int
    client_edges: int
    union_nodes: int
    union_edges: int
    def __init__(self, client_nodes: _Optional[int] = ..., client_edges: _Optional[int] = ..., union_nodes: _Optional[int] = ..., union_edges: _Optional[int] = ...) -> None: ...

class QueryK(_message.Message):
    __slots__ = ("k",)
    K_FIELD_NUMBER: _ClassVar[int]
    k: int
    def __init__(self, k: _Optional[int] = ...) -> None: ...

class BoolReply(_message.Message):
    __slots__ = ("ok",)
    OK_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    def __init__(self, ok: bool = ...) -> None: ...

class ResetRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResetResponse(_message.Message):
    __slots__ = ("cleared",)
    CLEARED_FIELD_NUMBER: _ClassVar[int]
    cleared: bool
    def __init__(self, cleared: bool = ...) -> None: ...
