class int_t(int):  # noqa: N801
    _signed = True

    def serialize(self):
        return self.to_bytes(self._size, "little")
        # return self.to_bytes(self._size, "little", signed=self._signed)

    @classmethod
    def deserialize(cls, data):
        if len(data) < cls._size:
            raise ValueError("Data is too short to contain %d bytes" % cls._size)

        # r = cls.from_bytes(data[: cls._size], "little", signed=cls._signed)
        r = cls.from_bytes(data[: cls._size], "little")
        return r, data[cls._size:]


class uint_t(int_t):  # noqa: N801
    _signed = False


class uint8_t(uint_t):  # noqa: N801
    _size = 1


class uint16_t(uint_t):  # noqa: N801
    _size = 2


class uint32_t(uint_t):  # noqa: N801
    _size = 4


class uint64_t(uint_t):  # noqa: N801
    _size = 8


class _List(list):
    _length = None

    def serialize(self):
        assert self._length is None or len(self) == self._length
        return b"".join([self._itemtype(i).serialize() for i in self])

    @classmethod
    def deserialize(cls, data):
        r = cls()
        while data:
            item, data = r._itemtype.deserialize(data)
            r.append(item)
        return r, data


class _LVList(_List):
    _prefix_length = 1

    def serialize(self):
        head = len(self).to_bytes(self._prefix_length, "little")
        data = super().serialize()
        return head + data

    @classmethod
    def deserialize(cls, data):
        r = cls()

        if len(data) < cls._prefix_length:
            raise ValueError("Data is too short")

        length = int.from_bytes(data[: cls._prefix_length], "little")
        data = data[cls._prefix_length:]
        for i in range(length):
            item, data = r._itemtype.deserialize(data)
            r.append(item)
        return r, data


def List(itemtype):  # noqa: N802
    class List(_List):
        _itemtype = itemtype

    return List


def LVList(itemtype, prefix_length=1):  # noqa: N802
    class LVList(_LVList):
        _itemtype = itemtype
        _prefix_length = prefix_length

    return LVList


class _FixedList(_List):
    @classmethod
    def deserialize(cls, data):
        r = cls()
        for i in range(r._length):
            item, data = r._itemtype.deserialize(data)
            r.append(item)
        return r, data


def fixed_list(length, itemtype):
    class FixedList(_FixedList):
        _length = length
        _itemtype = itemtype

    return FixedList


def Optional(optional_item_type):
    class Optional(optional_item_type):
        optional = True

        @classmethod
        def deserialize(cls, data):
            try:
                return super().deserialize(data)
            except ValueError:
                return None, b""

    return Optional


class EUI64_T(fixed_list(8, uint8_t)):
    # EUI 64-bit ID (an IEEE address).
    def __repr__(self):
        return ":".join("%02x" % i for i in self[::-1])

    def __hash__(self):
        return hash(repr(self))

    @classmethod
    def convert(cls, ieee: str):
        if ieee is None:
            return None
        ieee = [uint8_t(p, 16) for p in ieee.split(":")[::-1]]
        assert len(ieee) == cls._length
        return cls(ieee)


class HexRepr:
    def __repr__(self):
        return ("0x{:0" + str(self._size * 2) + "x}").format(self)

    def __str__(self):
        return ("0x{:0" + str(self._size * 2) + "x}").format(self)


class Struct:
    def __init__(self, *args, **kwargs):
        print('*******************************\n__init__ called with args ', args)
        print(self.__class__)
        print(type(args[0]))
        print(len(args))
        if len(args) == 1 and isinstance(args[0], self.__class__):
            print('copy constructor called')
            # copy constructor
            for field in self._fields:
                setattr(self, field[0], getattr(args[0], field[0]))
        elif len(args) == len(self._fields):
            print('standard constructor called')
            for field, value in zip(self._fields, args):
                setattr(self, field[0], field[1](value))
        elif not args:
            print('constructor called without args')
            for field in self._fields:
                setattr(self, field[0], None)
        print('*******************************\nexiting __init__')

    def serialize(self):
        print(self)
        r = b""
        for field in self._fields:
            r += getattr(self, field[0]).serialize()
        return r

    @classmethod
    def deserialize(cls, data):
        args = []
        for field_name, field_type in cls._fields:
            v, data = field_type.deserialize(data)
            args.append(v)
            # setattr(r, field_name, v)
        r = cls(*args)
        return r, data

    def __repr__(self):
        r = "<%s " % (self.__class__.__name__,)
        r += " ".join(
            ["%s=%s" % (f[0], getattr(self, f[0], None)) for f in self._fields]
        )
        r += ">"
        return r


def deserialize_cluster_fields(data, schema):
    result = []
    for type_ in schema:
        print(type_)
        value, data = type_.deserialize(data)
        result.append(value)
    return result, data


def serialize_cluster_fields(data, schema):
    # print(schema)
    # print(data)
    # print([zip(schema, data)])
    return b"".join(t(*v).serialize() for t, v in zip(schema, data))