from os import listdir, remove
import subprocess


def main():
    compiled_files = listdir('src/compiled')

    for compiled_file in compiled_files:
        remove(f'src/compiled/{compiled_file}')

    files = listdir('src/lib')

    for filename in files:
        mpy_filename = filename.replace('.py', '.mpy')

        subprocess.run(['mpy-cross', f'src/lib/{filename}', '-o', f'src/compiled/{mpy_filename}'])


if __name__ == "__main__":
    main()
