from re import match
from subprocess import run, PIPE

from clang.cindex import CursorKind, TypeKind

from models.exception import UnsupportedBodyException
from models.objects import ConstantObject, FunctionCall, VariableObject, ConstantType

includes = list()


def set_includes(incls):
    global includes
    includes = incls


def get_function_line(file, function_signature):
    cmd = f"grep -Fn \"{function_signature.strip()}\" {file}"
    results = [x for x in [run(cmd, shell=True, stdout=PIPE).stdout.decode().strip().strip("\n")] if x != '']

    if len(results) == 1:
        return int(results[0].split(":")[0])

    raise Exception("Exception searching the function")


def add_content_before_line(file, line, new_content):
    with open(file, "r+") as fp:
        content = fp.readlines()
        content = ''.join(content[:line-1]) + new_content + ''.join(content[line-1:])

        fp.seek(0, 0)
        fp.truncate(0)
        fp.write(content)


def extract_lines_column(file, start_line, start_column, end_line, end_column):
    lines = extract_lines(file, start_line, end_line)

    lines[-1] = lines[-1][:end_column]
    lines[0] = lines[0][start_column - 1:]

    return lines


def extract_lines(file, start_line, end_line):
    lines = list()
    with open(file) as fp:
        all_lines = fp.readlines()
        for i in range(start_line, end_line + 1, 1):
            lines.append(all_lines[i - 1])

    return lines


def replace_content(file, start_line, start_column, end_line, end_column, new_content):
    start_line -= 1
    end_line -= 1
    start_column -= 1
    end_column -= 1

    with open(file, "r+") as fp:
        lines = fp.readlines()

        content = ''.join(lines[:start_line]) \
                  + lines[start_line][:start_column] \
                  + new_content \
                  + lines[end_line][end_column:] \
                  + ''.join(lines[end_line + 1:])

        fp.seek(0, 0)
        fp.truncate(0)
        fp.write(content)


def handle_last_cursor(cursor, func_variables, is_function=False, enums=dict(), global_variables=dict(), added_lines=0):
    if len(list(cursor.get_children())) > 0:
        raise ValueError("Last cursor must not have children")

    if cursor.kind == CursorKind.INTEGER_LITERAL:
        return ConstantObject(cursor.type.kind, cursor.spelling)
    elif cursor.kind == CursorKind.COMPOUND_STMT:
        content = extract_lines_column(cursor.extent.start.file.name,
                                       cursor.extent.start.line+added_lines,
                                       cursor.extent.start.column,
                                       cursor.extent.end.line+added_lines,
                                       cursor.extent.end.column)
        instructions = [x.strip() for x in ''.join(content).replace("\n", "")[1:-1].split(";") if x.strip() != '']

        variables = list()
        for instruction in instructions:
            tmp = extract_directly_from_body(instruction, func_variables)

            if tmp:
                if len(tmp) > 1:
                    variables += tmp
                else:
                    variables.append(tmp)

        return variables
    elif cursor.kind == CursorKind.TYPE_REF:
        pass
    elif cursor.kind == CursorKind.NULL_STMT:
        # Nothing
        pass
    elif cursor.kind == CursorKind.CONTINUE_STMT:
        raise UnsupportedBodyException()
    elif cursor.kind == CursorKind.BREAK_STMT:
        raise UnsupportedBodyException()
    elif cursor.kind == CursorKind.STRING_LITERAL:
        return ConstantObject(cursor.type.kind, cursor.spelling)
    elif cursor.kind == CursorKind.RETURN_STMT:
        # The return str ->
        raise UnsupportedBodyException()
    elif cursor.kind == CursorKind.DECL_REF_EXPR:
        if is_function:
            return FunctionCall(cursor.spelling, cursor.type.spelling)

        if cursor.spelling not in enums and \
                cursor.spelling not in global_variables and \
                not is_define_variable(cursor.extent.start.file.name, cursor.spelling) \
                and cursor.type.kind != TypeKind.FUNCTIONPROTO \
                and cursor.type.kind != TypeKind.ELABORATED:
            return VariableObject(cursor.type.spelling, cursor.spelling)

        else: # cursor.type.kind == TypeKind.ELABORATED:
            # TODO: handle this case
            """
            Complex struct like:
            struct {
                int16_t base, len;
            } best = { -1, 0}, cur = { -1, 0};
            """
            raise UnsupportedBodyException("Unsupported struct definition")

    else:
        print("Last Cursor of type", cursor.kind, "to be handled")

    return None


def is_define_variable(file, name):
    cmd = "clang -E -Wp,-dD -I" + ' -I'.join(
        includes) + " " + file + " | grep \"^#define[ \t]\{1,\}" + name + "[ \t]\{1,\}\""
    results = [x for x in [run(cmd, shell=True, stdout=PIPE).stdout.decode().strip().strip("\n")] if x != '']

    if len(results) == 1:
        return True

    return False


def search_define_function(file, func_name):
    # search func_name with clang
    cmd = "clang -E -Wp,-dD -I" + ' -I'.join(includes) + " " + file + " | grep \"^#define[ \t]\{1,\}" + func_name + "\""
    results = [x for x in [run(cmd, shell=True, stdout=PIPE).stdout.decode().strip().strip("\n")] if x != '']

    return results


def extract_instructions_from_func_call(content, iter=0, curr_instruction="", n_open=0):
    instructions = list()
    for i in range(len(content)):
        if content[i].endswith("("):
            instr, iter = extract_instructions_from_func_call(content[i + 1:], 0, curr_instruction + content[i],
                                                              n_open + 1)
            instructions.append(instr)
            i += iter

        elif n_open > 0:  # inside a function
            if content[i] == ')':
                n_open -= 1
            if n_open == 0:
                return curr_instruction + ')', iter + 1
            else:
                return extract_instructions_from_func_call(content[i + 1:], iter + 1, curr_instruction + content[i],
                                                           n_open)

        else:
            instructions.append(content[i])

    return instructions


def extract_directly_from_body(instruction, func_variables):
    if "=" in instruction:
        variables = list()
        for tmp in instruction.split("="):
            variables.append(extract_directly_from_body(tmp.strip(), func_variables))

        return variables
    elif instruction.endswith('&') or instruction.endswith('|') or instruction.endswith('^') or instruction.endswith('/') or instruction.endswith('*'):
        return extract_directly_from_body(instruction[:-1].strip(), func_variables)
    elif instruction.strip() == "NULL":
        return ConstantObject("NULL", '\0')
    elif bool(match("(^\".*\"$|^'.*'$)", instruction)):  # constant
        return ConstantObject("char o char*", instruction)
    elif bool(match("^[x0-9\(\).,]+$", instruction)):  # constant
        return ConstantObject("int o double, signed or unsigned", instruction)
    elif bool(match("[a-zA-Z0-9_]+\(.*\)", instruction)):  # function call
        variables = list()
        variables.append(FunctionCall(instruction[:instruction.find("(")], "COME RECUPERO LA SIGNATURE DA QUA?!?"))
        content = instruction[instruction.find("(") + 1:-1]

        instructions = extract_instructions_from_func_call(content.split(","))

        for instr in instructions:
            variables.append(extract_directly_from_body(instr, func_variables))

        return variables
    else:  # simple variable
        name = instruction.strip()
        if '->' in name:
            name = name[:name.find('->')]
        if name.startswith('&'):
            name = name[1:]

        # Retrieve the type for this variable -> get also if constant or enum
        otype = None
        if name in func_variables:
            otype = func_variables[name]
        return VariableObject(otype, name)

    return None


def check_define_function_from_tokens(file, tokens, func_variables):
    defined_functions = dict()

    for i in range(len(tokens) - 1):
        if bool(match("^[a-zA-Z0-9_]+\($", tokens[i] + tokens[i + 1])):
            results = search_define_function(file, tokens[i] + "[ (]\{1\}")

            if len(results) == 1:
                # Extract tokens from this define function -> until the ")"
                content_tokens = list()
                n_open = 0
                for j in range(i + 2, len(tokens)):
                    if tokens[j] == ')':
                        if n_open == 0:
                            break
                        else:
                            n_open -= 1
                    content_tokens.append(tokens[j])
                    if content_tokens[-1] == '(':
                        n_open += 1

                defined_functions[tokens[i]] = extract_directly_from_body(
                    tokens[i] + '(' + (''.join(content_tokens)) + ')', func_variables)

    return defined_functions


def extract_include_header(file_path):
    headers = list()
    found = False
    with open(file_path, 'r') as f:
        while True:
            line = f.readline()

            if not line or line is None:
                break

            if not found:
                if line.startswith("#"):
                    found = True

            if found:
                line = line.strip()
                if line == '':
                    continue
                elif line.startswith("#"):
                    headers.append(line)
                else:
                    break

    return headers


def get_my_custom_hash_function():
    return """// My custom hash function -> return a pseudo-random integer from a char array
static u_int32_t my_hash(char* buf, size_t len, u_int32_t seed){
    // size_t len = strlen(buf);
    u_int32_t hash = seed; // 786431; /* prime */

    for (size_t i = 0; i < len; i++) {
        hash += (int) buf[i];
        hash += hash << 10;
        hash ^= hash >> 6;
    }
    hash += hash << 3;
    hash ^= hash >> 11;
    hash += hash << 15;
    return hash;
}
    """


def get_origin_function_hash_function():
    return """static u_int32_t get_origin_function_hash(void *offset, size_t count, u_int32_t seed) {

    char* functionBytes = malloc(count * sizeof(char));
    for (unsigned int i = 0; i < count; i++) {
        functionBytes[i] = ((char*)offset)[i];
    }

    u_int32_t result = my_hash(functionBytes, count, seed);
    free(functionBytes);
    
    return result;
}
    """


def get_random_portion_elf_hash_function():
    return """static u_int32_t get_random_portion_elf_hash(off_t offset, size_t count, u_int32_t seed) {
    
    char *buffer = NULL;
   int read_size;
   char filename[1024];
   FILE *handler = fopen(getElfPath(filename, 1024), "r");

   if (handler)
   {
       buffer = (char*) malloc(sizeof(char) * count );
       fseek(handler, offset, SEEK_SET);
       read_size = fread(buffer, sizeof(char), count, handler);

       if (count != read_size) {
           free(buffer);
           buffer = NULL;
       }
       fclose(handler);
    }
    u_int32_t result = my_hash(buffer, count, seed);
    free(buffer);

    return result;
}
    """


def get_all_elf_hash_function():
    return """static u_int32_t get_all_elf_hash(char* filename, u_int32_t seed) {
    
    // Read content of file
    char *buffer = NULL;
   int string_size, read_size;
   FILE *handler = fopen(filename, "r");

   if (handler)
   {
       fseek(handler, 0, SEEK_END);
       string_size = ftell(handler);
       rewind(handler);
       buffer = (char*) malloc(sizeof(char) * (string_size + 1) );
       read_size = fread(buffer, sizeof(char), string_size, handler);

       buffer[string_size] = 0x0;

       if (string_size != read_size) {
           free(buffer);
           buffer = NULL;
       }
       fclose(handler);
    }
    u_int32_t result = my_hash(buffer, string_size-1, seed);
    free(buffer);
    
    /*char* functionBytes = malloc(count * sizeof(char));
    for (unsigned int i = 0; i < count; i++) {
        functionBytes[i] = ((char*)offset)[i];
    }

    u_int32_t result = my_hash(functionBytes, count, seed);
    free(functionBytes);*/

    return result;
}
    """

def get_elf_path_function():
    return """static char * getElfPath(char* buf, int count) {
    int i;
    int rslt = readlink("/proc/self/exe", buf, count - 1);
    if (rslt < 0 || (rslt >= count - 1))
    {
        return NULL;
    }
    buf[rslt] = 0x0;
    return buf;
}
"""


def get_decrypt_function():
    return """static char** decryptedFunctionNames = NULL;
static int decryptedCurrentSize = 10;

static int decrypt_code_custom_function(char* functionName, void *offset, size_t count, char* key, int lenKey) {
    int page_size = getpagesize();

    if (decryptedFunctionNames == NULL) {
        decryptedFunctionNames = calloc(decryptedCurrentSize, sizeof(char*));
    }

    bool found = false;
    int numberOfFunction = 0;
    while(decryptedFunctionNames[numberOfFunction]) {
        if(strcmp(decryptedFunctionNames[numberOfFunction], functionName) == 0) {
            found = true;
            break;
        }
        numberOfFunction++;
    }
    if (found) {
        return 1;
    }

    char *page_start = ((char *)offset) - (((unsigned long)offset) % page_size);
    size_t page_count = 1; // Pages to mprotect
    while(((char *)offset) + count > (page_start + page_size * page_count)) {
        page_count++;
    }

    // Mark all pages where code lies in as W&X
    if(mprotect(page_start, page_count * page_size, PROT_READ | PROT_WRITE | PROT_EXEC) != 0) {
        puts("Err mprotect");
        return -1;
    }

    // TODO: update encryption method

    // Decrypt and write decrypted code back to .text segment
    unsigned char* result = malloc(count * sizeof(unsigned char));

    for (unsigned int i = 0; i < count; i++) {
        result[i] = (unsigned char) (((char*)offset)[i] ^ key[i%lenKey]);
    }

    // TODO: handle multi page
    // write back to .text section in memory
    memcpy(offset, result, count);
    
    // update functionNames
    if (numberOfFunction < decryptedCurrentSize) {
        decryptedFunctionNames[numberOfFunction] = functionName;
        numberOfFunction++;
    } else {
        // TODO: allocate more space
    }

    // Clean instruction cache
    __builtin___clear_cache(page_start, page_start + (page_count * page_size));
    return 0;
}
    """


def hash_string(string, seed):
    mask = (2**32) - 1
    h = seed & mask
    for c in string:
        h = (h + ord(c)) & mask
        h = (h + ((h << 10) & mask)) & mask
        h = h ^ (h >> 6)
    h = (h + ((h << 3) & mask)) & mask
    h = (h ^ ((h >> 11) & mask)) & mask
    h = (h + ((h << 15) & mask)) & mask
    return h


def get_int(integer):
    try:
        return int(integer)
    except:
        try:
            return int(integer, 16)
        except:
            print(f"ERROR Unknown integer = {integer}")
            return None


def parse_constant_value_to_string(constant_value):
    if isinstance(constant_value, int):
        return ConstantType.INTEGER, len(str(get_int(constant_value))), str(get_int(constant_value))

    # check if it is a string
    if bool(match("\".*\"", constant_value)):
        return ConstantType.STRING, len(constant_value[1:-1]), constant_value[1:-1]

    if constant_value == '\0':
        return ConstantType.STRING, 1, constant_value

    # check if it is a char -> integer
    if bool(match("'.?'", constant_value)):
        return ConstantType.CHARACTER, 1, str(ord(constant_value[1]))  # constant_value[1]

    # If it is an integer remove the parenthesis
    while bool(match("^\([x0-9a-f.,\(\)]+\)$", constant_value)):
        constant_value = constant_value[1:-1]

    # Check if there is a letter at the end (e.g., 14U)
    if bool(match("[x0-9a-f.,]+U$", constant_value)):
        constant_value = constant_value[:-1]

    return ConstantType.INTEGER, len(str(get_int(constant_value))), str(get_int(constant_value))
