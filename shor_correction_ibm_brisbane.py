# File: shor_correction.py
# Demonstrates the 9 qubit error correction code. 
# 
# Revision History
# August XX, 2023 - David Shimkus - Ported code from previous project.
# September 1X, 2023 - David Shimkus - Changed into GPU implementation.  Noise model introduced.  
# September 23, 2023 - David Shimkus - More parameters and clarity given.  
# September 27, 2023 - David Shimkus - Tightened code.
# October 9, 2023 - David Shimkus - Restructured to use "logical" entanglement.  Revisited the seeding of errors to include both logical qubits.  Started Campus Cluster work again.  

import time
start_time = time.time()

import numpy as np

from datetime import datetime
import random 
random.seed(datetime.now().timestamp()) #alternatively random.seed(1234) for constant

from qiskit import *
from qiskit import QuantumRegister
from qiskit import ClassicalRegister
from qiskit import QuantumCircuit
from qiskit.circuit.library import *
from qiskit_aer import AerSimulator
import qiskit_aer.noise as noise
from qiskit_aer.noise import pauli_error

#IBM cloud..
from qiskit import IBMQ

IBMQ.save_account("e37d5b53d616af7d965cdaf92e16755f74470c0e96d7966f07920940a4f3277e9d63d1891599876a5d525857cfc1b3aa73d9d3061ada98f2b2161fda489df7ef")
IBMQ.load_account()
provider = IBMQ.load_account()

backend = provider.get_backend('ibm_brisbane')

#### circuit "hyper" parameters ######################################

loops = 100
ideal_shots  = loops 
num_loops = loops # Dr. Gamage requested this - it also works better with the "force simulated" errors

######################################################################

print("Demonstration of two entangled qubits and the Bell State.")
print("Sampled",loops,"times.")

print("\nIdeal State:")

error_probability_x = 0.5 # bit flip
error_probability_z = 0.3 # phase flip
error_probability_y = 0.1 # bit AND phase flip

print("Custom error probability for bit flip: ", error_probability_x)

num_errors_x = 0
num_errors_z = 0
num_00 = 0
num_01 = 0
num_10 = 0
num_11 = 0

#IBM Brisbane
q = QuantumRegister(18,'q')
c = ClassicalRegister(2,'c')

circuit = QuantumCircuit(q,c)

circuit.h(q[0]) #initialize the superposition
#two X's is logically the same thing as #circuit.id(q[0]) - this does nothing when compiled!
#circuit.x(q[0])
circuit.cx(q[0],q[1])

circuit.barrier(q)

#encode the first logical qubit

circuit.cx(q[0],q[3])
circuit.cx(q[0],q[6])

circuit.h(q[0])
circuit.h(q[3])
circuit.h(q[6])

circuit.cx(q[0],q[1])
circuit.cx(q[3],q[4])
circuit.cx(q[6],q[7])

circuit.cx(q[0],q[2])
circuit.cx(q[3],q[5])
circuit.cx(q[6],q[8])

circuit.barrier(q)

# encode the second logical qubit

circuit.cx(q[9],q[12]) #q9 is the second data qubit
circuit.cx(q[9],q[15])

circuit.h(q[9])
circuit.h(q[12])
circuit.h(q[15])

circuit.cx(q[9],q[10])
circuit.cx(q[12],q[13])
circuit.cx(q[15],q[16])

circuit.cx(q[9],q[11])
circuit.cx(q[12],q[14])
circuit.cx(q[15],q[17])

circuit.barrier(q)

#decode the first logical qubit

circuit.cx(q[0],q[1])
circuit.cx(q[3],q[4])
circuit.cx(q[6],q[7])

circuit.cx(q[0],q[2])
circuit.cx(q[3],q[5])
circuit.cx(q[6],q[8])

circuit.ccx(q[1],q[2],q[0])
circuit.ccx(q[4],q[5],q[3])
circuit.ccx(q[8],q[7],q[6])

circuit.h(q[0])
circuit.h(q[3])
circuit.h(q[6])

circuit.cx(q[0],q[3])
circuit.cx(q[0],q[6])
circuit.ccx(q[6],q[3],q[0])

#decode the second logical qubit

circuit.cx(q[9],q[10])
circuit.cx(q[12],q[13])
circuit.cx(q[15],q[16])

circuit.cx(q[9],q[11])
circuit.cx(q[12],q[14])
circuit.cx(q[15],q[13])

circuit.ccx(q[10],q[11],q[9])
circuit.ccx(q[13],q[14],q[12])
circuit.ccx(q[17],q[16],q[15])

circuit.h(q[9])
circuit.h(q[12])
circuit.h(q[15])

circuit.cx(q[9],q[12])
circuit.cx(q[9],q[15])
circuit.ccx(q[15],q[12],q[9])

circuit.barrier(q)

circuit.measure(q[0],c[0])
circuit.measure(q[1],c[1])

#IBM cloud
#job = backend.run(transpile(circuit, backend), shots=ideal_shots)
job = backend.run(transpile(circuit, backend), shots=ideal_shots)

counts = job.result().get_counts()

#print('\n')
print("Counts using the built in Qiskit 'shots'")
#print("--------------------------------------")
print(counts)
#print("--------------------------------------")
finish_time = time.time() - start_time
print('Time elapsed: ' + str(finish_time) + ' seconds')
