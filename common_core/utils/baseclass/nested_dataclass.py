from dataclasses import (
    dataclass, make_dataclass, field, fields, InitVar)

"""
Nested Dataclass is a factory function that programmatically creates a 
dataclass of exclusive statically-typed fields that has the ability to nest 
other dataclasses within it similar to a doubly-linked list.  

Methods:
- `add_child(str)`: Adds a child dataclass to the parent dataclass.
- `get_child(str, *{str, str, str...})`: Returns the child dataclass instance.
- 'delete_child(str)': Deletes the dataclass instance. (All children are also deleted)
- 'reset(cascade: bool)': Resets the dataclass instance to its default values. 
                            cascade=False (default)Children are NOT reset
                            cascade=True Children are reset to their default values.

Attributes:
- `asdict`: Returns the dataclass instance as a dictionary.
- `children`: Returns a list of the children dataclass names.

Overridden Dunder Methods:
- `__setattr__()`: Prevents the addition of new fields to the dataclass 
                    instance. Also enforces that a new value for a field 
                    must be of the same type as the default value.
- '__getattr__(key)': Checks to see if the key is a child dataclass 
                    name; if so, returns the child dataclass instance.
                    
Ex:
# `fields` is a dictionary of the fields to be created with their default values.
# Future fields cannot be added to the dataclass instance after creation.
# Changing the value of a field is allowed, but must be of the same type.
fields = {      
    'metafield1': False
    'metafield2': False
    'metafield3': False
}
# `main` is a dataclass instance with the fields
name = 'Main'
main = nested_dataclass_factory(name, fields)  
main.metafield1 = True
print(main.asdict)  # {'metafield1': True, 'metafield2': False, 'metafield3': False}
main._name = 'New Name'  # Raises an exception
print(main._name)  # 'Main'

main.add_child('child1')
main.child1.metafield2 = True
print(main.asdict)  # {'metafield1': True, 
                       'metafield2': False, 
                       'metafield3': False, 
                       'child1': {
                            'metafield1': False,
                            'metafield2': True, 
                            'metafield3': False}
                        }
main.add_child('child2')
main.child2.metafield3 = True
print(main.children)  # ['child1', 'child2']

child = main.get_child('child2')
child.metafield1 = True
child.add_child('grandchild1')
child.grandchild1.metafield2 = True
print(main.asdict)  # {'metafield1': True, 
                       'metafield2': False, 
                       'metafield3': False, 
                       'child1': {
                            'metafield1': False,
                            'metafield2': True, 
                            'metafield3': False},
                       'child2': {
                            'metafield1': True,
                            'metafield2': False,
                            'metafield3': True,
                            'grandchild1': {
                                'metafield1': False,
                                'metafield2': True,
                                'metafield3': False}
                            }
                        }
child = main.get_child('child2', 'grandchild1') # Returns the grandchild1 instance
child = main.get_child('child5') # Raises an exception
child = main.get_child('child5', auto_create=True) # Creates a new child5 instance
print(main.children)  # ['child1', 'child2', 'child5']

gchild = main.get_child('child2', 'grandchild1')
gchild.path = ['child2', 'grandchild1']

main.add_child('child1') # Raises an exception (Duplicate child name)
main.add_child('child1', force=True) # Overwrites the existing child1 instance

print(main.child2.grandchild1.asdict)  # {'metafield1': False, 
                                            'metafield2': True, 
                                            'metafield3': False}   
"""


ERR_PFX = "NestedDataclassError: "


class NestedDataclassError:
    DUPLICATE_CHILD = (ERR_PFX + "Child `{0}` already exists.")
    CHILD_NOT_FOUND = (ERR_PFX + "Child `{0}` not found.")
    FIELD_NOT_FOUND = (ERR_PFX + "Field `{0}` not found.")
    FIELD_TYPE_MISMATCH = (ERR_PFX + "Field `{0}` must be of type {1}. Got {2} instead.")
    MISSING_CHILD = (ERR_PFX + "get_child() - At least one child name must be provided.")


def nested_dataclass_factory(name: str, field_dct: dict, parent=None):
    fields = []
    for field_name, field_value in field_dct.items():
        fields.append((field_name, type(field_value), field(default=field_value)))
    return make_dataclass(name, fields=fields, bases=(BaseNestedDataclass,))(_parent=parent)


@dataclass
class BaseNestedDataclass:
    _parent: InitVar

    def __post_init__(self, _parent=None):
        self._parent = _parent
        self._children = {}
        self._initialized = True

    @property
    def _name(self):
        return self.__class__.__name__

    @property
    def _fields(self):
        return fields(self)

    @property
    def asdict(self):
        dct = {f.name: getattr(self, f.name) for f in self._fields}
        for child_name, child in self._children.items():
            dct[child_name] = child.asdict
        return dct

    @property
    def children(self):
        return list(self._children.keys())

    @staticmethod
    def get_mro_keys(klass, reverse=True):
        """Returns a list of the class names in the MRO of the class."""
        # The MRO names can be used as keys in nesting the dataclasses
        # if the nested dictionary is meant to mimic a class hierarchy.
        if mro := getattr(klass, '__mro__', None):
            if reverse:
                return list(reversed([k.__name__ for k in mro if k != object]))
            return [k.__name__ for k in mro if k != object]

    def add_child(self, child_name: str, force=False):
        if child_name in self._children and not force:
            raise KeyError(NestedDataclassError.DUPLICATE_CHILD.format(child_name))
        cfields = {f.name: f.default for f in self._fields}
        child = nested_dataclass_factory(child_name, cfields, parent=self)
        self._children[child_name] = child

    def get_child(self, *child_names, auto_create=False):
        if not child_names:
            raise ValueError(NestedDataclassError.MISSING_CHILD)
        child_name, child_names = child_names[0], child_names[1:]
        if child_name not in self._children and auto_create:
            self.add_child(child_name)
        elif child_name not in self._children:
            raise KeyError(NestedDataclassError.CHILD_NOT_FOUND.format(child_name))
        child = self._children[child_name]
        if child_names:
            return child.get_child(*child_names, auto_create=auto_create)
        return child

    def delete_child(self, child_name):
        if child_name in self._children:
            del self._children[child_name]

    def reset(self, cascade=False):
        for f in self._fields:
            setattr(self, f.name, f.default)
        if cascade:
            for child in self._children.values():
                child.reset(cascade)

    def __setattr__(self, key, value):
        if getattr(self, '_initialized', False):
            if key not in [f.name for f in self._fields]:
                raise KeyError(NestedDataclassError.FIELD_NOT_FOUND.format(key))
            if not isinstance(value, type(getattr(self, key))):
                raise TypeError(NestedDataclassError.FIELD_TYPE_MISMATCH.format(
                    key, type(getattr(self, key)), type(value)))
        super().__setattr__(key, value)

    def __getattr__(self, key):
        if key != '_children' and key in self._children:
            return self._children[key]
        return super().__getattr__(key)
