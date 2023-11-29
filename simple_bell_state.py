# File: simple_bell_state.py
#
# Revision History:
# November 14, 2023 - David Shimkus - Initial Version 
# November 27, 2023 - David Shimkus - Removed barrier.

from qiskit import *

def new_simple_bell_circuit():
    q = QuantumRegister(2,'q')
    c = ClassicalRegister(2,'c')
    
    circuit = QuantumCircuit(q,c)

    circuit.h(q[0]) # initialize the superposition of the first "source" qubit
    circuit.cx(q[0],q[1]) # entanglement - bell state

    #circuit.barrier(q)

    circuit.measure(q[0],c[0])
    circuit.measure(q[1],c[1])

    return circuit

