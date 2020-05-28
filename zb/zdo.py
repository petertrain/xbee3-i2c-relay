import zb.types as t


class SimpleDescriptor(t.Struct):
    _fields = [
        ("endpoint", t.uint8_t),
        ("profile", t.uint16_t),
        ("device_type", t.uint16_t),
        ("device_version", t.uint8_t),
        ("input_clusters", t.LVList(t.uint16_t)),
        ("output_clusters", t.LVList(t.uint16_t)),
    ]


class NodeDescriptor(t.Struct):
    _fields = [
        ("byte1", t.uint8_t),
        ("byte2", t.uint8_t),
        ("mac_capability_flags", t.uint8_t),
        ("manufacturer_code", t.uint16_t),
        ("maximum_buffer_size", t.uint8_t),
        ("maximum_incoming_transfer_size", t.uint16_t),
        ("server_mask", t.uint16_t),
        ("maximum_outgoing_transfer_size", t.uint16_t),
        ("descriptor_capability_field", t.uint8_t),
    ]


class SizePrefixedSimpleDescriptor(SimpleDescriptor):
    def serialize(self):
        data = super().serialize()
        return len(data).to_bytes(1, "little") + data

    @classmethod
    def deserialize(cls, data):
        if not data or data[0] == 0:
            return None, data[1:]
        return super().deserialize(data[1:])


class NWK_T(t.HexRepr, t.uint16_t):
    pass


NWK = ("NWKAddr", NWK_T)
NWKI = ("NWKAddrOfInterest", NWK_T)
IEEE = ("IEEEAddr", t.EUI64_T)
STATUS = ("Status", t.uint8_t)


class Status:
    # The requested operation or transmission was completed successfully.
    SUCCESS = 0x00
    # The supplied request type was invalid.
    INV_REQUESTTYPE = 0x80
    # The requested device did not exist on a device following a child
    # descriptor request to a parent.
    DEVICE_NOT_FOUND = 0x81
    # The supplied endpoint was equal to = 0x00 or between 0xf1 and 0xff.
    INVALID_EP = 0x82
    # The requested endpoint is not described by a simple descriptor.
    NOT_ACTIVE = 0x83
    # The requested optional feature is not supported on the target device.
    NOT_SUPPORTED = 0x84
    # A timeout has occurred with the requested operation.
    TIMEOUT = 0x85
    # The end device bind request was unsuccessful due to a failure to match
    # any suitable clusters.
    NO_MATCH = 0x86
    # The unbind request was unsuccessful due to the coordinator or source
    # device not having an entry in its binding table to unbind.
    NO_ENTRY = 0x88
    # A child descriptor was not available following a discovery request to a
    # parent.
    NO_DESCRIPTOR = 0x89
    # The device does not have storage space to support the requested
    # operation.
    INSUFFICIENT_SPACE = 0x8A
    # The device is not in the proper state to support the requested operation.
    NOT_PERMITTED = 0x8B
    # The device does not have table space to support the operation.
    TABLE_FULL = 0x8C
    # The permissions configuration table on the target indicates that the
    # request is not authorized from this device.
    NOT_AUTHORIZED = 0x8D


class ZDOCmd:
    # Device and Service Discovery Server Requests
    # NWK_addr_req = 0x0000
    # IEEE_addr_req = 0x0001
    # Node_Desc_req = 0x0002
    # Power_Desc_req = 0x0003
    Simple_Desc_req = 0x0004
    Active_EP_req = 0x0005
    # Match_Desc_req = 0x0006
    # Complex_Desc_req = 0x0010
    # User_Desc_req = 0x0011
    # Discovery_Cache_req = 0x0012
    Device_annce = 0x0013
    # User_Desc_set = 0x0014
    # System_Server_Discovery_req = 0x0015
    # Discovery_store_req = 0x0016
    # Node_Desc_store_req = 0x0017
    # Active_EP_store_req = 0x0019
    # Simple_Desc_store_req = 0x001A
    # Remove_node_cache_req = 0x001B
    # Find_node_cache_req = 0x001C
    # Extended_Simple_Desc_req = 0x001D
    # Extended_Active_EP_req = 0x001E
    # Parent_annce = 0x001F
    # #  Bind Management Server Services Responses
    # End_Device_Bind_req = 0x0020
    # Bind_req = 0x0021
    # Unbind_req = 0x0022
    # # Network Management Server Services Requests
    # # ... TODO optional stuff ...
    # Mgmt_Lqi_req = 0x0031
    # Mgmt_Rtg_req = 0x0032
    # # ... TODO optional stuff ...
    # Mgmt_Leave_req = 0x0034
    # Mgmt_Permit_Joining_req = 0x0036
    # Mgmt_NWK_Update_req = 0x0038
    # # ... TODO optional stuff ...
    #
    # # Responses
    # # Device and Service Discovery Server Responses
    # NWK_addr_rsp = 0x8000
    # IEEE_addr_rsp = 0x8001
    # Node_Desc_rsp = 0x8002
    # Power_Desc_rsp = 0x8003
    Simple_Desc_rsp = 0x8004
    Active_EP_rsp = 0x8005
    # Match_Desc_rsp = 0x8006
    # Complex_Desc_rsp = 0x8010
    # User_Desc_rsp = 0x8011
    # Discovery_Cache_rsp = 0x8012
    # User_Desc_conf = 0x8014
    # System_Server_Discovery_rsp = 0x8015
    # Discovery_Store_rsp = 0x8016
    # Node_Desc_store_rsp = 0x8017
    # Power_Desc_store_rsp = 0x8018
    # Active_EP_store_rsp = 0x8019
    # Simple_Desc_store_rsp = 0x801A
    # Remove_node_cache_rsp = 0x801B
    # Find_node_cache_rsp = 0x801C
    # Extended_Simple_Desc_rsp = 0x801D
    # Extended_Active_EP_rsp = 0x801E
    # Parent_annce_rsp = 0x801F
    # #  Bind Management Server Services Responses
    # End_Device_Bind_rsp = 0x8020
    # Bind_rsp = 0x8021
    # Unbind_rsp = 0x8022
    # # ... TODO optional stuff ...
    # # Network Management Server Services Responses
    # Mgmt_Lqi_rsp = 0x8031
    # Mgmt_Rtg_rsp = 0x8032
    # # ... TODO optional stuff ...
    # Mgmt_Leave_rsp = 0x8034
    # Mgmt_Permit_Joining_rsp = 0x8036
    # # ... TODO optional stuff ...
    # Mgmt_NWK_Update_rsp = 0x8038


CLUSTERS = {
    ZDOCmd.Simple_Desc_req: (NWKI, ("EndPoint", t.uint8_t)),
    ZDOCmd.Active_EP_req: (NWKI,),
    # ZDOCmd.NWK_addr_rsp: (
    #     STATUS,
    #     IEEE,
    #     NWK,
    #     ("NumAssocDev", t.Optional(t.uint8_t)),
    #     ("StartIndex", t.Optional(t.uint8_t)),
    #     ("NWKAddressAssocDevList", t.Optional(t.List(NWK))),
    # ),
    # ZDOCmd.IEEE_addr_rsp: (
    #     STATUS,
    #     IEEE,
    #     NWK,
    #     ("NumAssocDev", t.Optional(t.uint8_t)),
    #     ("StartIndex", t.Optional(t.uint8_t)),
    #     ("NWKAddrAssocDevList", t.Optional(t.List(NWK))),
    # ),
    # ZDOCmd.Node_Desc_rsp: (
    #     STATUS,
    #     NWKI,
    #     ("NodeDescriptor", t.Optional(NodeDescriptor)),
    # ),
    ZDOCmd.Device_annce: (NWK, IEEE, ("Capability", t.uint8_t)),
    ZDOCmd.Simple_Desc_rsp: (
        STATUS,
        NWKI,
        ("SimpleDescriptor", t.Optional(SizePrefixedSimpleDescriptor)),
    ),
    ZDOCmd.Active_EP_rsp: (STATUS, NWKI, ("ActiveEPList", t.LVList(t.uint8_t)))
}

# Rewrite to (name, param_names, param_types)
for command_id, schema_template in CLUSTERS.items():
    param_names = [p[0] for p in schema_template]
    param_types = [p[1] for p in schema_template]
    CLUSTERS[command_id] = (param_names, param_types)


def deserialize_frame(cluster_id, data):
    tsn, data = t.uint8_t.deserialize(data)
    try:
        cluster_details = CLUSTERS[cluster_id]
    except KeyError:
        print("Unknown ZDO cluster {:04X}".format(cluster_id))
        return tsn, data

    args, data = t.deserialize_cluster_fields(data, cluster_details[1])
    if data != b"":
        print("Data remains after deserializing ZDO frame")
    return tsn, args


def serialize_frame(tsn, cluster_id, *args):
    tsn_data = t.uint8_t(tsn).serialize()
    schema = CLUSTERS[cluster_id][1]
    data = t.serialize_cluster_fields(args, schema)
    return tsn_data + data


def param_schema(cluster_id, index):
    _param_names, _param_types = CLUSTERS[cluster_id]
    print(_param_names, _param_types)
    return _param_names[index], _param_types[index]
