import subprocess

from serial_ports import select_serial_port


def main():
    serial_port = select_serial_port()

    if serial_port is None:
        return

    print(f'Uploading libraries to {serial_port}...')

    subprocess.run([
        'ampy',
        '-p',
        f'{serial_port}',
        'put',
        'src/compiled',
        '/lib'
    ])


if __name__ == "__main__":
    main()
