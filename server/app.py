import asyncio
import gc
import machine

import config
import lib.aht as aht
from lib.microdot.microdot import Microdot, abort

gc.collect()

# Heating enabled and desired temperature can be set from outside
state = {
    'heating_enabled': True,
    'relay_state': False,
    'gas_detected': False,
    'temperature': 0.0,
    'desired_temperature': config.DEFAULT_DESIRED_TEMPERATURE,
}

app = Microdot()

sensor: aht.AHT20


async def main():
    global sensor

    # Initialize temp sensor
    print('Initializing temperature sensor...')
    i2c = machine.SoftI2C(scl=machine.Pin(14), sda=machine.Pin(8))
    sensor = aht.AHT20(i2c)
    gc.collect()

    # Run web app
    print('Initializing web server...')
    ssl_ctx = None
    if config.USE_SSL:
        import ssl
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_ctx.load_cert_chain('certs/cert.der', 'certs/key.der')
    port = 443 if config.USE_SSL else 80
    asyncio.create_task(app.start_server(port=port, ssl=ssl_ctx, debug=True))

    # Wait for server to initialize
    await asyncio.sleep(10)
    print('Server initialized.')

    try:
        while True:
            await asyncio.sleep(0)

            update_state(
                temperature=round(sensor.temperature, 2)
            )

            gc.collect()
            await asyncio.sleep(config.SENSOR_POLL_TIME)
    finally:
        app.shutdown()


@app.get('/state')
async def get_state(_):
    return state


@app.get('/state/heating_enabled')
async def get_heating_enabled(_):
    import ujson
    return ujson.dumps(state['heating_enabled'])


@app.get('/state/relay_state')
async def get_heating_enabled(_):
    import ujson
    return ujson.dumps(state['relay_state'])


@app.get('/state/gas_detected')
async def get_heating_enabled(_):
    import ujson
    return ujson.dumps(state['gas_detected'])


@app.get('/state/temperature')
async def get_heating_enabled(_):
    import ujson
    return ujson.dumps(state['temperature'])


@app.get('/state/desired_temperature')
async def get_heating_enabled(_):
    import ujson
    return ujson.dumps(state['desired_temperature'])


@app.patch('/state')
async def patch_state(request):
    if request.json is None:
        abort(400)

    update_state(
        heating_enabled=request.json.get('heating_enabled'),
        gas_detected=request.json.get('gas_detected'),
        desired_temperature=request.json.get('desired_temperature'),
    )

    await asyncio.sleep_ms(10)


def update_state(
        heating_enabled: bool | None = None,
        gas_detected: bool | None = None,
        temperature: float | None = None,
        desired_temperature: float | None = None,
):
    old_state = set(state.items())

    if heating_enabled is not None:
        state['heating_enabled'] = heating_enabled
    if gas_detected is not None:
        state['gas_detected'] = gas_detected
    if temperature is not None:
        state['temperature'] = temperature
    if desired_temperature is not None:
        state['desired_temperature'] = desired_temperature

    state['relay_state'] = (state['heating_enabled']
                            and not state['gas_detected']
                            and state['temperature'] < state['desired_temperature'])

    if old_state != set(state.items()):
        print(state)
