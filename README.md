# xbee3-i2c-relay
Control multiple relays via i2c using micropython on the XBee3

Configures XBee to act as a simple on off for 4 / 8 endpoints via zdo.
The on off commands drive relays on a [Grove 4 / 8 channel SPDT relay via i2c](https://wiki.seeedstudio.com/Grove-4-Channel_SPDT_Relay/)

Ported a fair amount of code from [zigpy](https://github.com/zigpy/zigpy) to assist with handling of zigbee protocol.