import typing as t

from .user import User
from .application import PartialApplication

# https://github.com/python/cpython/pull/27663
# ----------------------------------------------------------------------
class _(t.TypedDict):pass
_TypedDictMeta=type(_)
def _(cls,name,bases,ns,total=True):
    for base in bases:
        if not(type(base)is _TypedDictMeta or base is t.Generic):
            raise TypeError('cannot inherit from both a TypedDict type '
                            'and a non-TypedDict base class')
        if any(issubclass(b,t.Generic)for b in bases):
            if'__orig_bases__'in ns:generic_base=(t.Generic,)
            else:
                generic_base = ()
                ns['__parameters__'] = ()
        else:generic_base=()
        tp_dict=type.__new__(_TypedDictMeta,name,(*generic_base,dict,),ns)
        annotations={}
        own_annotations=ns.get('__annotations__',{})
        own_annotation_keys=set(own_annotations.keys())
        msg = "TypedDict('Name', {f0: t0, f1: t1, ...}); each t must be a type"
        own_annotations={n: t._type_check(tp, msg)for n,tp in own_annotations.items()}
        required_keys=set()
        optional_keys=set()
        for base in bases:
            annotations.update(base.__dict__.get('__annotations__', {}))
            required_keys.update(base.__dict__.get('__required_keys__', ()))
            optional_keys.update(base.__dict__.get('__optional_keys__', ()))
        annotations.update(own_annotations)
        if total:required_keys.update(own_annotation_keys)
        else:optional_keys.update(own_annotation_keys)
        tp_dict.__annotations__ = annotations
        tp_dict.__required_keys__ = frozenset(required_keys)
        tp_dict.__optional_keys__ = frozenset(optional_keys)
        if not hasattr(tp_dict, '__total__'):tp_dict.__total__ = total
        return tp_dict
_TypedDictMeta.__new__=_
def _(cls,params):
    if issubclass(cls, t.Generic):return cls.__class_getitem__(params)
    raise TypeError(f"'{cls!r}' is not subscriptable")
_TypedDictMeta.__getitem__=t._tp_cache(_)
# ----------------------------------------------------------------------


class Hello(t.TypedDict):
    heartbeat_interval: int


UnvailableGuild = t.NewType("UnvailableGuild", dict)


class Ready(t.TypedDict, total=False):
    v: int
    user: User
    guilds: t.List[UnvailableGuild]
    session_id: str
    shard: t.Optional[t.Tuple[int, int]]
    application: PartialApplication


Resumed = t.Literal[None]  # FIXME
Reconnect = t.Literal[None]
InvalidSession = bool


T = t.TypeVar('T')


class Payload(t.TypedDict, t.Generic[T]):  # type: ignore
    op: int
    d: T


HelloPayload = Payload[Hello]
ReadyPayload = Payload[Ready]
ResumedPayload = Payload[Resumed]
ReconnectPayload = Payload[Reconnect]
InvalidSessionPayload = Payload[InvalidSession]

GatewayPayload = t.Union[
    HelloPayload,
    ReadyPayload,
    ResumedPayload,
    ReconnectPayload,
    InvalidSessionPayload,
]
