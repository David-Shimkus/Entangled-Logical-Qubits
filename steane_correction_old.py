# File: steane_correction.py
# Demonstrates the 7 qubit error correction code. 
# NOTE: this error correction code requires 6 "ancilla" qubits!  they can be re-used per logical qubit "within reason"
# 
# Revision History 
# August XX, 2023 - David Shimkus - Ported code from previous project.
# September 1X, 2023 - David Shimkus - Changed into GPU implementation.  Noise model introduced.  
# September 23, 2023 - David Shimkus - More parameters and clarity given.  
# September 27, 2023 - David Shimkus - Tightened code.
# September 27, 2023 - David Shimkus - Copied from Shor correction and updated core gate logic for the Steane code.  
# October 9, 2023 - David Shimkus - Revisited this code.  Inspiration: https://stem.mitre.org/quantum/error-correction-codes/steane-ecc.html
# October 25, 2023 - David Shimkus - Tried again.  Used https://arxiv.org/pdf/1306.4532.pdf for decode part.  
# November 1, 2023 - David Shimkus - More work on the decoding part and the syndrome measurement.  https://cs269q.stanford.edu/projects2019/stabilizer_code_report_Y.pdf

import time
start_time = time.time()

import numpy as np

from datetime import datetime
import random 
random.seed(datetime.now().timestamp()) #alternatively random.seed(1234), etc. for constant

from qiskit import *
from qiskit import QuantumRegister
from qiskit import ClassicalRegister
from qiskit import QuantumCircuit
from qiskit.circuit.library import *
from qiskit_aer import AerSimulator
import qiskit_aer.noise as noise
from qiskit_aer.noise import pauli_error

#### circuit "hyper" parameters ######################################

#TODO: wrap into runtime parameters, etc. 
loops = 10
ideal_shots  = loops 
error_shots = 1 # not sure on "parallel shots" - but "shots" runs after most of the heavy lifting is performed
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

        ##### Steane code starts here ########

        my_simulator = AerSimulator(method='statevector',device='GPU',noise_model=noise_model)

        # encode the first logical qubit
        #q = QuantumRegister(18,'q') #shor code demo
        q = QuantumRegister(17,'q') #steane code demo #7 physical qubits per logical qubit, with 3 "ancilla" qubits that get rewashed
        c = ClassicalRegister(14,'c') #we now have a larger classical register because we are measuring syndrome

        circuit = QuantumCircuit(q,c)

        #### this is our precious quantum bell state ##########

        circuit.h(q[0]) #set into superposition
        circuit.cx(q[0],q[7]) #bell state

        ##################################################

        circuit.barrier(q)

        # encode the first logical qubit

        circuit.h(q[4]) #2 #these numberings align with https://cs269q.stanford.edu/projects2019/stabilizer_code_report_Y.pdf
        circuit.h(q[5]) #1
        circuit.h(q[6]) #0

        circuit.cx(q[0],q[1]) #6 (psi), 4
        circuit.cx(q[0],q[2]) #6 (psi), 5

        circuit.cx(q[6],q[0]) #0, 6
        circuit.cx(q[6],q[1]) #0, 4
        circuit.cx(q[6],q[3]) #0, 3
        
        circuit.cx(q[5],q[0]) #1, #6
        circuit.cx(q[5],q[2]) #1, 4
        circuit.cx(q[5],q[3]) #1, 3
        
        circuit.cx(q[4],q[1]) #2, 4
        circuit.cx(q[4],q[2]) #2, 5
        circuit.cx(q[4],q[3]) #2, 3

        circuit.barrier(q)

        # encode the second logical qubit
        # q7 is the second data qubit
        
        circuit.h(q[11]) 
        circuit.h(q[12])
        circuit.h(q[13])

        circuit.cx(q[7],q[8])
        circuit.cx(q[7],q[9])

        circuit.cx(q[13],q[7])
        circuit.cx(q[13],q[8])
        circuit.cx(q[13],q[10])
        
        circuit.cx(q[12],q[7])
        circuit.cx(q[12],q[9])
        circuit.cx(q[12],q[10])
        
        circuit.cx(q[11],q[8])
        circuit.cx(q[11],q[9])
        circuit.cx(q[11],q[10])
        
        circuit.barrier(q)

        #### noisy channel here ############

        # BIT FLIP IN FIRST LOGICAL QUBIT

        circuit.x(q[2]) #bit flip error

        '''
        does_error_occur = random.random()
        error_qubit_index1 = random.randint(0,8)

        if does_error_occur <= error_probability_x:
                circuit.x(q[error_qubit_index1]) #Bit flip error
                num_errors_x = num_errors_x + 1
                
        # PHASE FLIP IN SECOND LOGICAL QUBIT

        does_error_occur = random.random()
        error_qubit_index2 = random.randint(0,8)

        if does_error_occur <= error_probability_z:
                circuit.z(q[error_qubit_index2]) #Phase flip error
                num_errors_z = num_errors_z + 1

        #TODO: CAN ALSO DO THE OTHER LOGICAL QUBIT ! <- THIS HERE IS IMPORTANT

        #circuit.h(q[0]) #set into superposition
        #circuit.cx(q[0],q[9]) #bell state
        '''

        ############################

        circuit.barrier(q)

        #syndrome measurements
        #measurements projected onto q14, q15, q16 (which are rewashed frequently)

        #bit flip detection for the first logical qubit

        circuit.cx(q[0],q[14])
        circuit.cx(q[2],q[14])
        circuit.cx(q[4],q[14])
        circuit.cx(q[6],q[14])

        circuit.cx(q[1],q[15])
        circuit.cx(q[2],q[15])
        circuit.cx(q[5],q[15])
        circuit.cx(q[6],q[15])        

        circuit.cx(q[3],q[16])
        circuit.cx(q[4],q[16])
        circuit.cx(q[5],q[16])
        circuit.cx(q[6],q[16])    

        circuit.measure(q[14],c[2]) #c[2] is for "bit2"
        circuit.measure(q[15],c[3]) #c[3] is for "bit1"
        circuit.measure(q[16],c[4]) #c[4] is for "bit0"

        circuit.barrier(q)

        #clean the qubits for reuse

        circuit.reset(q[14]) 
        circuit.reset(q[15])
        circuit.reset(q[16])

        circuit.barrier(q)

        #phase flip detection for the first logical qubit

        circuit.h(q[14])
        circuit.h(q[15])
        circuit.h(q[16])

        circuit.cx(q[14],q[0])
        circuit.cx(q[14],q[2])
        circuit.cx(q[14],q[4])
        circuit.cx(q[14],q[6])

        circuit.cx(q[15],q[1])
        circuit.cx(q[15],q[2])
        circuit.cx(q[15],q[5])
        circuit.cx(q[15],q[6])

        circuit.cx(q[16],q[3])
        circuit.cx(q[16],q[4])
        circuit.cx(q[16],q[5])
        circuit.cx(q[16],q[6])

        circuit.h(q[14]) 
        circuit.h(q[15])
        circuit.h(q[16])

        circuit.measure(q[14],c[5]) #c[5] is for "phase2"
        circuit.measure(q[15],c[6]) #c[6] is for "phase1"
        circuit.measure(q[16],c[7]) #c[7] is for "phase0"

        circuit.barrier(q)

        #bit flip detection for the second logical qubit

        circuit.cx(q[7],q[14])
        circuit.cx(q[9],q[14])
        circuit.cx(q[11],q[14])
        circuit.cx(q[13],q[14])

        circuit.cx(q[8],q[15])
        circuit.cx(q[9],q[15])
        circuit.cx(q[12],q[15])
        circuit.cx(q[13],q[15])        

        circuit.cx(q[10],q[16])
        circuit.cx(q[11],q[16])
        circuit.cx(q[12],q[16])
        circuit.cx(q[13],q[16])    

        circuit.measure(q[14],c[8]) #c[8] is for "bit2"
        circuit.measure(q[15],c[9]) #c[9] is for "bit1"
        circuit.measure(q[16],c[10]) #c[10] is for "bit0"

        circuit.barrier(q)

        #clean the qubits for reuse

        circuit.reset(q[14]) 
        circuit.reset(q[15])
        circuit.reset(q[16])

        #phase flip detection for the second logical qubit

        circuit.h(q[14])
        circuit.h(q[15])
        circuit.h(q[16])

        circuit.cx(q[14],q[0])
        circuit.cx(q[14],q[2])
        circuit.cx(q[14],q[4])
        circuit.cx(q[14],q[6])

        circuit.cx(q[15],q[1])
        circuit.cx(q[15],q[2])
        circuit.cx(q[15],q[5])
        circuit.cx(q[15],q[6])

        circuit.cx(q[16],q[3])
        circuit.cx(q[16],q[4])
        circuit.cx(q[16],q[5])
        circuit.cx(q[16],q[6])

        circuit.h(q[14]) 
        circuit.h(q[15])
        circuit.h(q[16])

        circuit.measure(q[14],c[11]) #c[11] is for "phase2"
        circuit.measure(q[15],c[12]) #c[12] is for "phase1"
        circuit.measure(q[16],c[13]) #c[13] is for "phase0"

        circuit.barrier(q)

        #adjust the data if needed, based on the syndrome 

        #logical qubit 1 bit flip syndrome: 
        #c[2] is for "bit2"
        #c[3] is for "bit1"
        #c[4] is for "bit0"
        print(c[2],c[3],c[4])


        #logical qubit 1 phase flip syndrome:

        #c[5] is for "phase2"
        #c[6] is for "phase1"
        #c[7] is for "phase0"



        #logical qubit 2 bit flip syndrome: 

        #c[8] is for "bit2"
        #c[9] is for "bit1"
        #c[10] is for "bit0"


        #logical qubit 2 phase flip syndrome: 

        #c[11] is for "phase2"
        #c[12] is for "phase1"
        #c[13] is for "phase0"


        #wash the syndrome qubits again.. we will need them!

        circuit.reset(q[14]) 
        circuit.reset(q[15])
        circuit.reset(q[16])

        circuit.barrier(q)

        #decode the data back from logical qubit 1

        circuit.cx(q[6],q[14]) #q14 will be come the decoded psi for logical qubit 1
        circuit.cx(q[5],q[14])
        circuit.cx(q[0],q[14])
        circuit.cx(q[14],q[1])
        circuit.cx(q[14],q[2])
        circuit.cx(q[14],q[0])

        #decode the data back from logical qubit 2

        #TODO
        

        #read the actual data

        circuit.measure(q[14],c[0])
        circuit.measure(q[15],c[1])

        

        #multi GPU
        backend = AerSimulator(noise_model=noise_model, #coupling_map=coupling_map,
                        basis_gates=basis_gates)
        transpiled_circuit = transpile(circuit, backend)

        result = execute(transpiled_circuit, my_simulator, shots=error_shots,
                blocking_enable=True, blocking_qubits=number_blocking_qubits).result()

        counts = result.get_counts()

        #print('\n')
        #print("----------------------------------------")
        #print("\nSteane code with bit flip and phase error")
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

circuit.draw(output='mpl', filename='steanecode.png')

#running it again with "shots"

result = execute(circuit, my_simulator, shots=ideal_shots, 
                blocking_enable=True, blocking_qubits=number_blocking_qubits,
                basis_gates=basis_gates
        ).result() 

counts = result.get_counts()

#print('\n')
print("Counts using the built in Qiskit 'shots'")
#print("--------------------------------------")
print(counts)

#print('\n')
#print('Shots: ' + str(shots))
#print('Depth: ' + str(depth))
#print('Number of Qubits: ' + str(number_qubits))
#print('Number of "Blocking" Qubits: ' + str(number_blocking_qubits))

print("\nNoisy State with Steane's 7 Qubit Error Correction Code for Logical Qubits:")
print('Number of bit flip errors: ' + str(num_errors_x))
print('Number of phase flip errors: ' + str(num_errors_z))
print('Number of 00 results: ' + str(num_00))
print('Number of 01 results: ' + str(num_01))
print('Number of 10 results: ' + str(num_10))
print('Number of 11 results: ' + str(num_11))

finish_time = time.time() - start_time
print('Time elapsed: ' + str(finish_time) + ' seconds')
