# File: shor_correction.py
# Demonstrates the 9 qubit error correction code. 
# 
# Revision History
# August XX, 2023 - David Shimkus - Ported code from previous project.
# September 1X, 2023 - David Shimkus - Changed into GPU implementation.  Noise model introduced.  
# September 23, 2023 - David Shimkus - More parameters and clarity given.  
# September 27, 2023 - David Shimkus - Tightened code.
# November 10, 2023 - David Shimkus - Adjusted output diagram to not wrap.  Fixed bug in "bet" logical qubit.  

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

#### circuit "hyper" parameters ######################################

loops = 100
ideal_shots  = loops 
error_shots = 1
num_loops = loops # Dr. Gamage requested this - it also works better with the "force simulated" errors
#depth  = 10
#number_qubits = 28 #max that can be done on two T600's it seems 
#number_qubits = 24
number_blocking_qubits = 22 #GPU specific parameter

######################################################################

#### error parameters ################################################
#https://qiskit.org/ecosystem/aer/apidocs/aer_noise.html
#https://qiskit.org/ecosystem/aer/tutorials/3_building_noise_models.html

prob_1 = 0.00 # 1-qubit gate
prob_2 = 0.00 # 2-qubit gate

#p_meas = 0.50

# Depolarizing quantum errors
error_1 = noise.depolarizing_error(prob_1, 1)
error_2 = noise.depolarizing_error(prob_2, 2)

#prob_x = 0.50 # bit flip
#prob_z = 0.00 # phase flip

# "normal" errors 
bit_flip = pauli_error([('X', prob_1), ('I', 1 - prob_1)])
#phase_flip = pauli_error([('Z', prob_z), ('I', 1 - prob_z)])
# Compose two bit-flip and phase-flip errors
#bitphase_flip = bit_flip.compose(phase_flip)

# Add errors to noise model
noise_model = noise.NoiseModel()

#noise_model.add_all_qubit_quantum_error(error_1, ['u1', 'u2', 'u3'])
#noise_model.add_all_qubit_quantum_error(error_2, ['cx'])
#noise_model.add_all_qubit_quantum_error(error_1, ['x'])
#error_measure = pauli_error([('X',p_meas), ('I', 1 - p_meas)])
#noise_model.add_all_qubit_quantum_error(error_measure, "measure")

#noise_model.add_all_qubit_quantum_error(bit_flip, "bit_flip")
noise_model.add_all_qubit_quantum_error(bit_flip, ['u1', 'u2', 'u3']) # refer to the "General" unitary matrix
#noise_model.add_all_qubit_quantum_error(phase_flip, "phase_flip")
#noise_model.add_all_qubit_quantum_error(bitphase_flip, "bitphase_flip")

# Get basis gates from noise model - these can be used as additional building blocks
basis_gates = noise_model.basis_gates

print("Demonstration of two entangled qubits and the Bell State.")
print("Sampled",loops,"times.")

print("\nIdeal State:")

print("Qiskit noise model: ",noise_model)

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

##### "Ideal" (no errors) starts here ########

my_simulator = AerSimulator(method='statevector',device='GPU',noise_model=noise_model)
#my_simulator = AerSimulator(method='statevector')

#demonstrate the noise model
q = QuantumRegister(2,'q')
c = ClassicalRegister(2,'c')

circuit = QuantumCircuit(q,c)

circuit.h(q[0]) #initialize the superposition
#two X's is logically the same thing as #circuit.id(q[0]) - this does nothing when compiled!
#circuit.x(q[0])
circuit.cx(q[0],q[1])

#### noisy channel here ####
#circuit.x(q[0]) # example bit flip
#circuit.z(q[0]) # example phase flip
############################

circuit.barrier(q)

circuit.measure(q[0],c[0])
circuit.measure(q[1],c[1])

#multi GPU
result = execute(circuit, my_simulator, shots=ideal_shots, 
                blocking_enable=True, blocking_qubits=number_blocking_qubits,
                basis_gates=basis_gates
        ).result() 

counts = result.get_counts()

#print('\n')
print("Counts using the built in Qiskit 'shots'")
#print("--------------------------------------")
print(counts)
#print("--------------------------------------")
finish_time = time.time() - start_time
print('Time elapsed: ' + str(finish_time) + ' seconds')

start_time = time.time() #reset timer
for i in range(num_loops):

        ##### Shor code starts here ########
        # heavily modified from https://quantumcomputinguk.org/tutorials/quantum-error-correction-shor-code-in-qiskit

        my_simulator = AerSimulator(method='statevector',device='GPU',noise_model=noise_model)

        # encode the first logical qubit
        q = QuantumRegister(18,'q')
        #q = QuantumRegister(28,'q')
        c = ClassicalRegister(2,'c')

        circuit = QuantumCircuit(q,c)

        #### this is our precious quantum state ##########

        circuit.h(q[0]) #set into superposition
        circuit.cx(q[0],q[9]) #bell state

        ##################################################

        circuit.barrier(q)

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

        #### noisy channel here ############

        # BIT FLIP IN FIRST LOGICAL QUBIT

        #does_error_occur = random.random()
        #error_qubit_index1 = random.randint(0,8)

        #if does_error_occur <= error_probability_x:
        #        circuit.x(q[error_qubit_index1]) #Bit flip error
        #        num_errors_x = num_errors_x + 1
                
        # PHASE FLIP IN SECOND LOGICAL QUBIT

        #does_error_occur = random.random()
        #error_qubit_index2 = random.randint(0,8)

        #if does_error_occur <= error_probability_z:
        #        circuit.z(q[error_qubit_index2]) #Phase flip error
        #        num_errors_z = num_errors_z + 1

        #TODO: CAN ALSO DO THE OTHER LOGICAL QUBIT ! <- THIS HERE IS IMPORTANT

        #circuit.h(q[0]) #set into superposition
        #circuit.cx(q[0],q[9]) #bell state

        ############################

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
        circuit.cx(q[15],q[17])

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
        circuit.measure(q[9],c[1])

        #multi GPU
        backend = AerSimulator(noise_model=noise_model, #coupling_map=coupling_map,
                        basis_gates=basis_gates)
        transpiled_circuit = transpile(circuit, backend)

        result = execute(transpiled_circuit, my_simulator, shots=error_shots,
                blocking_enable=True, blocking_qubits=number_blocking_qubits).result()

        counts = result.get_counts()

        #print('\n')
        #print("----------------------------------------")
        #print("\nShor code with bit flip and phase error")
        #print("----------------------------------------")
        #print(counts)

        #TODO: there are better ways to do this...
        key, value = list(counts.items())[0]
        #print(key)
        if key == '00':
                num_00 = num_00 + 1
        if key == '01':
                num_01 = num_01 + 1
        if key == '10':
                num_10 = num_10 + 1
        if key == '11':
                num_11 = num_11 + 1

circuit.draw(output='mpl', filename='shorcode.png', fold=-1)

#print('\n')
#print('Shots: ' + str(shots))
#print('Depth: ' + str(depth))
#print('Number of Qubits: ' + str(number_qubits))
#print('Number of "Blocking" Qubits: ' + str(number_blocking_qubits))

print("\nNoisy State with Shor's 9 Qubit Error Correction Code for Logical Qubits:")
print('Number of bit flip errors: ' + str(num_errors_x))
print('Number of phase flip errors: ' + str(num_errors_z))
print('Number of 00 results: ' + str(num_00))
print('Number of 01 results: ' + str(num_01))
print('Number of 10 results: ' + str(num_10))
print('Number of 11 results: ' + str(num_11))

finish_time = time.time() - start_time
print('Time elapsed: ' + str(finish_time) + ' seconds')
