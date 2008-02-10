#!/usr/bin/python
#
#
# Generate a C include file from a finite state machine definition.
#
# Right now the form is the one expected by htmlparser.c so this file is pretty
# tightly coupled with htmlparser.c.
#

__author__ = 'falmeida@google.com (Filipe Almeida)'

import sys
import getopt

TABSTOP = 2

class FSMGenerator(object):

  sm = {}  # dictionary that contains the finite state machine definition
           # loaded from a config file.

  def prefix(self):
    """ return a c declaration prefix """

    return self.sm['name'].lower() + '_'

  def c_state_internal(self, st):
    """ return the internal name of the state """

    return "%sSTATE_INT_%s" % (self.prefix().upper(), st.upper())

  def c_state_external(self, st):
    """ return the external name of the state """

    return "%sSTATE_%s" % (self.prefix().upper(), st.upper())

  def tab(self):
    """ Returns an expanded tab string """
    return "\t".expandtabs(TABSTOP)

  def make_tuple(self, data):
    """ converts data to a string representation of a c tuple to be inserted
    into a list.
    """

    return "%s{ %s }" % (self.tab(), ', '.join(data))

  def print_header(self):
    """ Print the include file header """

    if 'comment' in self.sm:
      print "/* " + self.sm['comment']
    else:
      print "/* State machine definition for " + self.sm['name']
    print " * Auto generated by generate_fsm.py. Please do not edit."
    print " */"
    print

  def print_enum(self, name, data):
    """ Print a c enum definition """
    list = []  # output list

    print "enum %s {" % name

    for e in data:
      list.append(self.tab() + e)
    print ",\n".join(list) + "\n};\n"


  def print_struct_list(self, name, type, data):
    """ Print a c flat list.

    Generic function to print list in c in the form of a struct.

    Args:
      name: name of the structure.
      type: type of the struct.
      data: contents of the struct as a list of elements
    """
    list = []  # output list

    print "static const %s %s[] = {" % (type, name)

    for e in data:
      list.append(self.tab() + e)
    print ",\n".join(list)
    print "};\n"


  def print_struct_list2(self, name, type, data):
    """ Print a c list of lists.
 
    Generic function to print a list of lists in c in the form of a struct.

    Args:
      name: name of the structure.
      type: type of the struct.
      data: contents of the struct as a list of lists.
    """
    list = []  # output list

    print "static const %s %s[] = {" % (type, name)

    for e in data:
      list.append(self.make_tuple(e))
    print ",\n".join(list)
    print "};\n"


  def print_states_enum(self):
    """ Print the internal states enum

    Prints an enum containing all the valid states.
    """
    list = []  # output list

    for (state, external) in self.sm['states']:
      list.append(self.c_state_internal(state))
    self.print_enum(self.prefix() + 'state_internal_enum', list)


  def print_states_external(self):
    """ Print a struct with a mapping from internal to external states """
    list = []  # output list

    for (state, external) in self.sm['states']:
      list.append(self.c_state_external(external))

    self.print_struct_list(self.prefix() + 'states_external', 'int', list)

  def print_transitions(self):
    """ Print the state transition list.

    Prints a structure that fills the following struct definition based on a
    list of (condition, source, destination) tuples stored in a variable named
    transitions:

    struct statetable_transitions_s {
      const char *condition;
      state source;
      state destination;
    };

    The conditions are mapped from the conditions variable.
    The resulting list is reversed as htmlparser.c expectes the list in
    reversed order of execution, and an terminator is added:

    { NULL, STATEMACHINE_ERROR, STATEMACHINE_ERROR }
    """
    list = []          # output list
    conditions_h = {}  # mapping of condition name to condition expression

    for name, value in self.sm['conditions']:
      conditions_h[name] = value

    for e in self.sm['transitions']:
      (condition, src, dst) = e
      new_condition = '"%s"' % conditions_h[condition]
      list.append([new_condition,
                   self.c_state_internal(src),
                   self.c_state_internal(dst)
                   ])

    list.reverse() # The include appears in reversed order
    list.append(['NULL', 'STATEMACHINE_ERROR', 'STATEMACHINE_ERROR'])

    self.print_struct_list2(self.prefix() + 'state_transitions',
                            'struct statetable_transitions_s', list)

  def load(self, filename):
    """ Load the state machine definition file.

    In the file, the following variables are defined.

    name: name of the state machine
    conditions: a mapping between condition names and bracket expressions.
    states: lists of tuples containing the internal state name and the
    respective external super state.
    transitions: list of tuples in the form (condition, source state,xi
    destination state) defining the transition table.

    Example:

    name = 'c comment parser'
    
    states = [
      ['text',             'text'],    # main js body
      ['comment',          'comment'], # / start of a comment
      ['comment_ln',       'comment'], # // single line comments
      ['comment_ml',       'comment'], # /* start of multiline comment
      ['comment_ml_close', 'comment']  # */ end of multiline comment
    ]
    
    conditions = [
      ['/',       '/'],
      ['*',       '*'],
      ['lf',      '\\n'],
      ['default', '[:default:]']
    ]

    transitions = [
      ['/',       'text',              'comment'],

      ['/',       'comment',           'comment_ln'],
      ['*',       'comment',           'comment_ml'],
      ['default', 'comment',           'text'],

      ['lf',      'comment_ln',        'text'],
      ['default', 'comment_ln',        'comment_ln'],

      ['*',       'comment_ml',        'comment_ml_close'],
      ['default', 'comment_ml',        'comment_ml'],

      ['/',       'comment_ml_close',  'text'],

      ['default', 'comment_ml_close',  'comment_ml'],
    ]

    """

    execfile(filename, self.sm)

  def print_num_states(self):
    """ Print a Macro defining the number of states. """

    print "#define %s_NUM_STATES %s\n" % (self.sm['name'].upper(),
                                          str(len(self.sm['states'])))

  def generate(self):
    self.print_header()
    self.print_num_states()
    self.print_states_enum()
    self.print_states_external()
    self.print_transitions()

  def __init__(filename):
    pass

def main():

  gen = FSMGenerator()
  if len(sys.argv) != 2:
    print "usage: generate_fsm.py config_file"
    sys.exit(1)

  gen.load(sys.argv[1])
  gen.generate()


if __name__ == "__main__":
    main()