import inspect
import types
import importlib

class Entity:

    def __new__(cls, *args, **kwargs):
        raise RuntimeError("Do not instantiate.")

def is_category(cls):
    if inspect.isclass(cls):
        if issubclass(cls, Entity):
            return True
    elif isinstance(cls, types.UnionType):
        if all(issubclass(x, Entity) for x in cls.__args__):
            return True
    return False

def is_subclass_of(one, another):
    if inspect.isclass(one):
        assert issubclass(one, Entity)
        return issubclass(one, another)
    else:
        assert isinstance(one, types.UnionType)
        return all(issubclass(x, another) for x in one.__args__)

class Any(Entity): pass

class Data(Any): pass

class Object(Any): pass

class Tube(Object): pass

class Plate(Object): pass

class Plate96(Plate): pass

class Array(Data): pass

class Array96(Array): pass

ArrayLike = Plate96 | Array

def get_categories():
    return {
        key: value
        for key, value in inspect.getmembers(importlib.import_module(__name__))
        if is_category(value)
    }

if __name__ == "__main__":
    print(is_subclass_of(Array96, Any))
    print(is_subclass_of(Array96, Data))
    print(is_subclass_of(Array96, Object))
    print(is_subclass_of(Array96, ArrayLike))
    print(is_subclass_of(ArrayLike, Array))

    print(Array96, is_category(Array96))
    print(ArrayLike, is_category(ArrayLike))
    print(ArrayLike | Tube, is_category(ArrayLike | int))

    try:
        a = Array96()
    except RuntimeError as err:
        print(err.args)

    print(get_categories())