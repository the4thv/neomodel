from .util import items
from .properties import AliasProperty, Property
from .relationship_manager import RelationshipDefinition, RelationshipManager
from .exception import NoSuchProperty
import types


class NeoObject(object):
    def __init__(self, *args, **kwargs):
        try:
            super(NeoObject, self).__init__(*args, **kwargs)
        except TypeError:
            super(NeoObject, self).__init__()
        self.__node__ = None
        for key, val in items(self._class_properties()):
            if val.__class__ is RelationshipDefinition:
                self.__dict__[key] = val.build_manager(self, key)
            # handle default values
            elif isinstance(val, (Property,)) and not isinstance(val, (AliasProperty,)):
                if not key in kwargs or kwargs[key] is None:
                    if val.has_default:
                        kwargs[key] = val.default_value()
        for key, value in items(kwargs):
            if not(key.startswith("__") and key.endswith("__")):
                setattr(self, key, value)

    @property
    def __properties__(self):
        node_props = {}
        for key, value in items(super(NeoObject, self).__dict__):
            if (not key.startswith('_')
                    and not isinstance(value, types.MethodType)
                    and not isinstance(value, RelationshipManager)
                    and not isinstance(value, AliasProperty)
                    and value is not None):
                node_props[key] = value
        return node_props

    @classmethod
    def inflate(cls, node):
        props = {}
        for key, prop in items(cls._class_properties()):
            if (issubclass(prop.__class__, Property)
                    and not isinstance(prop, AliasProperty)):
                if key in node.__metadata__['data']:
                    props[key] = prop.inflate(node.__metadata__['data'][key], node_id=node.id)
                elif prop.has_default:
                    props[key] = prop.default_value()
                else:
                    props[key] = None

        snode = cls(**props)
        snode.__node__ = node
        return snode

    @classmethod
    def get_property(cls, name):
        try:
            node_property = getattr(cls, name)
        except AttributeError:
            raise NoSuchProperty(name, cls)
        if not issubclass(node_property.__class__, Property)\
                or not issubclass(node_property.__class__, AliasProperty):
            NoSuchProperty(name, cls)
        return node_property

    @classmethod
    def _class_properties(cls):
        # get all dict values for inherited classes
        # reverse is done to keep inheritance order
        props = {}
        for scls in reversed(cls.mro()):
            for key, value in items(scls.__dict__):
                props[key] = value
        return props
