from umqtt.robust import MQTTClient

_TWIN = "$iothub/twin"
_TWIN_RES = f'{_TWIN}/res'
_TWIN_SUBSCRIBE_TOPIC = f'{_TWIN_RES}/#'
_TWIN_GET = '{twin}/GET/?$rid={rid}'.format(twin=_TWIN, rid='{rid}')
_TWIN_PATCH = '{twin}/PATCH/properties/reported/?$rid={rid}'.format(twin=_TWIN, rid='{rid}')


# def callback(topic, message):
#     """ Callback function for handling incoming messages from IoT Hub. """
#
#     print(f'Received message on callback: {topic}, {message}')

    # try:
    #     topic_str: str = topic.decode()
    #
    #     if topic_str.startswith(_TWIN):
    #         print(f'Got twin message for topic {topic_str}: {message}')
    #
    #         # Handle response to a twin GET request
    #         if self.twin_cb is not None and topic_str.startswith(_TWIN_RES):
    #             import ujson
    #             twin_message = ujson.loads(message.decode())
    #             self.twin_cb(twin_message)
    #
    # except Exception as e:
    #     print(f"Error processing message: {e}")
    #     if self.user_cb is not None:
    #         self.user_cb(topic, message)


class MqttTwinClient(MQTTClient):
    def __init__(self, *argv, **kwargs):
        super().__init__(*argv, **kwargs)

        # Inject callback
        # self.cb = callback
        # self.user_cb = None
        # self.twin_cb = None
        # super().set_callback(callback)

    # def set_callback(self, f):
    #     self.user_cb = f

    def subscribe_twin(self, f):
        """ Subscribe to twin updates. The function receives the twin properties as parameter. """

        self.subscribe(_TWIN_SUBSCRIBE_TOPIC)
        # self.twin_cb = f

    def request_twin(self):
        """ Request the current device twin properties from IoT Hub. """

        import helpers

        uuid = helpers.uuid()
        self.publish(_TWIN_GET.format(rid=uuid), '')

    def update_reported_properties(self, reported_properties):
        """ Update reported properties in the device twin. """

        import helpers, ujson

        uuid = helpers.uuid()
        payload = ujson.dumps({
            "properties": {
                "reported": reported_properties
            }
        })
        self.publish(_TWIN_PATCH.format(rid=uuid), payload)
