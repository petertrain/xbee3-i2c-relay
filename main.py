import time
import xbee
from machine import Pin, I2C

import zb.zdo as zdo
import zb.zha as zha

import struct

print(" +-------------------------------------+")
print(" |          i2crelay                   |")
print(" +-------------------------------------+\n")

print("Waiting for data...\n")

btn = Pin(Pin.board.D4, Pin.IN)
last_button_state = 1

i2c = I2C(1)

CMD_CHANNEL_CTRL = 0x10
relay_state = 0x0
base_ep = 0xc0
relay_count = 4

serial_h = struct.unpack('I', xbee.atcmd('SH'))[0]
serial_l = struct.unpack('I', xbee.atcmd('SL'))[0]

capability_flags = 0x8E

reporting_tsn = 0

heartbeat_timeout = 300000


def print_message(message):
    print("Data received from {} >>".format(''.join('{:02x}'.format(x).upper() for x in message['sender_eui64'])))
    print("cluster: {0:X}".format(message['cluster']))
    print("dest_ep: {}".format(message['dest_ep']))
    print("source_ep: {}".format(message['source_ep']))
    print("payload: {}".format(message['payload']))
    print("profile: {}".format(message['profile']))
    print("broadcast: {}".format(message['broadcast']))
    print("sender_nwk: {}".format(message['sender_nwk']))
    print("sender_eui64: {}".format(message['sender_eui64']))


def handle_zdo_message(message):
    tsn, args = zdo.deserialize_frame(message['cluster'], message['payload'])
    print("ZDO request cluster {:04X}, args: ".format(message['cluster']), args)
    if message['cluster'] == zdo.ZDOCmd.Active_EP_req:
        if args[0] == xbee.atcmd('MY'):
            response_frame = zdo.serialize_frame(tsn, zdo.ZDOCmd.Active_EP_rsp, (zdo.Status.SUCCESS,), (args[0],),
                                                 ([base_ep + r for r in range(relay_count)],))
            xbee.transmit(message['sender_eui64'], response_frame,
                          source_ep=message['source_ep'], dest_ep=message['dest_ep'],
                          cluster=zdo.ZDOCmd.Active_EP_rsp, profile=message['profile'])
    elif message['cluster'] == zdo.ZDOCmd.Simple_Desc_req:
        if args[0] == xbee.atcmd('MY'):
            # n, t = param_schema(ZDOCmd.Simple_Desc_rsp, 2)
            # print(n, t)

            response_frame = zdo.serialize_frame(tsn, zdo.ZDOCmd.Simple_Desc_rsp,
                                                 (zdo.Status.SUCCESS,),
                                                 (args[0],),
                                                 (args[1], 260, 0x0, 0x0, [0x6], []))
            xbee.transmit(message['sender_eui64'], response_frame,
                          source_ep=message['source_ep'], dest_ep=message['dest_ep'],
                          cluster=zdo.ZDOCmd.Simple_Desc_rsp, profile=message['profile'])

    else:
        print("No handler for ZDO message:")
        print_message(message)


def set_relays():
    cmd_bytes = struct.pack("BB", CMD_CHANNEL_CTRL, relay_state)

    i2c.writeto(17, cmd_bytes)


def handle_zha_message(message):
    frc, tsn, command_id, args, data = zha.deserialize_frame(message['cluster'], message['payload'])
    # print(frc, tsn, command_id, args, data)
    if message['cluster'] == 6:  # on off switch
        relay_id = message['dest_ep'] - 0xc0
        if frc.frame_type == zha.FrameType.CLUSTER_COMMAND:
            cmd_string = zha.on_off_server_commands[command_id]
            global relay_state

            if command_id == 0:
                relay_state &= ~(1 << relay_id)
            elif command_id == 1:
                relay_state |= (1 << relay_id)

            set_relays()
            print('executing {} against relay_id {}'.format(cmd_string, relay_id))
            publish_relay_state(relay_id)
        elif frc.frame_type == zha.FrameType.GLOBAL_COMMAND:
            if command_id == 0:
                response_frame = zha.serialize_attribute_response(tsn, relay_id, args[0])
                xbee.transmit(message['sender_eui64'], response_frame,
                              source_ep=message['source_ep'], dest_ep=message['dest_ep'],
                              cluster=zdo.ZDOCmd.Simple_Desc_rsp, profile=message['profile'])
            elif command_id == 0x0b:    # default response to report attributes
                print('Attribute report resulted in response status {}'.format(args[1]))


def publish_relay_state(relay_id):
    _ai = xbee.atcmd('AI')
    if _ai != 0:
        print('publish_relay_state: Not associated to a PAN (current state is {}.  Cannot publish'.format(
            _ai))
        return

    global reporting_tsn
    state = True if relay_state & (1 << relay_id) else False
    msg = zha.serialize_on_off_report(reporting_tsn & 0xFF, state)
    reporting_tsn += 1
    ep = relay_id + base_ep
    xbee.transmit(xbee.ADDR_COORDINATOR, msg,
                  source_ep=ep, dest_ep=ep,
                  cluster=0x0006, profile=260)


set_relays()
for r in range(relay_count):
    publish_relay_state(r)
heartbeat_time = time.ticks_ms()

while True:
    # Check if the XBee has any messages in the queue.
    received_msg = xbee.receive()
    if received_msg:
        ai = xbee.atcmd('AI')
        if ai != 0:
            print('handle message: Not associated to a PAN (current state is {}.  Cannot handle message'.format(ai))
        else:
            # print_message(received_msg)
            if received_msg['profile'] == 0 and received_msg['dest_ep'] == 0:
                handle_zdo_message(received_msg)
            elif received_msg['profile'] == 260:  # zha profile
                handle_zha_message(received_msg)
            else:
                print("No handler for message:")
                print_message(received_msg)
    else:
        now = time.ticks_ms()
        delta = time.ticks_diff(now, heartbeat_time)
        if delta >= heartbeat_timeout:
            heartbeat_time = now
            for r in range(relay_count):
                publish_relay_state(r)
        time.sleep(0.1)

