# Certificates

## Generate PEM

```shell
openssl req -x509 -nodes -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365
```

## Convert to DER

```shell
openssl x509 -outform der -in cert.pem -out cert.der
```

```shell
openssl rsa -outform der -in key.pem -out key.der
```

## Upload to ESP32

```shell
ampy -p /dev/ttyACM0 mkdir /certs
```

```shell
ampy -p /dev/ttyACM0 put cert.der /certs/cert.der
```

```shell
ampy -p /dev/ttyACM0 put key.der /certs/key.der
```