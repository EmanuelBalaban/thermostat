import os
import subprocess


def main():
    src_dir = 'lib'
    compiled_dir = 'compiled'

    # Clear compiled directory
    for root, _, files in os.walk(compiled_dir):
        for file in files:
            os.remove(os.path.join(root, file))

    # Recursively process files in src_dir
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):  # Process only Python files
                relative_path = os.path.relpath(root, src_dir)
                compiled_subdir = os.path.join(compiled_dir, relative_path)

                # Create corresponding directory in compiled_dir
                os.makedirs(compiled_subdir, exist_ok=True)

                # Convert the Python file to .mpy
                source_file = os.path.join(root, file)
                mpy_file = os.path.join(compiled_subdir, file.replace('.py', '.mpy'))
                subprocess.run(['mpy-cross', source_file, '-o', mpy_file])


if __name__ == "__main__":
    main()
