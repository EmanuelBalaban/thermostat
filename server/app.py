import asyncio
import gc
import machine

import config
import lib.aht as aht
from lib.microdot.microdot import Microdot, abort, send_file
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
state_listeners: list[asyncio.Event] = []

app = Microdot()

sensor: aht.AHT20


async def main():
    global sensor

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
    port = 443 if config.USE_SSL else 80
    asyncio.create_task(app.start_server(port=port, ssl=ssl_ctx, debug=True))
    gc.collect()

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


@app.get('/')
async def index_html(_):
    return send_file('web/index.html', content_type='text/html')


@app.get('/script.js')
async def script_js(_):
    return send_file('web/script.js')


@app.get('/styles.css')
async def styles_css(_):
    return send_file('web/styles.css')


@app.get('/state')
@with_sse
async def watch_state(_, sse):
    event = subscribe_to_state_updates()

    try:
        await sse.send(state)

        while True:
            state_clone = set(state.items())

            try:
                await asyncio.wait_for(event.wait(), timeout=config.SSE_FREQ)

                diff = set(state.items()) - state_clone

                if len(diff) != 0:
                    updates = dict(diff)
                    await sse.send(updates)
                else:
                    await sse.send(None)  # Send heartbeat
            except (asyncio.TimeoutError, asyncio.CancelledError):
                await sse.send(None)  # Send heartbeat

            await asyncio.sleep(0)
    except OSError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"Unhandled error: {e}")
    finally:
        unsubscribe_from_state_updates(event)


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
        update_state_listeners()


@app.get('/android-chrome-192x192.png')
async def favicon(_):
    return send_file('icons/android-chrome-192x192.png')


@app.get('android-chrome-512x512.png')
async def favicon(_):
    return send_file('icons/android-chrome-512x512.png')


@app.get('apple-touch-icon.png')
async def favicon(_):
    return send_file('icons/apple-touch-icon.png')


@app.get('/favicon.ico')
async def favicon(_):
    return send_file('icons/favicon.ico')


@app.get('favicon-16x16.png')
async def favicon(_):
    return send_file('icons/favicon-16x16.png')


@app.get('favicon-32x32.png')
async def favicon(_):
    return send_file('icons/favicon-32x32.png')


def update_state_listeners():
    for listener in state_listeners:
        listener.set()


def subscribe_to_state_updates() -> asyncio.Event:
    """
    Create a new asyncio event for listening to state updates.
    Returns the event object and the id of the object.
    """

    event = asyncio.Event()
    state_listeners.append(event)
    return event


def unsubscribe_from_state_updates(event: asyncio.Event):
    state_listeners.remove(event)
