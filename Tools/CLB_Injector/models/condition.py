import random
import string
from random import randint
from sys import maxsize

from clang.cindex import Cursor, CursorKind

from models.exception import UnsupportedConstantException
from models.objects import VariableObject, FunctionCall, ConstantType
from utils import check_define_function_from_tokens, handle_last_cursor, extract_lines_column, hash_string, \
    parse_constant_value_to_string

from re import match, search
from Crypto.Random import get_random_bytes
from Crypto.Util.number import getPrime


class QualifiedCondition:
    def __init__(self, filename, line, function_name, function_signature,
                 condition: Cursor, range_cursor: Cursor, constant_value, other_variable, operator, return_type, is_else):
        self.filename = filename
        self.line = line
        self.function_name = function_name
        self.function_signature = function_signature
        self.condition = condition
        self.range_cursor = range_cursor
        self.return_type = return_type
        self.is_else = is_else

        try:
            self.__condition_type, self.__length_constant_value, self.__string_constant_value = parse_constant_value_to_string(
                constant_value)

            if self.__string_constant_value is None:
                raise Exception

        except Exception:
            raise UnsupportedConstantException()

        self.other_variable = other_variable
        self.operator = operator

    def __extract_body_recursive(self, cursor, func_variables, enums, global_variables, added_lines):
        children = list(cursor.get_children())

        if len(children) == 0:
            return handle_last_cursor(cursor, func_variables, enums=enums,
                                      global_variables=global_variables, added_lines=added_lines)

        elif cursor.kind == CursorKind.CALL_EXPR:
            # Check if there is no tokens
            if len(list(cursor.get_tokens())) <= 0 and cursor.spelling == "":
                return None

            func, *args = list(cursor.get_children())

            # Retrieve the function name
            try:
                func_call = handle_last_cursor(list(func.get_children())[-1], func_variables, is_function=True,
                                               enums=enums, global_variables=global_variables, added_lines=added_lines)
            except ValueError:
                print("TODO: handle function call -> func_call has no func call ")
                func_call = FunctionCall(cursor.spelling, cursor.type.spelling)

            # Extract all function arguments
            for arg in args:
                arg_name = self.__extract_body_recursive(arg, func_variables, enums, global_variables, added_lines)
                func_call.add_argument(arg_name)

            return func_call

        elif cursor.kind == CursorKind.DECL_STMT:
            tokens = [t.spelling for t in cursor.get_tokens()]
            variables = list()

            # check if there is also an assign
            try:
                # TODO: Update this check
                index = tokens.index("=")

                # get left variable
                var = \
                    VariableObject(list(cursor.get_children())[0].type.spelling,
                                   list(cursor.get_children())[0].spelling, True)
                variables.append(var)

                # get right variables
                right = tokens[index + 1:]
                for key in func_variables:
                    if key in right:
                        var = VariableObject(func_variables[key], key)
                        variables.append(var)
            except:
                # There is no assignment -> get until ';' token
                if ',' in tokens:
                    indexs = [i for i, token in enumerate(tokens) if token == ',']
                    if indexs[0] - 2 == 0:
                        type = tokens[0]
                    else:
                        type = ''.join(tokens[:indexs[0] - 2])
                    for index in indexs:
                        var = VariableObject(type, tokens[index - 1], True)
                        variables.append(var)
                    var = VariableObject(type, tokens[indexs[-1] + 1], True)
                    variables.append(var)

                else:
                    if tokens.index(";") - 2 == 0:
                        type = tokens[0]
                    else:
                        type = ''.join(tokens[:tokens.index(";") - 2])
                    var = VariableObject(type, tokens[tokens.index(";") - 1], True)
                    variables.append(var)

            return variables

        else:
            results = list()
            for child in children:
                result = self.__extract_body_recursive(child, func_variables, enums, global_variables, added_lines)

                if result:
                    results.append(result)

            if results and len(results) > 0:
                if len(results) > 1:
                    return results
                else:
                    return results[0]

            return None

    def extract_body(self, func_variables, enums, global_variables, added_lines=0):
        # extract define functions
        define_functions = check_define_function_from_tokens(self.filename,
                                                             [t.spelling for t in self.range_cursor.get_tokens()],
                                                             func_variables)

        body = list()
        for define_function in define_functions:
            body += define_functions[define_function]

        extracted_body = \
            self.__extract_body_recursive(self.range_cursor, func_variables, enums, global_variables, added_lines)

        from collections.abc import Iterable
        body += extracted_body if isinstance(extracted_body, Iterable) else [
            extracted_body] if extracted_body is not None else list()
        lines = extract_lines_column(self.range_cursor.extent.start.file.name,
                                     self.range_cursor.extent.start.line + added_lines,
                                     self.range_cursor.extent.start.column,
                                     self.range_cursor.extent.end.line + added_lines,
                                     self.range_cursor.extent.end.column)

        needed_variables, _ = self.__retrieve_needed_variables(body)
        if not isinstance(needed_variables, list):
            needed_variables = [needed_variables]

        return needed_variables, lines

    def __retrieve_needed_variables(self, results, declared_variables=set()):
        if isinstance(results, list):
            variables = set()
            for result in results:
                tmp, declared_variables = self.__retrieve_needed_variables(result, declared_variables)

                if tmp:
                    if isinstance(tmp, list):
                        variables.update(tmp)
                    else:
                        variables.add(tmp)

            return list(variables), declared_variables

        elif isinstance(results, VariableObject):
            # Ignore variable that is defined in QualifiedCondition
            if not results.is_defined and results not in declared_variables:
                return results, declared_variables
            else:
                declared_variables.add(results)

        elif isinstance(results, FunctionCall):
            tmp, declared_variables = self.__retrieve_needed_variables(results.arguments, declared_variables)

            """Decomment if we want to consider also the function as signature
            if tmp:
                if isinstance(tmp, list):
                    return tmp.append(results), declared_variables
                else:
                    return [tmp, results], declared_variables

            return results, declared_variables
            """
            return tmp, declared_variables

        return None, declared_variables

    def __custom_print(self, results):
        if isinstance(results, list):
            for result in results:
                self.__custom_print(result)
        else:
            print(results.__str__())

    def __retrieve_hashed_constant(self):
        seed = getPrime(32, randfunc=get_random_bytes)
        return seed, hash_string(self.__string_constant_value, seed)

    def get_new_function_string(self, needed_variables, lines, output_file):
        # Create new name function for the extracted qualified condition
        new_func_name = f"{self.function_name}_{randint(0, (maxsize * 2 + 1))}"

        # Create function body
        body_func_str = ''.join(lines)
        if not bool(match("^[ \t]*{", body_func_str)):
            body_func_str = "{\n" + body_func_str + "\n}"
        body_func_str.strip()

        # Fix input parameters
        calling_params = list()
        input_params = list()

        # Inject AT control
        seed = getPrime(32, randfunc=get_random_bytes)
        at_control = f"\n\toff_t offset = 0x0ff53701;" \
                     f"\n\tsize_t count = 0xb17e5010;" \
                     f"\n\tu_int32_t precomputed_hash = 0x4559ffff;" \
                     f"\n\tu_int32_t current_at_value = get_random_portion_elf_hash(offset, count, {str(seed)});\n\t" \
                     "\n\tif (current_at_value != precomputed_hash) {\n\t" \
                     "puts(\"*Aborting: Security Exception (Repackaging detected)\");" \
                     "\nexit(123);\n}\n\n"
        # calling_params.append(f"(char*)&{self.function_name}")
        # input_params.append("void* at_offset")
        first_index = body_func_str.find('{') + 1
        body_func_str = body_func_str[:first_index] + at_control + body_func_str[first_index:]
        first_index += len(at_control)

        with open(output_file, "a") as fp:
            fp.write(
                "{\"source_file\": \"" + self.filename + "\", \"origin_func\": \"" + self.function_name + "\", \"new_func\": \"" + new_func_name + "\", \"seed\": " + str(
                    seed & ((2 ** 32) - 1)) + ", \"encryption_key\": \"" + (
                    str(self.__string_constant_value) if self.__string_constant_value != '\\' else '\\\\') + "\"}\n")

        for nv in needed_variables:
            result = nv.get_info_as_extracted_function_parameter()

            if result:
                input_params.append(f"{result['new_type']} {result['new_name']}")
                calling_params.append(f"{result['calling_parameter']}")

                if result["substitute"]:
                    assignment_before = f"{nv.type} {nv.name} = *{result['new_name']};\n\t"
                    assignment_after = f"*{result['new_name']} = {nv.name};\n\t"
                    last_index = body_func_str.rfind('}')
                    body_func_str = body_func_str[:first_index] + assignment_before + \
                                    body_func_str[first_index:last_index] + assignment_after + body_func_str[
                                                                                               last_index:]

        if len(input_params) > 0:
            parameters = ', '.join(input_params)
        else:
            parameters = 'void'

        # Modify ret value if it is present
        def_struct = ""
        return_type = "void"
        if search("return.*;", body_func_str):
            # create new type def function -> prepend to the new function
            struct_name = new_func_name + "_struct"
            return_type = struct_name
            def_struct = \
                "typedef struct {\n\tbool isReturn;\n\t" + self.return_type + " returnValue;\n} " + struct_name + ";"

            new_lines = list()
            old_lines = body_func_str.split('\n')
            for index in range(len(old_lines)):
                line = old_lines[index]
                m = search('return(.+?);', line)
                if m:
                    ret_value = str(m.group(1)).strip()

                    if ret_value is None or ret_value == "":
                        ret_value = "NULL"
                        print("This is a void function")

                    new_lines.append(f"{struct_name} {struct_name}_ret_val;")
                    new_lines.append(f"{struct_name}_ret_val.isReturn = true;")
                    new_lines.append(f"{struct_name}_ret_val.returnValue = {ret_value};")
                    new_lines.append(f"return {struct_name}_ret_val;")

                else:
                    new_lines.append(line)

            body_func_str = '\n'.join(new_lines)

            # Append continue return at the end of this instruction block
            last_index = body_func_str.rfind('}')
            body_func_str = body_func_str[:last_index] + \
                            f"{struct_name} {struct_name}_ret_val_default;\n" \
                            f"{struct_name}_ret_val_default.isReturn = false;\n" \
                            f"return {struct_name}_ret_val_default;\n" + \
                            body_func_str[last_index:]

        func_string = f"{def_struct}\n{return_type} {new_func_name} ({parameters}) {body_func_str}\n"
        return new_func_name, func_string, ', '.join(calling_params), return_type

    def compute_my_hash_instructions(self, function_with_init_injected_variables, bool_var_name="my_new_check_bool"):
        # pre-compute the hash value
        seed, precomputed_hash = self.__retrieve_hashed_constant()
        if precomputed_hash is None:  # if something went wrong
            raise UnsupportedConstantException()

        new_content = ""
        if self.__condition_type == ConstantType.STRING:
            if self.function_name not in function_with_init_injected_variables:
                var = ''.join([t.spelling for t in self.other_variable.get_tokens()])
                if var.startswith('*'):
                    var = var[1:]
                new_content += \
                    f"\tbool {bool_var_name} = my_hash((char*){var}, {self.__length_constant_value}, {seed}) {self.operator} {precomputed_hash};\n"
                function_with_init_injected_variables[self.function_name] = False
            else:
                new_content += \
                    f"{bool_var_name} = my_hash({''.join([t.spelling for t in self.other_variable.get_tokens()])}," \
                    f"{self.__length_constant_value}, {seed}) {self.operator} {precomputed_hash};\n"
        else:
            if self.__condition_type == ConstantType.CHARACTER:
                old_token = ''.join([t.spelling for t in self.other_variable.get_tokens()])
                origin_token = f"origin_token_{''.join(random.choices(string.ascii_letters + string.digits, k=10))}"
                new_content += f"\tint {origin_token} = (int) ((char){old_token});\n"

            else:
                origin_token = ''.join([t.spelling for t in self.other_variable.get_tokens()])

            # if self.function_name not in function_with_init_injected_variables:
            new_content += """
    int x_VARID_custom = ORIGINAL_TOKENS;
    int len_VARID_custom = snprintf(NULL, 0, "%d", x_VARID_custom);
    char* str_VARID_custom = malloc(len_VARID_custom+1);
    snprintf(str_VARID_custom, len_VARID_custom+1, "%d", x_VARID_custom);
    //printf("Generated string (in ORIGINAL_FUNCTION) %s", str_VARID_custom);
    //puts("");
    bool BOOL_VAR_NAME = my_hash(str_VARID_custom, STR_LENGTH, SEED) OPERATOR PRECOMPUTED_HASH;
    free(str_VARID_custom);\n
            """
            new_content = new_content.replace("VARID", ''.join(random.choices(string.ascii_letters + string.digits, k=20)))

            new_content = new_content.replace("ORIGINAL_TOKENS", origin_token)
            new_content = new_content.replace("BOOL_VAR_NAME", bool_var_name)
            new_content = new_content.replace("SEED", str(seed))
            new_content = new_content.replace("OPERATOR", str(self.operator))
            new_content = new_content.replace("PRECOMPUTED_HASH", str(precomputed_hash))
            new_content = new_content.replace("ORIGINAL_FUNCTION", self.function_name)
            new_content = new_content.replace("STR_LENGTH", str(self.__length_constant_value))

            new_content = f"\t{new_content.strip()}\n"

        return new_content, function_with_init_injected_variables

    def get_decrypt_instruction(self, function_to_decrypt, output_file, inserted=0):
        hex_placeholder = hex(0xefcdab89 + inserted)[2:]
        new_content = f"size_t s_{hex_placeholder} = 0x{hex_placeholder};\n"
        if self.__condition_type == ConstantType.STRING:
            new_content += f"decrypt_code_custom_function(\"{function_to_decrypt}\", (void*)&{function_to_decrypt}, s_{hex_placeholder}, {''.join([t.spelling for t in self.other_variable.get_tokens()])}, {self.__length_constant_value});"
        else:

            origin_token = ''.join([t.spelling for t in self.other_variable.get_tokens()])
            var_name = f"x__{randint(0, (maxsize * 2 + 1))}"
            new_content += f"int {var_name} = {origin_token};"
            new_content += f"\nint len__{var_name} = snprintf(NULL, 0, \"%d\", {var_name});"
            new_content += f"\nchar* str__{var_name} = malloc(len__{var_name} + 1);"
            new_content += f"\nsnprintf(str__{var_name}, len__{var_name}+1, \"%d\", {var_name});"
            new_content += f"\ndecrypt_code_custom_function(\"{function_to_decrypt}\", (void*)&{function_to_decrypt}, s_{hex_placeholder}, str__{var_name}, {self.__length_constant_value});"
            new_content += f"\nfree(str__{var_name});"

        with open(output_file, "a") as fp:
            fp.write(
                "{\"source_file\": \"" + self.filename + "\", \"original_function_name\": \"" + self.function_name + "\", \"new_function_name\": \"" + function_to_decrypt + "\", \"hex_to_replace\": \"" + "".join(
                    reversed([hex_placeholder[i:i + 2] for i in range(0, len(hex_placeholder), 2)])) + "\"}\n")

        return new_content
