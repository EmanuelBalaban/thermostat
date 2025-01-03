import subprocess

from serial_ports import select_serial_port


def main():
    serial_port = select_serial_port()

    if serial_port is None:
        return

    subprocess.run([
        'ampy',
        '-p',
        f'{serial_port}',
        'ls',
    ])


if __name__ == "__main__":
    main()
