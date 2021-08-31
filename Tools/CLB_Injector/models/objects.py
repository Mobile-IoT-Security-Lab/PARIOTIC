from enum import Enum
from re import match


class GenericObject:
    def __init__(self, otype):
        self.type = otype

    def __str__(self):
        return f"Generic object of type {self.type}"


class FunctionCall:
    def __init__(self, function_name, signature):
        self.function_name = function_name
        self.arguments = list()
        self.signature = signature

    def add_argument(self, argument):
        self.arguments.append(argument)

    def __str__(self):
        return f"{self.function_name}({', '.join([a.__str__() for a in self.arguments])})"

    def get_new_body_definition(self):
        if self.signature:
            return f"{self.signature} {self.function_name}"

        return None


class ConstantObject(GenericObject):
    def __init__(self, otype, value):
        super().__init__(otype)
        self.value = value

    def __str__(self):
        return f"{self.value} <{self.type}>"


class VariableObject(GenericObject):
    def __init__(self, otype, name, is_defined=False):
        super().__init__(otype)
        self.name = name
        self.is_defined = is_defined

    def __str__(self):
        return f"{self.name} <{self.type}>"

    def __eq__(self, other):
        """
        Overrides the default implementation
        This method is user for create hash in set
        """
        if isinstance(other, VariableObject):
            return self.name == other.name and self.type == other.type
        return False

    def __hash__(self):
        return hash((self.name, self.type))

    def get_info_as_extracted_function_parameter(self):
        """
        Return a new dict object or none
        """

        if self.type:
            result = dict()

            if bool(match("^[a-zA-Z0-9_]+ \[[0-9]+\]$", self.type.strip())):
                result["substitute"] = False
                result["new_name"] = self.name
                result["calling_parameter"] = self.name
                result["new_type"] = f"{self.type.strip().split(' ')[0]}*"
            else:
                result["substitute"] = True
                result["new_name"] = self.name + "__custom"
                result["calling_parameter"] = f"&{self.name}"
                result["new_type"] = f"{self.type}*"

            return result

        return None


class ConstantType(Enum):
    INTEGER = 0
    STRING = 1
    CHARACTER = 2
