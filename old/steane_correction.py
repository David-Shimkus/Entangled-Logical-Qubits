# File: steane_correction.py
# Demonstrates the 7 qubit error correction code. 
#
# This is a [[7,1,3]] code, which derives from a classical Hamming Code of [7,4,3].
# The first parameter 'n' is the length of the ENCODED word.
# The second parameter is the length of the SOURCE word.
# The final parameter is sometimes optional... and it is the "distance" parameter.
# This distance parameter is the number of differences it takes between source and encoded for the scheme to fall apart.  
#
# Revision History:
# September 19, 2023 - David Shimkus - Initial installation.
# September 2X, 2023 - David Shimkus - Various tweaks.  
# September 25, 2023 - David Shimkus - Rewrote final section - numerous comments for clarity added.  

import time
start_time = time.time()

import numpy as np

from qiskit import *
from qiskit import QuantumRegister
from qiskit import ClassicalRegister
from qiskit import QuantumCircuit
from qiskit.circuit.library import *
from qiskit_aer import AerSimulator
import qiskit_aer.noise as noise

#### circuit "hyper" parameters ######################################
shots  = 100
depth  = 10
#number_qubits = 28 #max that can be done on two T600's it seems 
#number_qubits = 24

# Sets the number of qubits of chunk size used for parallelizing with multiple GPUs or multiple processes with MPI (CPU/GPU).
# 16*2^blocking_qubits should be less than 1/4 of the GPU memory in double precision. 
# set this parameter to satisfy sizeof(complex)*2^(blocking_qubits+4) < size of the smallest memory space in byte.
# with two T600's the highest this can go is 22... if complex numbers are 16 bytes then 16 * (2^22) = 67108864 < 4096 * 2
number_blocking_qubits = 20   

my_simulator = AerSimulator(method='statevector',device='GPU')
#my_simulator = AerSimulator(method='statevector')
######################################################################

#### error parameters ################################################
#Inspiration: https://qiskit.org/ecosystem/aer/apidocs/aer_noise.html

prob_1 = 0.00  # 1-qubit gate - this can be set to 0.001 for "regular" testing
prob_2 = 0.00  # 2-qubit gate - this can be set to 0.010 for "regular" testing 

# depolarizing quantum errors
error_1 = noise.depolarizing_error(prob_1, 1) 
error_2 = noise.depolarizing_error(prob_2, 2) 

# add the errors to the "noise model"
noise_model = noise.NoiseModel()
noise_model.add_all_qubit_quantum_error(error_1, ['u1', 'u2', 'u3'])
noise_model.add_all_qubit_quantum_error(error_2, ['cx'])

# get basis gates from noise model - these are passed in as a parameter to the execution
# basis gates are "normal" gates used in circuit construction 
basis_gates = noise_model.basis_gates

######################################################################

#### Steane code follows #############################################
# inspiration: https://github.com/KnightShuffler/Steane-Code-in-Qiskit/blob/main/task2.ipynb

def error_correction(qc, x_ancillas, z_ancillas, logical_qubit, x_syndrome, z_syndrome):
    # make sure inputs are valid
    if not isinstance(qc, QuantumCircuit):
        raise TypeError("'qc', should be a QuantumCircuit")
    
    if not isinstance(x_ancillas, QuantumRegister):
        raise TypeError("'x_ancillas' should be a QuantumRegister")
    elif x_ancillas.size != 3:
        raise TypeError("'x_ancillas' must have 3 qubits")
        
    if not isinstance(z_ancillas, QuantumRegister):
        raise TypeError("'z_ancillas' should be a QuantumRegister")
    elif z_ancillas.size != 3:
        raise TypeError("'z_ancillas' must have 3 qubits")
    
    if not isinstance(logical_qubit, QuantumRegister):
        raise TypeError("'logical_qubit' should be a QuantumRegister")
    elif logical_qubit.size != 7:
        raise TypeError("'logical_qubit' must have 7 qubits")
    
    if not isinstance(x_syndrome, ClassicalRegister):
        raise TypeError("'x_syndrome' should be a ClassicalRegister")
    elif x_syndrome.size != 3:
        raise TypeError("'x_syndrome' must have 3 bits")
        
    if not isinstance(z_syndrome, ClassicalRegister):
        raise TypeError("'z_syndrome' should be a ClassicalRegister")
    elif z_syndrome.size != 3:
        raise TypeError("'z_syndrome' must have 3 bits")
        
    # initialize the ancillas (ancillae?) to |0>
    for i in range(3):
        qc.initialize([1,0], x_ancillas[i]) # recall the matrix notation of |0>
        qc.initialize([1,0], z_ancillas[i])
        
    # apply Hadamard to the ancillas
    qc.h(x_ancillas)
    qc.h(z_ancillas)
    
    # controlled g_i: 

    # g1, g2, g3 read left to right as binary integer tell us the index of the qubit to apply corrective Z gate to
    qc.cx(z_ancillas[2], [logical_qubit[i-1] for i in [4,5,6,7]]) # Controlled g1
    qc.cx(z_ancillas[1], [logical_qubit[i-1] for i in [2,3,6,7]]) # Controlled g2
    qc.cx(z_ancillas[0], [logical_qubit[i-1] for i in [1,3,5,7]]) # Controlled g3
    
    # g4, g5, g6 read left to right as binary integer tell us the index of the qubit to apply corrective X gate to
    qc.cz(x_ancillas[2], [logical_qubit[i-1] for i in [4,5,6,7]]) # Controlled g4
    qc.cz(x_ancillas[1], [logical_qubit[i-1] for i in [2,3,6,7]]) # Controlled g5
    qc.cz(x_ancillas[0], [logical_qubit[i-1] for i in [1,3,5,7]]) # Controlled g6
    
    # apply Hadamard to the ancillas (ancillae?) again
    qc.h(x_ancillas)
    qc.h(z_ancillas)
    
    # measure the ancillae
    qc.measure(x_ancillas, x_syndrome)
    qc.measure(z_ancillas, z_syndrome)
    
    # apply the corrective X gates IF THE SYNDROME DEMANDS IT (note the c_if)
    for i in range(1,8):
        qc.x(logical_qubit[i-1]).c_if(x_syndrome,i)
    
    # apply the corrective Z gates
    for i in range(1,8):
        qc.z(logical_qubit[i-1]).c_if(z_syndrome,i)

# adds the logical Hadamard  gate to a QuantumCircuit qc
def logical_h(qc, logical_qubit):
    if not isinstance(qc, QuantumCircuit):
        raise TypeError("'qc', should be a QuantumCircuit")
        
    if not isinstance(logical_qubit, QuantumRegister):
        raise TypeError("'logical_qubit' should be a QuantumRegister")
    elif logical_qubit.size != 7:
        raise TypeError("'logical_qubit' must have 7 qubits")

    qc.h(logical_qubit)

# adds the logical CNOT gate to a QuantumCircuit qc with logical qubit 'control' as the control and 'target' as target
def logical_cx(qc, control, target):
    if not isinstance(qc, QuantumCircuit):
        raise TypeError("'qc', should be a QuantumCircuit")
        
    if not isinstance(control, QuantumRegister):
        raise TypeError("'control' should be a QuantumRegister")
    elif control.size != 7:
        raise TypeError("'control' must have 7 qubits")
    
    if not isinstance(control, QuantumRegister):
        raise TypeError("'control' should be a QuantumRegister")
    elif control.size != 7:
        raise TypeError("'control' must have 7 qubits")

    for i in range(7):
        qc.cx(control[i],target[i])

# measures logical_qubit in the Z basis using ancilla, in the circuit qc
def logical_z_measure(qc, ancilla, logical_qubit, measurement):
    # make sure the inputs are valid
    if not isinstance(qc, QuantumCircuit):
        raise TypeError("'qc' should be a QuantumCircuit")
    
    if not isinstance(ancilla, QuantumRegister):
        raise TypeError("'ancilla' should be a QuantumRegister")
    elif ancilla.size != 1:
        raise TypeError("'ancilla' must have 1 qubit")
    
    if not isinstance(logical_qubit, QuantumRegister):
        raise TypeError("'logical_qubit'should be a QuantumRegister")
    elif logical_qubit.size != 7:
        raise TypeError("'logical_qubit' must have 7 qubits")
    
    if not isinstance(measurement, ClassicalRegister):
        raise TypeError("'measurement' should be a ClassicalRegister")
    elif measurement.size != 1:
        raise TypeError("'measurement' must have 1 bit")
        
    # Initialize ancilla to |0>
    qc.initialize([1,0],ancilla)
    
    # Apply Hadamard to ancilla
    qc.h(ancilla)
    # Apply controlled logical-Z
    for i in range(7):
        qc.cz(ancilla, logical_qubit[i])
    # Apply Hadamard to ancilla
    qc.h(ancilla)
    
    # Measure the ancilla
    qc.measure(ancilla, measurement)

lq     = QuantumRegister(7)
x_anc  = QuantumRegister(3)
x_syn  = ClassicalRegister(3)
z_anc  = QuantumRegister(3)
z_syn  = ClassicalRegister(3)

qc = QuantumCircuit(x_anc,z_anc,lq,x_syn,z_syn)
error_correction(qc, x_anc, z_anc, lq, x_syn, z_syn)

qc.save_statevector()

#multi GPU
result = execute(qc, my_simulator, shots=shots, 
        blocking_enable=True, blocking_qubits=number_blocking_qubits).result() 
#result = execute(qc, my_simulator).result()

sv = result.get_statevector()

# list that holds the computational basis vector names where the amplitude is non-zero
indices = []       
for i in range(len(sv)):
    if sv[i] != 0:
        # store the index as a 10-bit long binary number
        indices.append( ((str(bin(i)[2:]).zfill(3+7)),sv[i]) )

print('Number of kets in superposition: ', len(indices))
print("Kets in superposition:")
for i in indices:
    print('Ket:', i[0][0:7][::-1], '--- Amplitude:', i[1] ) # Extract the 7 left-most bits of the number, 
                                                            # reverse them (for consistency with the notes)
                                                            # and print the amplitude of the ket

print('\nsqrt[1/8] =',np.sqrt(1/8))                        # To verify the amplitudes are correct




counts = result.get_counts()

print('\n')
print("Uncorrected bit flip and phase error")
print("--------------------------------------")
print(counts)
print("--------------------------------------")


#####Steane code starts here ########
#https://github.com/KnightShuffler/Steane-Code-in-Qiskit/blob/main/task2.ipynb
q = QuantumRegister(9,'q')
c = ClassicalRegister(1,'c')

circuit = QuantumCircuit(q,c)



circuit.barrier(q)

circuit.measure(q[0],c[0])

#multi GPU
backend = AerSimulator(noise_model=noise_model, #coupling_map=coupling_map,
                       basis_gates=basis_gates)
transpiled_circuit = transpile(circuit, backend)

result = execute(transpiled_circuit, my_simulator, shots=shots,
        blocking_enable=True, blocking_qubits=number_blocking_qubits).result()

counts = result.get_counts()

print('\n')
print("----------------------------------------")
print("\nSteane code with bit flip and phase error")
print("----------------------------------------")
print(counts)

circuit.draw(output='mpl', filename='steanecode.png')

print('\n')
print('Shots: ' + str(shots))
print('Depth: ' + str(depth))
print('Number of Qubits: ' + str(number_qubits))
print('Number of "Blocking" Qubits: ' + str(number_blocking_qubits))

finish_time = time.time() - start_time
print('Time: ' + str(finish_time) + ' seconds')
