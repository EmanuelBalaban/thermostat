import math

class GasSensorType:
    def __init__(self, key, a, b):
        self.key = key
        self.a = a
        self.b = b

    def calculate_ppm(self, rs_ro_ratio: float):
        return 10 ** (self.a * math.log10(rs_ro_ratio) + self.b)
    
    def mqtt_id(self):
        return f'kitchen_{self.key.lower()}_sensor'

    def state_topic(self) -> bytes:
        return f'home/kitchen/gas/{self.key.lower()}'.encode()

    def discovery_topic(self) -> bytes:
        return f'homeassistant/sensor/{self.mqtt_id()}/config'.encode()
    
    def discovery_payload(self, device) -> dict:
        id = self.mqtt_id()

        payload = {
            'device': device,
            'object_id': id,
            'unique_id': id,
            'platform': 'sensor',
            'state_class': 'measurement',
            'name': f'{self.key} Gas Sensor',
            'state_topic': self.state_topic(),
            'suggested_display_precision': 2,
            'unit_of_measurement': 'ppm',
            'expire_after': 60,
        }

        if self.key == 'CO':
            payload['device_class'] = 'carbon_monoxide'

        return payload