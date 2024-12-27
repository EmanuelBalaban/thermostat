import asyncio
import gc
import machine

import config
import lib.aht as aht
from lib.microdot.microdot import Microdot, abort
from lib.microdot.sse import with_sse

gc.collect()

# Heating enabled and desired temperature can be set from outside
state = {
    'heating_enabled': True,
    'relay_state': False,
    'gas_detected': False,
    'temperature': 0.0,
    'desired_temperature': 24.0,
}
state_updates = asyncio.Event()

app = Microdot()


async def main():
    # Initialize temp sensor
    print('Initializing temperature sensor...')
    i2c = machine.SoftI2C(scl=machine.Pin(9), sda=machine.Pin(8))
    sensor = aht.AHT20(i2c)
    gc.collect()

    # Run web app
    print('Initializing web server...')
    ssl_ctx = None
    if config.USE_SSL:
        import ssl
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_ctx.load_cert_chain('certs/cert.der', 'certs/key.der')
    asyncio.create_task(app.start_server(debug=True, ssl=ssl_ctx))
    gc.collect()

    try:
        while True:
            await asyncio.sleep(0)

            update_state(
                temperature=round(sensor.temperature, 2)
            )

            gc.collect()
            await asyncio.sleep(30)
    finally:
        app.shutdown()


@app.get('/state')
@with_sse
async def watch_state(_, sse):
    await sse.send(state)

    while True:
        state_clone = set(state.items())

        # TODO: check if should send heartbeat
        await state_updates.wait()
        state_updates.clear()

        diff = set(state.items()) - state_clone

        if len(diff) != 0:
            updates = dict(diff)
            await sse.send(updates)

        await asyncio.sleep(0)


@app.put('/state/heating_enabled')
async def update_heating_enabled(request):
    import struct
    update_state(
        heating_enabled=struct.unpack('?', request.body)[0],
    )


@app.put('/state/desired_temperature')
async def update_desired_temperature(request):
    update_state(
        desired_temperature=request.json['desired_temperature'],
    )


@app.patch('/state')
async def patch_state(request):
    if request.json is None:
        abort(400)

    update_state(
        heating_enabled=request.json.get('heating_enabled'),
        gas_detected=request.json.get('gas_detected'),
        desired_temperature=request.json.get('desired_temperature'),
    )


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
        state_updates.set()
