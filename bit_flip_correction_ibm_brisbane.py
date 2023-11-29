# File: bit_flip_correction_ibm_brisbane.py
# Demonstrates the 3 qubit phase-flip-only correction code. 
# 
# Revision History
# August XX, 2023 - David Shimkus - Ported code from previous project.
# September 1X, 2023 - David Shimkus - Changed into GPU implementation.  Noise model introduced.  
# September 23, 2023 - David Shimkus - More parameters and clarity given.  
# September 27, 2023 - David Shimkus - Tightened code.
# October 10, 2023 - David Shimkus - Changed to 3 Qubit bit flip code.  
# November 13, 2023 - David Shimkus - Updated for IBM Brisbane execution.  

import time
start_time = time.time()

import numpy as np

from datetime import datetime
import random 
random.seed(datetime.now().timestamp()) #alternatively random.seed(1234) for constant

import qiskit
from qiskit import *
from qiskit import QuantumRegister
from qiskit import ClassicalRegister
from qiskit import QuantumCircuit
from qiskit.circuit.library import *
from qiskit_aer import AerSimulator
import qiskit_aer.noise as noise
from qiskit_aer.noise import pauli_error

print("Imports Successful")
print("Qiskit Version:")
print(qiskit.__qiskit_version__)
print("")

#IBM cloud..
from qiskit import IBMQ

IBMQ.save_account("e37d5b53d616af7d965cdaf92e16755f74470c0e96d7966f07920940a4f3277e9d63d1891599876a5d525857cfc1b3aa73d9d3061ada98f2b2161fda489df7ef")
IBMQ.load_account()
provider = IBMQ.load_account()

backend = provider.get_backend('ibm_brisbane')

#### circuit "hyper" parameters ######################################

loops = 1000

######################################################################
        
q = QuantumRegister(6,'q')
c = ClassicalRegister(2,'c')

circuit = QuantumCircuit(q,c)

#### this is our precious quantum state ##########

circuit.h(q[0]) #set into superposition
circuit.cx(q[0],q[3]) #bell state

##################################################

circuit.barrier(q)

# encode the first logical qubit

circuit.cx(q[0],q[1])
circuit.cx(q[0],q[2])

circuit.barrier(q)

# encode the second logical qubit

circuit.cx(q[3],q[4]) #q3 is the second data qubit
circuit.cx(q[3],q[5])

circuit.barrier(q)

#### noisy channel here ############

# BIT FLIP IN EITHER THE FIRST OR SECOND LOGICAL QUBIT

#does_error_occur = random.random()
#error_qubit_index1 = random.randint(0,5)

#if does_error_occur <= error_probability_x:
#        circuit.x(q[error_qubit_index1]) #Bit flip error
#        num_errors_x = num_errors_x + 1

# PHASE FLIP IN EITHER THE FIRST OR SECOND LOGICAL QUBIT
'''
does_error_occur = random.random()
error_qubit_index2 = random.randint(0,5)

if does_error_occur <= error_probability_z:
        circuit.z(q[error_qubit_index2]) #Phase flip error
        num_errors_z = num_errors_z + 1
'''
############################

circuit.barrier(q)

#decode the first logical qubit

circuit.cx(q[0],q[1])
circuit.cx(q[0],q[2])
circuit.ccx(q[2],q[1],q[0])

#decode the second logical qubit

circuit.cx(q[3],q[4])
circuit.cx(q[3],q[5])
circuit.ccx(q[5],q[4],q[3])

circuit.barrier(q)

circuit.measure(q[0],c[0])
circuit.measure(q[3],c[1])

#IBM cloud
transpiled_circuit = transpile(circuit, backend)

#generated image may be too large
transpiled_circuit.draw(output='mpl', filename='bit_flip_brisbane_transpiled.png', fold=-1)
print("Number of operations for 'Brisbane Transpiled Circuit':")
print(dict(transpiled_circuit.count_ops()))

job = backend.run(transpiled_circuit, shots=loops)
counts = job.result().get_counts()

#print('\n')
print("Counts using the built in Qiskit 'shots'")
#print("--------------------------------------")
print(counts)

finish_time = time.time() - start_time
print('Time elapsed: ' + str(finish_time) + ' seconds')
