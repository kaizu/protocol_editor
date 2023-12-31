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
    elif is_union(one):
        return all(_is_acceptable(x, another) for x in one.__args__)
    elif isinstance(one, typing._GenericAlias):
        assert inspect.isclass(one.__origin__) and issubclass(one.__origin__, Entity), f"{one}"

        #XXX:
        if issubclass(one.__origin__, Spread) and another in (Object, Data):
            assert len(one.__args__) == 1
            return _is_acceptable(one.__args__[0], another)

        return issubclass(one.__origin__, another)
    else:
        assert False, f"Never reach here [{type(one)}]"

def is_acceptable(one, another):
    # print(f"is_acceptable: {one}, {another}")
    if inspect.isclass(another):
        assert issubclass(another, Entity)
        return _is_acceptable(one, another)
    elif is_union(another):
        # return any(_is_acceptable(one, x) for x in another.__args__)
        return any(is_acceptable(one, x) for x in another.__args__)
    elif isinstance(another, typing._GenericAlias):
        return (
            isinstance(one, typing._GenericAlias)
            and _is_acceptable(one, another.__origin__)
            and len(one.__args__) == len(another.__args__)
            and all(is_acceptable(x, y) for x, y in zip(one.__args__, another.__args__))
        )
    else:
        assert False, f"Never reach here: {another} ({type(another)})"

class Any(Entity): pass

class Object(Entity): pass

class Data(Entity): pass

class Spread(Entity, typing.Generic[typing.TypeVar("T")]): pass

Any = Object | Data

# Scalar

class Scalar(Data): pass

class Boolean(Scalar): pass

class Integer(Scalar): pass

class Float(Scalar): pass

Real = Integer | Float

class String(Scalar): pass

# Term

class Class(String): pass

class LiquidClass(Class): pass

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

def is_spread(x):
    return isinstance(x, typing._GenericAlias) and x.__origin__ == Spread

def is_array(x):
    return isinstance(x, typing._GenericAlias) and x.__origin__ == Array

#TODO: Only numbers are supported.
_POSSIBLE_TRAITS = (Integer, Float, Array[Integer], Array[Float], Spread[Integer], Spread[Float], Spread[Array[Integer]], Spread[Array[Float]])

def primitive_upper(x, y):
    assert x in _POSSIBLE_TRAITS, x
    assert y in _POSSIBLE_TRAITS, y

    if is_spread(x) or is_spread(y):
        return Spread[primitive_upper(x.__args__[0] if is_spread(x) else x, y.__args__[0] if is_spread(y) else y)]
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
    assert is_acceptable(Array, Any)
    assert is_acceptable(Array, Data)
    assert not is_acceptable(Array, Object)
    assert is_acceptable(Array, ArrayLike)
    assert not is_acceptable(ArrayLike, Array)

    assert is_acceptable(Spread, Spread)
    assert is_acceptable(Spread[Array], Spread)
    assert is_acceptable(Spread[Array], Spread[Array])
    assert is_acceptable(Spread[Array], Spread[ArrayLike])
    assert is_acceptable(Spread[Array], Spread[Array])
    assert is_acceptable(Spread[Array], Data)
    assert is_acceptable(Spread[Plate96], Spread)
    assert is_acceptable(Spread[Plate96], Object)

    assert Spread == Spread
    assert Spread[Float] != Spread
    assert Spread[Float] not in (Spread, )

    # print(Array96, is_category(Array96))
    # print(ArrayLike, is_category(ArrayLike))
    # print(ArrayLike | Tube, is_category(ArrayLike | int))

    # try:
    #     a = Array96()
    # except RuntimeError as err:
    #     print(err.args)

    # print(get_categories())