"""
    Function module
"""
import logging
from itertools import groupby
from slither.core.sourceMapping.sourceMapping import SourceMapping
from slither.core.children.childContract import ChildContract

from slither.core.variables.stateVariable import StateVariable
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.unaryOperation import UnaryOperation
from slither.core.expressions.memberAccess import MemberAccess
from slither.core.expressions.indexAccess import IndexAccess

from slither.core.declarations.solidityVariables import SolidityVariable, SolidityFunction

logger = logging.getLogger("Function")

class Function(ChildContract, SourceMapping):
    """
        Function class
    """

    def __init__(self):
        super(Function, self).__init__()
        self._name = None
        self._view = None
        self._pure = None
        self._payable = None
        self._visibility = None
        self._is_constructor = None
        self._is_implemented = None
        self._is_empty = None
        self._entry_point = None
        self._nodes = []
        self._variables = {}
        self._parameters = []
        self._returns = []
        self._vars_read = []
        self._vars_written = []
        self._state_vars_read = []
        self._vars_read_or_written = []
        self._solidity_vars_read = []
        self._state_vars_written = []
        self._calls = []
        self._expression_vars_read = []
        self._expression_vars_written = []
        self._expression_calls = []
        self._expression_modifiers = []
        self._modifiers = []
        self._payable = False

    @property
    def name(self):
        """
            str: function name
        """
        if self._name == '':
            if self.is_constructor:
                return 'constructor'
            else:
                return 'fallback'
        return self._name

    @property
    def nodes(self):
        """
            list(Node): List of the nodes
        """
        return self._nodes

    @property
    def entry_point(self):
        """
            Node: Entry point of the function
        """
        return self._entry_point

    @property
    def visibility(self):
        """
            str: Function visibility
        """
        return self._visibility

    @property
    def payable(self):
        """
            bool: True if the function is payable
        """
        return self._payable

    @property
    def is_constructor(self):
        """
            bool: True if the function is the constructor
        """
        return self._is_constructor or self._name == self.contract.name

    @property
    def view(self):
        """
            bool: True if the function is declared as view
        """
        return self._view

    @property
    def pure(self):
        """
            bool: True if the function is declared as pure
        """
        return self._pure

    @property
    def is_implemented(self):
        """
            bool: True if the function is implemented
        """
        return self._is_implemented

    @property
    def is_empty(self):
        """
            bool: True if the function is empty
        """
        return self._is_empty

    @property
    def parameters(self):
        """
            list(LocalVariable): List of the parameters
        """
        return self._parameters

    @property
    def returns(self):
        """
            list(LocalVariable): List of the return variables
        """
        return self._returns

    @property
    def modifiers(self):
        """
            list(Modifier): List of the modifiers
        """
        return self._modifiers

    def __str__(self):
        return self._name

    @property
    def variables(self):
        """
            Return all local variables
            Include paramters and return values
        """
        return self._variables.values()

    def variables_as_dict(self):
        return self._variables

    @property
    def variables_read(self):
        """
            list(Variable): Variables read (local/state/solidity)
        """
        return self._vars_read

    @property
    def variables_written(self):
        """
            list(Variable): Variables written (local/state/solidity)
        """
        return self._vars_written

    @property
    def state_variables_read(self):
        """
            list(StateVariable): State variables read
        """
        return self._state_vars_read

    @property
    def solidity_variables_read(self):
        """
            list(SolidityVariable): Solidity variables read
        """
        return self._solidity_vars_read

    @property
    def state_variables_written(self):
        """
            list(StateVariable): State variables written
        """
        return self._state_vars_written

    @property
    def variables_read_or_written(self):
        """
            list(Variable): Variables read or written (local/state/solidity)
        """
        return self._vars_read_or_written

    @property
    def variables_read_as_expression(self):
        return self._expression_vars_read

    @property
    def variables_written_as_expression(self):
        return self._expression_vars_written

    @property
    def calls(self):
        """
            list(Function or SolidityFunction): List of calls
        """
        return self._calls

    @property
    def calls_as_expression(self):
        return self._expression_calls

    @property
    def expressions(self):
        """
            list(Expression): List of the expressions
        """
        expressions = [n.expression for n in self.nodes]
        expressions = [e for e in expressions if e]
        return expressions

    @property
    def signature(self):
        """
            (str, list(str), list(str)): Function signature as (name, list parameters type, list return values type)
        """
        return self.name, [str(x.type) for x in self.parameters], [str(x.type) for x in self.returns]

    @property
    def signature_str(self):
        """
            str: func_name(type1,type2) returns (type3)
            Return the function signature as a str (contains the return values)
        """
        name, parameters, returnVars = self.signature
        return name+'('+','.join(parameters)+') returns('+','.join(returnVars)+')'

    @property
    def full_name(self):
        """
            str: func_name(type1,type2)
            Return the function signature without the return values
        """
        name, parameters, _ = self.signature
        return name+'('+','.join(parameters)+')'


    def _filter_state_variables_written(self, expressions):
        ret =[]
        for expression in expressions:
            if isinstance(expression, Identifier):
                ret.append(expression)
            if isinstance(expression, UnaryOperation):
                ret.append(expression.expression)
            if isinstance(expression, MemberAccess):
                ret.append(expression.expression)
            if isinstance(expression, IndexAccess):
                ret.append(expression.expression_left)
        return ret

    def _analyze_read_write(self):
        """ Compute variables read/written/...

        """
        write_var = [x.variables_written_as_expression for x in self.nodes]
        write_var = [x for x in write_var if x]
        write_var = [item for sublist in write_var for item in sublist ]
        write_var = list(set(write_var))
        # Remove dupplicate if they share the same string representation
        write_var = [next(obj) for i, obj in groupby(sorted(write_var, key=lambda x: str(x)), lambda x: str(x))]
        self._expression_vars_written =  write_var

        write_var = [x.variables_written for x in self.nodes]
        write_var = [x for x in write_var if x]
        write_var = [item for sublist in write_var for item in sublist ]
        write_var = list(set(write_var))
        # Remove dupplicate if they share the same string representation
        write_var = [next(obj) for i, obj in\
                    groupby(sorted(write_var, key=lambda x: str(x)), lambda x: str(x))]
        self._vars_written = write_var

        read_var = [x.variables_read_as_expression for x in self.nodes]
        read_var = [x for x in read_var if x]
        read_var = [item for sublist in read_var for item in sublist]
        # Remove dupplicate if they share the same string representation
        read_var = [next(obj) for i, obj in\
                    groupby(sorted(read_var, key=lambda x: str(x)), lambda x: str(x))]
        self._expression_vars_read = read_var

        read_var = [x.variables_read for x in self.nodes]
        read_var = [x for x in read_var if x]
        read_var = [item for sublist in read_var for item in sublist]
        # Remove dupplicate if they share the same string representation
        read_var = [next(obj) for i, obj in\
                    groupby(sorted(read_var, key=lambda x: str(x)), lambda x: str(x))]
        self._vars_read = read_var

        self._state_vars_written = [x for x in self.variables_written if\
                                    isinstance(x, StateVariable)]
        self._state_vars_read = [x for x in self.variables_read if\
                                    isinstance(x, (StateVariable))]
        self._solidity_vars_read = [x for x in self.variables_read if\
                                    isinstance(x, (SolidityVariable))]

        self._vars_read_or_written = self._vars_written + self._vars_read

    def _analyze_calls(self):
        calls = [x.calls_as_expression for x in self.nodes]
        calls = [x for x in calls if x]
        calls = [item for sublist in calls for item in sublist]
        # Remove dupplicate if they share the same string representation
        calls = [next(obj) for i, obj in\
                 groupby(sorted(calls, key=lambda x: str(x)), lambda x: str(x))]
        self._expression_calls = calls

        calls = [x.calls for x in self.nodes]
        calls = [x for x in calls if x]
        calls = [item for sublist in calls for item in sublist]
        calls = [next(obj) for i, obj in\
                 groupby(sorted(calls, key=lambda x: str(x)), lambda x: str(x))]
        self._calls = [c for c in calls if isinstance(c, (Function, SolidityFunction))]

    def all_state_variables_read(self):
        """ recursive version of variables_read
        """
        variables = self.state_variables_read
        explored = [self]
        to_explore = [c for c in self.calls if isinstance(c, Function) and c not in explored]
        to_explore += [m for m in self.modifiers if m not in explored]

        while to_explore:
            f = to_explore[0]
            to_explore = to_explore[1:]
            if f in explored:
                continue
            explored.append(f)
            variables += f.state_variables_read
            to_explore += [c for c in f.calls if\
                           isinstance(c, Function) and c not in explored and c not in to_explore]
            to_explore += [m for m in f.modifiers if m not in explored and m not in to_explore]

        return list(set(variables))

    def all_solidity_variables_read(self):
        """ recursive version of solidity_read
        """
        variables = self.solidity_variables_read
        explored = [self]
        to_explore = [c for c in self.calls if isinstance(c, Function) and c not in explored]
        to_explore += [m for m in self.modifiers if m not in explored]

        while to_explore:
            f = to_explore[0]
            to_explore = to_explore[1:]
            if f in explored:
                continue
            explored.append(f)
            variables += f.solidity_variables_read
            to_explore += [c for c in f.calls if\
                           isinstance(c, Function) and c not in explored and c not in to_explore]
            to_explore += [m for m in f.modifiers if m not in explored and m not in to_explore]

        return list(set(variables))

    def all_expressions(self):
        """ recursive version of variables_read
        """
        variables = self.expressions
        explored = [self]
        to_explore = [c for c in self.calls if isinstance(c, Function) and c not in explored]
        to_explore += [m for m in self.modifiers if m not in explored]

        while to_explore:
            f = to_explore[0]
            to_explore = to_explore[1:]
            if f in explored:
                continue
            explored.append(f)
            variables += f.expressions
            to_explore += [c for c in f.calls if\
                           isinstance(c, Function) and c not in explored and c not in to_explore]
            to_explore += [m for m in f.modifiers if m not in explored and m not in to_explore]

        return list(set(variables))

    def all_variables_written(self):
        """ recursive version of variables_written
        """
        variables = self.state_variables_written
        explored = [self]
        to_explore = [c for c in self.calls if isinstance(c, Function) and c not in explored]
        to_explore += [m for m in self.modifiers if m not in explored]

        while to_explore:
            f = to_explore[0]
            to_explore = to_explore[1:]
            if f in explored:
                continue
            explored.append(f)
            variables += f.state_variables_written
            to_explore += [c for c in f.calls if\
                           isinstance(c, Function) and c not in explored and c not in to_explore]
            to_explore += [m for m in f.modifiers if m not in explored and m not in to_explore]

        return list(set(variables))

    def all_calls(self):
        """ recursive version of calls
        """
        calls = self.calls
        explored = [self]
        to_explore = [c for c in self.calls if isinstance(c, Function) and c not in explored]
        to_explore += [m for m in self.modifiers if m not in explored]

        while to_explore:
            f = to_explore[0]
            to_explore = to_explore[1:]
            if f in explored:
                continue
            explored.append(f)
            calls += f.calls
            to_explore += [c for c in f.calls if\
                           isinstance(c, Function) and c not in explored and c not in to_explore]
            to_explore += [m for m in f.modifiers if m not in explored and m not in to_explore]

        return list(set(calls))

    def is_reading(self, variable):
        """
            Check if the function reads the variable
        Args:
            variable (Variable):
        Returns:
            bool: True if the variable is read
        """
        return variable in self.variables_read

    def is_reading_in_conditional_node(self, variable):
        """
            Check if the function reads the variable in a IF node
        Args:
            variable (Variable):
        Returns:
            bool: True if the variable is read
        """
        variables_read = [n.variables_read for n in self.nodes if n.contains_if()]
        variables_read = [item for sublist in variables_read for item in sublist]
        return variable in variables_read

    def is_reading_in_require_or_assert(self, variable):
        """
            Check if the function reads the variable in an require or assert
        Args:
            variable (Variable):
        Returns:
            bool: True if the variable is read
        """
        variables_read = [n.variables_read for n in self.nodes if n.contains_require_or_assert()]
        variables_read = [item for sublist in variables_read for item in sublist]
        return variable in variables_read

    def is_writing(self, variable):
        """
            Check if the function writes the variable
        Args:
            variable (Variable):
        Returns:
            bool: True if the variable is written
        """
        return variable in self.variables_written

    def apply_visitor(self, Visitor):
        """
            Apply a visitor to all the function expressions
        Args:
            Visitor: slither.visitors
        Returns
            list(): results of the visit
        """
        expressions = self.expressions
        v = [Visitor(e).result() for e in expressions]
        return [item for sublist in v for item in sublist]


    def cfg_to_dot(self, filename):
        """
            Export the function to a dot file
        Args:
            filename (str)
        """
        with open(filename, 'w') as f:
            f.write('digraph{\n')
            for node in self.nodes:
                f.write('{}[label="{}"];\n'.format(node.node_id, str(node)))
                for son in node.sons:
                    f.write('{}->{};\n'.format(node.node_id, son.node_id))

            f.write("}\n")

    def get_summary(self):
        """
            Return the function summary
        Returns:
            (str, str, list(str), list(str), listr(str), list(str);
            name, visibility, modifiers, variables read, variables written, calls
        """
        return (self.name, self.visibility,
                [str(x) for x in self.modifiers],
                [str(x) for x in self.state_variables_read + self.solidity_variables_read],
                [str(x) for x in self.state_variables_written],
                [str(x) for x in self.calls])
