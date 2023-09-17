#!/usr/bin/python
# -*- coding: utf-8 -*-
from logging import getLogger

logger = getLogger(__name__)

import inspect
import types
import typing
import importlib
import itertools
import functools


class _EntityMeta(type):
    
    def __instancecheck__(self, obj):
        # if self is Any:
        #     raise TypeError("Entity cannot be used with isinstance()")
        return super().__instancecheck__(obj)

    def __repr__(self):
        return f'{self.__module__}.{self.__qualname__}'
        # return super().__repr__()  # respect to subclasses

class Entity(metaclass=_EntityMeta): pass

def is_category(cls):
    if inspect.isclass(cls):
        if issubclass(cls, Entity):
            return True
    elif isinstance(cls, types.UnionType):
        if all(is_category(x) for x in cls.__args__):
            return True
    elif isinstance(cls, typing._GenericAlias):
        if inspect.isclass(cls.__origin__) and issubclass(cls.__origin__, Entity) and all(is_category(x) for x in cls.__args__):
            return True
    return False

def _is_acceptable(one, another):
    # print(f"_is_acceptable: {one}, {another}")
    assert inspect.isclass(another)
    if inspect.isclass(one):
        assert issubclass(one, Entity)
        return issubclass(one, another)
    elif isinstance(one, types.UnionType) or isinstance(one, typing._UnionGenericAlias):
        return all(_is_acceptable(x, another) for x in one.__args__)
    elif isinstance(one, typing._GenericAlias):
        assert inspect.isclass(one.__origin__) and issubclass(one.__origin__, Entity), f"{one}"
        return issubclass(one.__origin__, another)
    else:
        assert False, f"Never reach here [{type(one)}]"

def is_acceptable(one, another):
    # print(f"is_acceptable: {one}, {another}")
    if inspect.isclass(another):
        assert issubclass(another, Entity)
        return _is_acceptable(one, another)
    elif isinstance(another, types.UnionType) or isinstance(another, typing._UnionGenericAlias):
        # return any(_is_acceptable(one, x) for x in another.__args__)
        return any(is_acceptable(one, x) for x in another.__args__)
    elif isinstance(another, typing._GenericAlias):
        if isinstance(one, typing._GenericAlias):
            return (
                _is_acceptable(one, another.__origin__)
                and len(one.__args__) == len(another.__args__)
                and all(is_acceptable(x, y) for x, y in zip(one.__args__, another.__args__))
            )
        else:
            return False
    else:
        assert False, f"Never reach here: {another} ({type(another)})"

class Any(Entity): pass

class Object(Any): pass

class Data(Any): pass

# _Spread

class _Spread(Entity): pass

class Group(Data, _Spread, typing.Generic[typing.TypeVar("T")]): pass

class ObjectGroup(Object, _Spread, typing.Generic[typing.TypeVar("T")]): pass

# Scalar

class Scalar(Data): pass

class Integer(Scalar): pass

class Float(Scalar): pass

Real = Integer | Float

# Array

class Array(Data, typing.Generic[typing.TypeVar("T")]): pass

# Labware

class Labware(Object): pass

class Tube(Labware): pass

class Tube5(Tube): pass

class Plate(Labware): pass

class Plate96(Plate): pass

ArrayLike = Plate96 | Array  # deprecated

def first_arg(x):
    assert isinstance(x, typing._GenericAlias)
    return x.__args__[0]

def is_union(x):
    return isinstance(x, types.UnionType) or isinstance(x, typing._UnionGenericAlias)

def is_group(x):
    return isinstance(x, typing._GenericAlias) and x.__origin__ == Group

def is_array(x):
    return isinstance(x, typing._GenericAlias) and x.__origin__ == Array

#TODO: Only numbers are supported.
_POSSIBLE_TRAITS = (Integer, Float, Array[Integer], Array[Float], Group[Integer], Group[Float], Group[Array[Integer]], Group[Array[Float]])

def primitive_upper(x, y):
    assert x in _POSSIBLE_TRAITS, x
    assert y in _POSSIBLE_TRAITS, y

    if is_group(x) or is_group(y):
        return Group[primitive_upper(x.__args__[0] if is_group(x) else x, y.__args__[0] if is_group(y) else y)]
    elif is_array(x) or is_array(y):
        return Array[primitive_upper(x.__args__[0] if is_array(x) else x, y.__args__[0] if is_array(y) else y)]
    elif x == Float or y == Float:
        return Float
    else:
        assert x == Integer, x
        assert y == Integer, y
        return Integer

def expand_to_primitives(x):
    a = tuple(y for y in _POSSIBLE_TRAITS if is_acceptable(y, x))
    assert len(a) > 0, x
    return a

def _upper(x, y):
    assert isinstance(x, tuple)
    assert isinstance(y, tuple)
    a = tuple(set(primitive_upper(x_, y_) for x_, y_ in itertools.product(x, y)))
    assert len(a) > 0, f"upper: {x}, {y}"
    # print(f"upper: {x}, {y}, {a} ({len(a)})")
    return a

def upper(*traits):
    assert len(traits) > 0
    a = tuple(functools.reduce(_upper, (expand_to_primitives(x) for x in traits)))
    if len(a) == 1:
        return a[0]
    return typing.Union[a]

def get_categories():
    return {
        key: value
        for key, value in inspect.getmembers(importlib.import_module(__name__))
        if is_category(value)
    }

if __name__ == "__main__":
    print(is_acceptable(Array, Any))
    print(is_acceptable(Array, Data))
    print(is_acceptable(Array, Object))
    print(is_acceptable(Array, ArrayLike))
    print(is_acceptable(ArrayLike, Array))

    print(is_acceptable(Group[Array], Group))
    print(is_acceptable(Group[Array], Group[Array]))
    print(is_acceptable(Group[Array], Group[ArrayLike]))
    print(is_acceptable(Group[Array], Group[Array]))
    print(is_acceptable(Group, Group))

    print(is_acceptable(ObjectGroup[Plate96], _Spread))
    print(is_acceptable(ObjectGroup[Plate96], Object))

    print(Group == Group)
    print(Group[Float] == Group)
    print(Group[Float] in (Group, ))

    # print(Array96, is_category(Array96))
    # print(ArrayLike, is_category(ArrayLike))
    # print(ArrayLike | Tube, is_category(ArrayLike | int))

    # try:
    #     a = Array96()
    # except RuntimeError as err:
    #     print(err.args)

    # print(get_categories())