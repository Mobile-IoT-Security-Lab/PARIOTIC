# Example

We tested our PoC with [RIOT](http://riot-os.org/), an open source IoT firmware written in C language.

To pull the RIOT submodule:
```
$ git submodule update --init --recursive
```

> NB: The file `sources.txt` and `includes.txt` are related to the RIOT version 2021.01. Different RIOT version could have different source files (`sources.txt`) and include directories (listed in the `includes.txt`). 

To protected the RIOT firmware 3 steps are needed:
1) Run the `CLB Injector` (See the [CLB Injector README](../Tools/CLB_Injector/README.md) for more details)
```
$ cd <path/to/PATRIOT>/Example
$ <path/to/parserc/venv>/bin/python3 ../Tools/CLB_Injector/main.py -f ./sources.txt -i ./includes.txt -d ${PWD}/
```
2) Build the source code
```
$ cd ./RIOT/
$ sudo ./dist/tools/tapsetup/tapsetup
$ cd ./examples/default/
$ make WERROR=0 all
```
3) Run the `CLB Protector` (See the [CLB Protector README](../Tools/CLB_Protector/README.md) for more details)
```
$ cd <path/to/PATRIOT>/Example
$ java -jar ./CLB_Protector.jar -i ./RIOT/examples/default/bin/native/default.elf -ed /tmp/encryption-details.txt -od /tmp/other-details.txt
```


Now you are able to run the protected elf file:
```
$ cd ./RIOT/examples/default 
$ make term
```

To rerun the protection steps, you need to clean the modified files from RIOT folder:
```
$ cd <path/to/PATRIOT>/Example/RIOT
$ git restore .
```
