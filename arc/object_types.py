import uuid
from typing import TypeAlias

from arc.link import ObjectDelta
from arc.object import Object, ObjectPath

ObjectCache: TypeAlias = dict[uuid.UUID, list[Object]]
VarCache: TypeAlias = dict[uuid.UUID, int]
Cache: TypeAlias = tuple[ObjectCache, VarCache]
PathMap: TypeAlias = dict[uuid.UUID, set[ObjectPath]]

ObjectGroup: TypeAlias = list[list[Object]]
LinkGroup: TypeAlias = list[list[ObjectDelta]]
