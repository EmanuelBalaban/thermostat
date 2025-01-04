import asyncio, urequests, machine, neopixel
from urequests import Response
from lib.mq2 import MQ2

import config

relay_state = False
gas_detected = False

neo_pixel_pin = 1
relay_pin = 10
gas_sensor_pin = 4

gas_sensor = MQ2(pinData=gas_sensor_pin, baseVoltage=3.3)
relay = machine.Pin(relay_pin, machine.Pin.OUT)
np = neopixel.NeoPixel(machine.Pin(neo_pixel_pin, machine.Pin.OUT), 1)


async def main():
    relay.off()
    np[0] = set_brightness((0, 0, 0), 0.0)  # Black
    np.write()

    print("Calibrating the sensor...")
    gas_sensor.calibrate()
    print(f"Calibration completed. RO: {gas_sensor._ro}")

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
        # Read LPG concentration
        lpg = gas_sensor.readLPG()
        print(f"LPG: {lpg} ppm")

        # Read methane concentration
        methane = gas_sensor.readMethane()
        print(f"Methane: {methane} ppm")

        # Read smoke concentration
        smoke = gas_sensor.readSmoke()
        print(f"Smoke: {smoke} ppm")

        # Read hydrogen concentration
        hydrogen = gas_sensor.readHydrogen()
        print(f"Hydrogen: {hydrogen} ppm")

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
