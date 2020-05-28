import zb.types as t


class FrameType:
    """ZCL Frame Type."""

    GLOBAL_COMMAND = 0b00
    CLUSTER_COMMAND = 0b01
    RESERVED_2 = 0b10
    RESERVED_3 = 0b11


class FrameControl:
    """The frame control field contains information defining the command type
     and other control flags."""

    def __init__(self, frame_control: int = 0x00) -> None:
        self.value = frame_control

    @property
    def disable_default_response(self) -> bool:
        """Return True if default response is disabled."""
        return bool(self.value & 0b10000)

    @disable_default_response.setter
    def disable_default_response(self, value: bool) -> None:
        """Disable the default response."""
        if value:
            self.value |= 0b10000
            return
        self.value &= 0b11101111

    @property
    def frame_type(self) -> FrameType:
        """Return frame type."""
        return self.value & 0b00000011

    @frame_type.setter
    def frame_type(self, value) -> None:
        """Sets frame type to Global general command."""
        self.value &= 0b11111100
        self.value |= value

    @property
    def is_cluster(self) -> bool:
        """Return True if command is a local cluster specific command."""
        return bool(self.frame_type == FrameType.CLUSTER_COMMAND)

    @property
    def is_general(self) -> bool:
        """Return True if command is a global ZCL command."""
        return bool(self.frame_type == FrameType.GLOBAL_COMMAND)

    @property
    def is_manufacturer_specific(self) -> bool:
        """Return True if manufacturer code is present."""
        return bool(self.value & 0b100)

    @is_manufacturer_specific.setter
    def is_manufacturer_specific(self, value: bool) -> None:
        """Sets manufacturer specific code."""
        if value:
            self.value |= 0b100
            return
        self.value &= 0b11111011

    @property
    def is_reply(self) -> bool:
        """Return True if is a reply (server cluster -> client cluster."""
        return bool(self.value & 0b1000)

    # in ZCL specs the above is the "direction" field
    direction = is_reply

    @is_reply.setter
    def is_reply(self, value: bool) -> None:
        """Sets the direction."""
        if value:
            self.value |= 0b1000
            return
        self.value &= 0b11110111

    def __repr__(self) -> str:
        """Representation."""
        return (
            "<{} frame_type={} manufacturer_specific={} is_reply={} "
            "disable_default_response={}>"
        ).format(
            self.__class__.__name__,
            self.frame_type,
            self.is_manufacturer_specific,
            self.is_reply,
            self.disable_default_response,
        )

    def serialize(self) -> bytes:
        return t.uint8_t(self.value).serialize()

    @classmethod
    def cluster(cls, is_reply: bool = False):
        """New Local Cluster specific command frame control."""
        r = cls(FrameType.CLUSTER_COMMAND)
        r.is_reply = is_reply
        if is_reply:
            r.disable_default_response = True
        return r

    @classmethod
    def deserialize(cls, data):
        frc, data = t.uint8_t.deserialize(data)
        return cls(frc), data

    @classmethod
    def general(cls, is_reply: bool = False):
        """New General ZCL command frame control."""
        r = cls(FrameType.GLOBAL_COMMAND)
        r.is_reply = is_reply
        if is_reply:
            r.disable_default_response = True
        return r


on_off_attributes = {
    0x0000: ("on_off", t.uint8_t),
    0x4000: ("global_scene_control", t.uint8_t),
    0x4001: ("on_time", t.uint16_t),
    0x4002: ("off_wait_time", t.uint16_t),
}

on_off_server_commands = {
    0x0000: ("off", (), False),
    0x0001: ("on", (), False),
    0x0002: ("toggle", (), False),
    0x0040: ("off_with_effect", (t.uint8_t, t.uint8_t), False),
    0x0041: ("on_with_recall_global_scene", (), False),
    0x0042: ("on_with_timed_off", (t.uint8_t, t.uint16_t, t.uint16_t), False),
}


def deserialize_frame(cluster_id, data):
    frc, data = FrameControl.deserialize(data)

    if frc.is_manufacturer_specific:
        manufacturer, data = t.uint16_t.deserialize(data)
    tsn, data = t.uint8_t.deserialize(data)
    command_id, data = t.uint8_t.deserialize(data)

    if frc.frame_type == FrameType.CLUSTER_COMMAND:
        if frc.is_reply:
            print('No zha client commands implemented')
            schema = ()
        else:
            schema = on_off_server_commands[command_id][1]  # Only on off switch commands are implemented
    elif frc.frame_type == FrameType.GLOBAL_COMMAND:
        if command_id == 0x0:       # Read attributes request
            schema = (t.List(t.uint16_t),)
        elif command_id == 0x0b:    # default response to report attributes
            schema = (t.uint8_t,)
        else:
            print('General command {:02X} is not implemented'.format(command_id))
            schema = ()
    else:
        print('Reserved type not implemented')

    args, data = t.deserialize_cluster_fields(data, schema)
    if data != b"":
        print("Data remains after deserializing ZCL frame")

    return frc, tsn, command_id, args, data


def serialize_on_off_report(tsn, on):
    frc = FrameControl.general()
    frc.disable_default_response = True
    attribute_id = t.uint16_t(0x000)  # on off attribute id
    attribute_type = t.uint8_t(0x10)  # boolean type id
    attribute_value = t.uint8_t(1 if on else 0)

    attribute_data = attribute_id.serialize() + attribute_type.serialize() + attribute_value.serialize()
    return frc.serialize() + t.uint8_t(tsn).serialize() + t.uint8_t(0x0A).serialize() + attribute_data


def serialize_attribute_response(tsn, on, attributes):
    frc = FrameControl.general()

    data = frc.serialize() + t.uint8_t(tsn).serialize() + t.uint8_t(0x01).serialize()
    for attribute in attributes:
        attribute_id = t.uint16_t(attribute)  # on off attribute id
        if attribute == 0x000:
            attribute_status = t.uint8_t(0x00)
            attribute_type = t.uint8_t(0x10)  # boolean type id
            attribute_value = t.uint8_t(1 if on else 0)

            attribute_data = attribute_id.serialize() + attribute_status.serialize() + \
                             attribute_type.serialize() + attribute_value.serialize()

            data += attribute_data
        else:
            attribute_status = t.uint8_t(0x86)      # Attribute not supported

            attribute_data = attribute_id.serialize() + attribute_status.serialize()
            data += attribute_data

    return data
