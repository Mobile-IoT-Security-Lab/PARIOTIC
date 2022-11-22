from subprocess import run, PIPE

from models.exception import UnsupportedBodyException, UnsupportedConstantException
from models.parser import Parser
from utils import set_includes, extract_include_header, get_my_custom_hash_function, replace_content, \
    add_content_before_line, get_decrypt_function, get_elf_path_function, get_random_portion_elf_hash_function
from re import match

import argparse
import os
import random
import string

# NEEDED_LIBRARIES = ['string.h', 'stdio.h', 'stdlib.h', 'stdbool.h', 'sys/mman.h', 'unistd.h', 'sys/types.h']
NEEDED_LIBRARIES = ['string.h', 'stdio.h', 'stdlib.h', 'stdbool.h', 'unistd.h', 'sys/types.h']

def parse_args():
    """
    Parse the following input parameters:
    - the path of the file with all needed files (*.c)
    - a list of folder which contains the included files (e.g., -I for clang) - A comma separated list
    """

    parser = argparse.ArgumentParser(description="CLB Injector")
    parser.add_argument('-f', '--input_files', dest='input_files', type=str, required=True,
                        help='A file which contains the relative path of the c file required for the building of the IoT firmare.')
    parser.add_argument('-i', '--includes', dest='includes', type=str, required=True,
                        help='The file containing all include folders')
    parser.add_argument('-d', '--source-directory', dest='source_directory', type=str, required=True,
                        help='The source code base directory')
    parser.add_argument('-oe', '--output-encryption-details', dest='output_encryption_details', type=str, required=False,
                        default='/tmp/encryption-details.txt',
                        help='The output path for the encryption details file. The default is /tmp/encryption-details.txt')
    parser.add_argument('-oo', '--output-other-details', dest='output_other_details', type=str, required=False,
                        default='/tmp/other-details.txt',
                        help='The output path for the other details file. The default is /tmp/other-details.txt')

    return parser.parse_args()


def parse_file(file_path, includes, output_encryption_details, output_other_details):
    # Parse file and create the qualified_conditions in the parser object
    parser = Parser(file_path, includes)
    try:
        parser.parse()
    except Exception as e:
        print(f"Parser exception -> Message = {str(e)}")
        return 0

    # Init variables
    function_with_init_injected_variables = dict()  # keep track if we initialize injected variables in this function
    new_functions = dict()  # contains all the extracted functions for an origin one
    n_new_line = 0  # keep track the number of line inserted/removed in the current file

    # Iterate over all qualified_conditions
    for qc in parser.qualified_conditions:
        try:
            # Extract the needed variables
            needed_variables, lines = qc.extract_body(func_variables=parser.func_variables[qc.function_name],
                                                      enums=parser.enums, global_variables=parser.global_variables,
                                                      added_lines=n_new_line)

            if len(lines) <= 0:
                raise UnsupportedBodyException("Empty body")
        except UnsupportedBodyException:
            print(f"QC in function {qc.function_name} at line {qc.line} of file {qc.filename} unsupported body's "
                  f"instruction")
            continue
        except:
            print(f"QC in function {qc.function_name} at line {qc.line} of file {qc.filename} error during body analysis")
            continue

        # Create new function body
        try:
            new_func_name, func_string, parameters_string, return_type, func_ptr_type = \
                qc.get_new_function_string(needed_variables, lines, output_encryption_details)
        except:
            continue

        # Update the source code with the new content
        # Cast integer to string and invoke the my_hash function
        try:
            bool_var_name = f"my_new_check_bool_{''.join(random.choices(string.ascii_letters + string.digits, k=20))}"
            new_content, function_with_init_injected_variables = \
                qc.compute_my_hash_instructions(function_with_init_injected_variables, bool_var_name)
        except UnsupportedConstantException:
            print(f"QC in function {qc.function_name} at line {qc.line} of file {qc.filename} unsupported constant")
            continue
        add_content_before_line(file_path, qc.condition.extent.start.line + n_new_line, new_content)
        n_new_line += len(new_content.split("\n")) - 1

        # Modify the if condition
        new_content = f"{bool_var_name}"
        start_line = qc.condition.extent.start.line + n_new_line
        end_line = qc.condition.extent.end.line + n_new_line
        if start_line != end_line:
            n_new_line -= end_line - start_line
        replace_content(file_path, start_line, qc.condition.extent.start.column,
                        end_line, qc.condition.extent.end.column, new_content)

        # replace if body
        old_start_line = start_line
        start_line = qc.range_cursor.extent.start.line + n_new_line
        if qc.is_else or old_start_line != start_line:
            start_column = qc.range_cursor.extent.start.column
        else:
            start_column = qc.condition.extent.start.column + len(new_content) + 1
        end_line = qc.range_cursor.extent.end.line + n_new_line
        n_new_line -= end_line - start_line
        new_content = "{\n\t// puts(\"REPLACED BODY -> INVOKING NEW FUNCTION " + new_func_name + "\");\n"
        l = len(new_functions[qc.function_signature]) if qc.function_signature in new_functions else 0
        new_content += f"\n\t{qc.get_decrypt_instruction(new_func_name, output_other_details, l)}"
        func_ptr_type = func_ptr_type.replace("VARIABLE_NAME", f"{new_func_name}_funcptr")
        new_content += f"\n{func_ptr_type} = {new_func_name}; // {new_func_name}_funcptr = &ofuncdecr; // {new_func_name}; // ofuncdecr;\n"
        new_content += f"\n//puts(\"Before calling function at code\");\n"
        if return_type == "void":
            new_content += f"\n\t({new_func_name}_funcptr)({parameters_string});"
            new_content += f"\n\t// free(ofuncdecr);"
            new_content += "\n}"
        else:
            new_content += f"\n\t{return_type} {return_type}_val = ({new_func_name}_funcptr)({parameters_string});"
            new_content += f"\n\t if ({return_type}_val.isReturn)\n\t\treturn {return_type}_val.returnValue;"
            new_content += f"\n\t// free(ofuncdecr);"
            new_content += "\n}"

        n_new_line += len(new_content.split('\n')) - 1
        replace_content(file_path, start_line, start_column,
                        end_line, qc.range_cursor.extent.end.column, new_content)

        # Create and insert func_string before current function (qc.function_name)
        func_string = f"\n// QC in file {qc.filename} at line {qc.line}\n" + func_string + "\n"
        if qc.function_signature in new_functions:
            current_list = new_functions[qc.function_signature]
            current_list.append(func_string)
            new_functions[qc.function_signature] = current_list
        else:
            current_list = list()
            current_list.append(func_string)
            new_functions[qc.function_signature] = current_list

    total_qc = 0

    # Prepend the new functions
    if len(new_functions) > 0:
        # update the include and add the my_hash function
        with open(file_path, "r+") as c_file:
            lines = c_file.read().split("\n")
            new_content = ""
            n_ifs = 0
            has_continuation_character = False
            for index in range(len(lines)):
                if has_continuation_character:
                    new_content += f"{lines[index]}\n"
                    if not lines[index].strip().endswith("\\"):
                        has_continuation_character = False
                    continue

                elif n_ifs > 0:
                    new_content += f"{lines[index]}\n"
                    if lines[index].strip().startswith("#end"):
                        n_ifs -= 1
                    continue

                elif lines[index].strip() == "" or \
                        lines[index].strip().startswith("/*") or \
                        lines[index].strip().startswith("*") or \
                        lines[index].strip().startswith("*/") or \
                        bool(match("^[ \t]*(#|\"|extern)", lines[index].strip())):
                    new_content += f"{lines[index]}\n"
                    if lines[index].strip().startswith("#if"):
                        n_ifs += 1
                    if lines[index].strip().endswith("\\"):
                        has_continuation_character = True
                    continue

                # Check for required functions
                headers = extract_include_header(file_path)
                for library in NEEDED_LIBRARIES:
                    if f"#include <{library}>" not in headers:
                        new_content += f"#include <{library}>\n"

                new_content += f"\n{get_my_custom_hash_function()}\n"
                new_content += f"\n{get_decrypt_function()}\n"
                # new_content += f"\n{get_elf_path_function()}\n"
                new_content += f"\n{get_random_portion_elf_hash_function()}\n"

                # Add all signature of new functions
                for function_signature in new_functions:
                    total_qc += len(new_functions[function_signature])
                    for func_string in new_functions[function_signature]:
                        if "typedef" in func_string:
                            tmp = func_string.split("_struct;")[0] + '_struct;\n'
                            tmp += func_string.split('_struct;')[1].split('{')[0] + ';\n'
                            new_content += f'\n{tmp}\n'
                        else:
                            new_content += f'\n{func_string.split("{")[0]};\n'
                new_content += '\n'.join(lines[index:])
                break

            c_file.seek(0, 0)
            c_file.truncate(0)
            c_file.write(new_content)

    # Append new function bodies to the current file
    with open(file_path, "a") as c_file:
        for function_signature in new_functions:
            for func_string in new_functions[function_signature]:
                if "typedef" in func_string:
                    c_file.write(f'\n{func_string.split("_struct;")[-1]}\n')
                else:
                    c_file.write(f'\n{func_string}\n')

    return total_qc

def main():
    # TODO: check handling of #define and macros
    # TODO: Check if we can retrieve more QCs

    args = parse_args()
    file_paths = list()

    with open(args.input_files, "r") as input_file:
        while True:
            line = input_file.readline()

            if not line or line is None:
                break

            file_paths.append(os.path.abspath(os.path.join(args.source_directory, line.strip())))

    includes = list()  # [args.source_directory + include for include in args.includes.split(",")]
    with open(args.includes, 'r') as includes_file:
        lines = (includes_file.read()).split('\n')
        for line in lines:
            includes.append(os.path.abspath(os.path.join(args.source_directory, line.strip())))
    set_includes(includes)

    # Init files
    with open(args.output_encryption_details, "w") as fp:
        fp.write("")
    with open(args.output_other_details, "w") as fp:
        fp.write("")

    total = 0
    for file_path in file_paths:
        if not file_path.endswith('.c'):
            continue

        total += parse_file(file_path, includes, args.output_encryption_details, args.output_other_details)

    print("\n\nRESULT => Total number of considered if = ", total)


if __name__ == "__main__":
    main()
