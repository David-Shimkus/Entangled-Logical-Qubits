# File: multi_gpu_test_benchmark.py
# gpu_test.py

import time
start_time = time.time()

import numpy as np

from qiskit import *
from qiskit.circuit.library import *
from qiskit_aer import AerSimulator

#my_simulator = AerSimulator(method='statevector',device='GPU')
my_simulator = AerSimulator(method='statevector')

shots  = 100
depth  = 10
#number_qubits = 28 #max that can be done on two T600's it seems 
number_qubits = 24
number_blocking_qubits = 22

my_circuit = QuantumVolume(number_qubits, depth, seed=12354)
my_circuit.measure_all()
my_circuit = transpile(my_circuit,my_simulator) #I am not sure what transpile does yet



#result = my_simulator.run(my_circuit, shots=shots, seed_simulator=12345).result() #this works OK 

#result = execute(my_circuit, my_simulator, shots=shots, block_enable=True, blocking_qubits=5).result()

#result=execute(circuit,sim,shots=shots,seed_simulator=12345).result()

#result = execute(my_circuit, my_simulator, shots=shots).result() #single GPU

#multi GPU
result = execute(my_circuit, my_simulator, shots=shots, 
        blocking_enable=True, blocking_qubits=number_blocking_qubits).result() 

print('Shots: ' + str(shots))
print('Depth: ' + str(depth))
print('Number of Qubits: ' + str(number_qubits))
print('Number of "Blocking" Qubits: ' + str(number_blocking_qubits))

finish_time = time.time() - start_time
print('Time: ' + str(finish_time) + ' seconds')
