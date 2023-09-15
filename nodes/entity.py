import inspect
import types
import typing
import importlib

class Entity:

    def __new__(cls, *args, **kwargs):
        raise RuntimeError("Do not instantiate.")

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
        assert isinstance(one, typing._GenericAlias)
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
        assert False, "Never reach here"

is_subclass_of = is_acceptable
# def is_subclass_of(one, another):
#     if not isinstance(another, typing._GenericAlias):
#         if inspect.isclass(one):
#             assert issubclass(one, Entity)
#             return issubclass(one, another)
#         elif isinstance(one, types.UnionType):
#             return all(issubclass(x, another) for x in one.__args__)
#         else:
#             assert isinstance(one, typing._GenericAlias)
#             return issubclass(one.__origin__, another)
#     else:
#         if inspect.isclass(one):
#             assert issubclass(one, Entity)
#             raise NotImplementedError()
#         elif isinstance(one, types.UnionType):
#             raise NotImplementedError()
#         else:
#             assert isinstance(one, typing._GenericAlias)
#             raise NotImplementedError()

class Any(Entity): pass

class Data(Any): pass

class Group(Data, typing.Generic[typing.TypeVar("T")]): pass

class Scalar(Data): pass

class Object(Any): pass

class Tube(Object): pass

class Plate(Object): pass

class Plate96(Plate): pass

class Integer(Scalar): pass

class Float(Scalar): pass

class Array(Data, typing.Generic[typing.TypeVar("T")]): pass

# class Array96(Array): pass

ArrayLike = Plate96 | Array
Real = Integer | Float

def integer_or_float(*types):
    assert len(types) > 0
    for x in types:
        if x == Float:
            return Float
        assert x == Integer
    return Integer

def get_categories():
    return {
        key: value
        for key, value in inspect.getmembers(importlib.import_module(__name__))
        if is_category(value)
    }

if __name__ == "__main__":
    print(is_subclass_of(Array, Any))
    print(is_subclass_of(Array, Data))
    print(is_subclass_of(Array, Object))
    print(is_subclass_of(Array, ArrayLike))
    print(is_subclass_of(ArrayLike, Array))

    print(is_subclass_of(Group[Array], Group))
    print(is_subclass_of(Group[Array], Group[Array]))
    print(is_subclass_of(Group[Array], Group[ArrayLike]))
    print(is_subclass_of(Group[Array], Group[Array]))
    print(is_subclass_of(Group, Group))

    # print(Array96, is_category(Array96))
    # print(ArrayLike, is_category(ArrayLike))
    # print(ArrayLike | Tube, is_category(ArrayLike | int))

    # try:
    #     a = Array96()
    # except RuntimeError as err:
    #     print(err.args)

    # print(get_categories())