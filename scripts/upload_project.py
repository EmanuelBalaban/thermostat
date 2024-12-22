import os, subprocess

from serial_ports import select_serial_port


def main():
    serial_port = select_serial_port()

    if serial_port is None:
        return

    files = [file for file in os.listdir('src') if os.path.isfile(f'src/{file}') and file.endswith('.py')]

    print(f'Uploading {files} to {serial_port}...')

    for file in files:
        subprocess.run([
            'ampy',
            '-p',
            f'{serial_port}',
            'put',
            f'src/{file}',
            f'{file}'
        ])


if __name__ == "__main__":
    main()
