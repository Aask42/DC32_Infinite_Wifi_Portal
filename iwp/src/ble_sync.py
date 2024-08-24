from micropython import const
import bluetooth
import struct

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_MANUFACTURER = const(0xFF)

class BLESync:
    def __init__(self, name, frame_callback):
        self.name = name
        self.frame_callback = frame_callback
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._connections = set()
        self._payload = self._advertising_payload(name=self.name)
        self._advertise()
        self._frame_num = 0

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._connections.add(conn_handle)
            print("Connected:", addr)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            self._connections.remove(conn_handle)
            self._advertise()
            print("Disconnected:", addr)
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            # Handle incoming data if necessary

    def _advertising_payload(self, name=None):
        payload = bytearray()
        payload.extend(struct.pack("BB", 2, _ADV_TYPE_FLAGS))
        payload.extend(struct.pack("BB", 0x06, _ADV_TYPE_FLAGS))
        if name:
            payload.extend(struct.pack("BB", len(name) + 1, _ADV_TYPE_NAME) + name.encode())
        return payload

    def _advertise(self):
        self._ble.gap_advertise(100_000, adv_data=self._payload)

    def sync_frames(self, t):
        self._frame_num += 1
        payload = self._payload + struct.pack("BB", _ADV_TYPE_MANUFACTURER, self._frame_num)
        self._ble.gap_advertise(100_000, adv_data=payload)
        self.frame_callback(self._frame_num)

    def get_frame_num(self):
        return self._frame_num
