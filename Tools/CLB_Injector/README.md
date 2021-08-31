# CLB Injector

The CLB Injector is a python project, which is responsible to modify the C/C++ source code to identify the QCs of an IoT firmware and build the CLBs.

## Prerequisites

This tool is base on python3 and clang compiler version 11. In partcular, the tool expects the existance of `/usr/lib/llvm-11/lib` folder and `/usr/lib/llvm-11/lib/libclang.so.1` file (required in the `models/parser.py` file).

In the Ubuntu 20.04 OS run:
```
$ sudo apt install clang-11
```

Otherwise, if you want to use different versions of the clang compiler, you could modify the paths at line `9` of `models/parser.py` file:
```
Config.set_library_path("/usr/lib/llvm-11/lib")
Config.set_library_file("/usr/lib/llvm-11/lib/libclang.so.1")
```
> NB: The *CLB Injector* is tested with the clang version 11. Different version could lead to different results.

## Setup

In order to run the tool, you need to install the needed python libraries:
```
$ python3 -m venv </path/to/new/venv>
$ source </path/to/new/venv>/bin/activate
$ pip install -r requirements.txt
```

## Usage
```
usage: main.py [-h] -f INPUT_FILES -i INCLUDES [-oe OUTPUT_ENCRYPTION_DETAILS]
               [-oo OUTPUT_OTHER_DETAILS]

CLB Injector

optional arguments:
  -h, --help            show this help message and exit
  -f INPUT_FILES, --input_files INPUT_FILES
                        A file which contains all the path of the c file required for the building
                        of the IoT firmare.
  -i INCLUDES, --includes INCLUDES
                        A comma separated list of all folder with headers files
  -oe OUTPUT_ENCRYPTION_DETAILS, --output-encryption-details OUTPUT_ENCRYPTION_DETAILS
                        The output path for the encryption details file. The default is
                        /tmp/encryption-details.txt
  -oo OUTPUT_OTHER_DETAILS, --output-other-details OUTPUT_OTHER_DETAILS
                        The output path for the other details file. The default is /tmp/origin-
                        details.txt
```
See [Example](../../Example/README.md) for an example.