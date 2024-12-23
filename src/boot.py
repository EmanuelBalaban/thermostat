import network, utime
import config


def connect_to_wifi():
    print('Connecting to WiFi...')

    wlan = network.WLAN(network.WLAN.IF_STA)
    wlan.active(config.ENABLE_WIFI)

    if not config.ENABLE_WIFI:
        return

    # Reset connection status
    if wlan.isconnected():
        wlan.disconnect()

    if config.USE_STATIC_IP_ADDR:
        wlan.ifconfig((
            config.IP_ADDR,
            config.SUBNET_MASK,
            config.GATEWAY_ADDR,
            config.DNS_SERVER))

    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWD)

    while not wlan.isconnected():
        utime.sleep(0.1)

    if wlan.status() == network.STAT_GOT_IP:
        print("Successfully connected to Wi-Fi network!")
        print("IP Address: {}".format(wlan.ifconfig()[0]))


# TODO: configure hardware

connect_to_wifi()
