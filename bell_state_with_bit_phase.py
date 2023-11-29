# File: bell_state_with_bit_phase.py
#
# Revision History:
# November 14, 2023 - David Shimkus - Initial Version 
# November 27, 2023 - David Shimkus - Commented out barriers.

from qiskit import *

def new_bit_flip_circuit():
    
    q = QuantumRegister(6,'q')
    c = ClassicalRegister(2,'c')

    circuit = QuantumCircuit(q,c)

    circuit.h(q[0]) # set into superposition
    circuit.cx(q[0],q[3]) # bell state

    #circuit.barrier(q)

    # encode the first logical qubit

    circuit.cx(q[0],q[1])
    circuit.cx(q[0],q[2])

    #circuit.barrier(q)

    # encode the second logical qubit

    circuit.cx(q[3],q[4]) #q3 is the second data qubit
    circuit.cx(q[3],q[5])

    #circuit.barrier(q)

    #TODO: noisy channel could/can go here...

    #circuit.barrier(q)

    #decode the first logical qubit

    circuit.cx(q[0],q[1])
    circuit.cx(q[0],q[2])
    circuit.ccx(q[2],q[1],q[0])

    #decode the second logical qubit

    circuit.cx(q[3],q[4])
    circuit.cx(q[3],q[5])
    circuit.ccx(q[5],q[4],q[3])

    #circuit.barrier(q)

    circuit.measure(q[0],c[0])
    circuit.measure(q[3],c[1])

    return circuit

def new_phase_flip_circuit():
    q = QuantumRegister(6,'q')
    c = ClassicalRegister(2,'c')

    circuit = QuantumCircuit(q,c)

    circuit.h(q[0]) # set into superposition
    circuit.cx(q[0],q[3]) # bell state

    #circuit.barrier(q)

    # encode the first logical qubit

    circuit.cx(q[0],q[1])
    circuit.cx(q[0],q[2])

    circuit.h(q[0])
    circuit.h(q[1])
    circuit.h(q[2])

    #circuit.barrier(q)

    # encode the second logical qubit

    circuit.cx(q[3],q[4]) #q3 is the second data qubit
    circuit.cx(q[3],q[5])

    circuit.h(q[3])
    circuit.h(q[4])
    circuit.h(q[5])

    #circuit.barrier(q)

    #TODO: noisy channel could/can go here...

    #circuit.barrier(q)

    #decode the first logical qubit

    circuit.h(q[0])
    circuit.h(q[1])
    circuit.h(q[2])

    circuit.cx(q[0],q[1])
    circuit.cx(q[0],q[2])
    circuit.ccx(q[2],q[1],q[0])

    #decode the second logical qubit

    circuit.h(q[3])
    circuit.h(q[4])
    circuit.h(q[5])

    circuit.cx(q[3],q[4])
    circuit.cx(q[3],q[5])
    circuit.ccx(q[5],q[4],q[3])

    #circuit.barrier(q)

    circuit.measure(q[0],c[0])
    circuit.measure(q[3],c[1])

    return circuit