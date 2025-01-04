import asyncio, urequests, machine, neopixel
from urequests import Response

import config

relay_state = False
gas_detected = False

neo_pixel_pin = 1
relay_pin = 10
gas_sensor_pin = 4

gas_sensor = machine.ADC(machine.Pin(gas_sensor_pin, machine.Pin.IN))
relay = machine.Pin(relay_pin, machine.Pin.OUT)
np = neopixel.NeoPixel(machine.Pin(neo_pixel_pin, machine.Pin.OUT), 1)


async def main():
    relay.off()
    np[0] = set_brightness((0, 0, 0), 0.0)  # Black
    np.write()

    asyncio.create_task(watch_state())
    asyncio.create_task(monitor_gas_sensor())

    while True:
        await asyncio.sleep(1)


async def watch_state():
    global relay_state

    endpoint = f'{config.API_URL}/state/relay_state'

    while True:
        try:
            response: Response = urequests.get(endpoint)
            new_relay_state = response.json()

            if relay_state != new_relay_state:
                relay_state = new_relay_state
                react_to_relay_state()
        except Exception as e:
            print(f"Error fetching relay_state: {e}")

        # Request state every X seconds
        await asyncio.sleep(config.STATE_POLL_TIME)


async def monitor_gas_sensor():
    while True:
        print(gas_sensor.read_uv())

        adc_value = gas_sensor.read()  # values between 0 and 4095
        gas_percentage = adc_value * 100 / 4095

        print(f'Gas sensor: {adc_value}\nGas percentage: {gas_percentage}')

        # TODO: send patch

        await asyncio.sleep(config.SENSOR_POLL_TIME)


def set_brightness(color, brightness):
    return tuple(int(c * brightness) for c in color)


def react_to_relay_state():
    if relay_state:
        np[0] = set_brightness((255, 0, 0), 0.1)  # Red
        relay.on()
        print('Heating is ON')
    else:
        np[0] = set_brightness((0, 0, 0), 0.0)  # Black
        relay.off()
        print('Heating is OFF')

    np.write()
