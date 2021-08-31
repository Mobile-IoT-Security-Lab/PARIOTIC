from clang.cindex import Config, Cursor, CursorKind, TranslationUnit, TypeKind
from abc import ABC, abstractmethod
from subprocess import run, PIPE
from re import match

from models.condition import QualifiedCondition
from utils import extract_lines_column

Config.set_library_path("/usr/lib/llvm-11/lib")
Config.set_library_file("/usr/lib/llvm-11/lib/libclang.so.1")


class AbstractParser(ABC):
    def __init__(self, file_path, includes):
        self.typedefs = dict()
        self.enums = dict()
        # name -> value
        self.global_cost_variables = dict()
        # name -> type
        self.global_variables = dict()
        # name -> type
        self.define_variable = dict()

        self.file_path = file_path
        self.includes = includes
        includes_input = [f"-I{include}" for include in includes]
        self.translation_unit = TranslationUnit.from_source(file_path, includes_input)

    @abstractmethod
    def parse(self):
        pass

    def walk_through_units(self):
        for child in self.translation_unit.cursor.get_children():
            if child.kind == CursorKind.TYPEDEF_DECL:
                self.handle_typedef_decl(child)
            elif child.kind == CursorKind.ENUM_DECL:
                self.handle_enum_decl(child)
            elif child.kind == CursorKind.STRUCT_DECL:
                self.handle_struct_decl(child)
            elif child.kind == CursorKind.UNION_DECL:
                self.handle_union_decl(child)
            elif child.kind == CursorKind.FUNCTION_DECL:
                self.handle_func_decl(child)
            elif child.kind == CursorKind.VAR_DECL:
                self.handle_var_decl(child)
            else:
                self.handle_generic(child)

    @abstractmethod
    def handle_typedef_decl(self, cursor):
        pass

    def handle_enum_decl(self, cursor):
        for child in cursor.get_children():
            self.enums[child.spelling] = child.enum_value

    @abstractmethod
    def handle_struct_decl(self, cursor):
        pass

    @abstractmethod
    def handle_union_decl(self, cursor):
        pass

    @abstractmethod
    def handle_func_decl(self, cursor):
        pass

    def handle_var_decl(self, cursor):
        # Extract const value
        if cursor.type.is_const_qualified():  # NB: the pointers are not const!
            tokens = [t.spelling for t in cursor.get_tokens()]
            if "extern" in tokens:
                print("TODO: potential extern const")
                pass
            else:
                if cursor.type.kind == TypeKind.TYPEDEF:
                    print("TODO: handle complex const struct")
                    pass
                else:
                    *_, right = cursor.get_children()
                    tokens = [t.spelling for t in right.get_tokens()]

                    if len(tokens) == 0:
                        raise ValueError("No token found")
                    elif len(tokens) == 1:
                        self.global_cost_variables[cursor.spelling] = tokens[0]
                    else:
                        print("TODO: extract const value!")

        self.global_variables[cursor.spelling] = cursor.type.spelling

    @abstractmethod
    def handle_generic(self, cursor):
        pass


class Parser(AbstractParser):
    def __init__(self, file_path, includes):
        super().__init__(file_path, includes)
        self.func_variables = dict()
        self.qualified_conditions = list()

    def parse(self):
        return self.walk_through_units()

    def handle_typedef_decl(self, cursor):
        pass

    def handle_struct_decl(self, cursor):
        pass

    def handle_union_decl(self, cursor):
        pass

    def __extract_constant(self, cursor, parent, operator="==", is_left=True):
        tokens = [t.spelling for t in cursor.get_tokens()]

        if len(tokens) == 1:
            if cursor.spelling:
                result = None

                if cursor.spelling in self.global_cost_variables:
                    result = self.global_cost_variables[cursor.spelling]
                elif cursor.spelling in self.enums:
                    result = self.enums[cursor.spelling]

                return result
            else:
                return tokens[0]

        else:
            # Check if #define or NULL
            indices = [i for i, x in enumerate(list(parent.get_tokens())) if x.spelling == operator]
            if len(indices) != 1:
                return None

            parent_tokens = [t.spelling for t in parent.get_tokens()]
            if is_left:
                variable_name = ''.join(parent_tokens[:indices[0]])
            else:
                variable_name = ''.join(parent_tokens[indices[0] + 1:])

            if variable_name == "NULL":
                return '\0'
            elif match("^-[0-9]+$", variable_name):
                return variable_name

            cmd = f"clang -E -Wp,-dD -I{' -I'.join(self.includes)} {self.file_path} | grep \"#define {variable_name}\" | sed -ne 's/^#define {variable_name} // p'"
            results = [x for x in run(cmd, shell=True, stdout=PIPE).stdout.decode().strip().split("\n") if x != '']

            if len(results) == 1:
                result = results[0]

                if not bool(match("(^[x0-9\(\)]+$|^'.+'$|^\".+\"$)", result)):
                    return None

                return result

        return None

    def __handle_compound_stmt_recursive(self, cursor, function_name,
                                         function_signature, qualified_conditions, func_variables, return_type):
        for child in cursor.get_children():
            if child.kind == CursorKind.DECL_STMT:
                for tmp in child.get_children():
                    func_variables[tmp.spelling] = tmp.type.spelling
                # TODO: check if we can consider these variables as constants

            elif child.kind == CursorKind.IF_STMT:
                # NB: We consider only extern if -> do not create nested logic bombs
                is_else = False
                try:
                    condition, then, elze = child.get_children()
                except:
                    condition, then, *_ = child.get_children()
                    elze = None

                if condition.kind == CursorKind.BINARY_OPERATOR:
                    (left, right) = list(condition.get_children())
                elif condition.kind == CursorKind.UNARY_OPERATOR:
                    print("TODO: consider also if that is like if(isSomething) ")
                    continue
                elif condition.kind == CursorKind.CALL_EXPR:
                    print("TODO: consider also if that contails only a function call like if (irq_is_in()) ")
                    continue
                elif condition.kind == CursorKind.UNEXPOSED_EXPR:  # Complex stmt likes strcmp(...) == 0
                    content = extract_lines_column(child.extent.start.file.name, child.extent.start.line,
                                                   child.extent.start.column, then.extent.start.line,
                                                   then.extent.start.column)
                    print("TODO: Handle complex if stmts -> create and hand-parsing of the condition content", content)
                    continue
                else:
                    continue

                # Extract operators
                try:
                    offset = len(list(left.get_tokens()))
                    operator = [i for i in condition.get_tokens()][offset].spelling
                except:
                    print(
                        "Error on offset to be handled -> TODO: potential error could be from #define on the left -> define breaks the Cursor")
                    continue

                # TODO: handle functions like strcmp, strncmp, ecc..
                if_body = None
                if operator == "==":
                    # encrypt then stmt
                    if_body = then
                elif isinstance(elze, Cursor) and operator == "!=":
                    # encrypt else stmts
                    if_body = elze
                    is_else = True

                if not isinstance(if_body, Cursor):
                    continue

                # check if there is a constant in left or rigth
                constant = self.__extract_constant(left, condition, operator)
                other = right
                if not constant or constant is None:
                    constant = self.__extract_constant(right, condition, operator, False)
                    other = left
                if not constant or constant is None:
                    continue

                # Check the type of the other variable
                correct_types = ['int', 'unsigned int', 'char', 'char*', 'char *', 'pid_t', 'ssize_t', 'size_t',
                                 'const char', 'const char*', 'const char *']
                other_var_type = other.type.spelling
                if other_var_type not in correct_types:
                    continue

                # Add a qualified condition
                qualified_conditions.append(QualifiedCondition(child.extent.start.file.name, child.extent.start.line,
                                                               function_name, function_signature, condition, if_body,
                                                               constant, other, operator, return_type, is_else))

            elif child.kind == CursorKind.WHILE_STMT or child.kind == CursorKind.FOR_STMT \
                    or child.kind == CursorKind.SWITCH_STMT:

                *_, last = child.get_children()
                if last.kind != CursorKind.COMPOUND_STMT:
                    continue

                _, qualified_conditions, func_variables = \
                    self.__handle_compound_stmt_recursive(last, function_name,
                                                          function_signature, qualified_conditions, func_variables,
                                                          return_type)

            elif child.kind == child.kind == CursorKind.DO_STMT:

                first, *_ = child.get_children()
                if first.kind != CursorKind.COMPOUND_STMT:
                    continue

                _, qualified_conditions, func_variables = \
                    self.__handle_compound_stmt_recursive(first, function_name,
                                                          function_signature, qualified_conditions, func_variables,
                                                          return_type)

            else:
                pass

        return None, qualified_conditions, func_variables

    def handle_func_decl(self, cursor):
        if self.file_path != cursor.extent.start.file.name:
            return

        if "extern" in [t.spelling for t in cursor.get_tokens()]:
            return

        if len(list(cursor.get_children())) <= 0:
            return

        *params, last = cursor.get_children()
        if last.kind != CursorKind.COMPOUND_STMT:
            return

        # variable name -> type
        func_variables = dict()
        for param in params:
            func_variables[param.spelling] = param.type.spelling

        qualified_conditions = list()
        function_signature = ''.join(
            extract_lines_column(self.file_path, cursor.extent.start.line, cursor.extent.start.column,
                                 last.extent.start.line, last.extent.start.column - 1))
        _, qualified_conditions, func_variables = \
            self.__handle_compound_stmt_recursive(last, cursor.spelling, function_signature, qualified_conditions,
                                                  func_variables, cursor.result_type.spelling)

        self.func_variables[cursor.spelling] = func_variables

        if len(qualified_conditions) > 0:
            self.qualified_conditions += qualified_conditions

    def handle_generic(self, cursor):
        # Why we can be here?
        print("Generic handler for CursorType", cursor.kind)
        pass
