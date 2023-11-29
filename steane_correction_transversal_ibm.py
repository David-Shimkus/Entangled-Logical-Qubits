# File: steane_correction_transversal_ibm.py
# Demonstrates the 7 qubit error correction code with two entangled logical qubits forming a Bell State.  
# NOTE: this error correction code requires 7 physical qubits to form one logical qubit!  
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
# November 2, 2023 - David Shimkus - Massive overhaul of syndrome measurements.  No longer reading to classical register.  "In-place" correction implemented.  
# November 8, 2023 - David Shimkus - More work on the decoding syndrome.  
# November 10, 2023 - David Shimkus - It is finally working.  
# November 13, 2023 - David Shimkus - Transversal implementation.
# November 13, 2023 - David Shimkus - IBM Brisbane implementation.  Cleaned code and removed extraneous runs.      

import time
start_time = time.time()

import numpy as np

from datetime import datetime
import random 
random.seed(datetime.now().timestamp()) #alternatively random.seed(1234), etc. for constant

import qiskit
from qiskit import *
from qiskit import QuantumRegister
from qiskit import ClassicalRegister
from qiskit import QuantumCircuit
from qiskit.circuit.library import *
from qiskit_aer import AerSimulator
import qiskit_aer.noise as noise
from qiskit_aer.noise import pauli_error
from qiskit.circuit.library.standard_gates import C3XGate
#from qiskit.circuit.library.standard_gates import C3ZGate #this did not work, but for future reference: Z=HXH

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
#backend = provider.get_backend('ibmq_sherbrooke')


#### circuit "hyper" parameters ######################################

#TODO: wrap into runtime parameters, etc. 
loops = 100 
######################################################################

start_time = time.time() #reset timer

##### Steane code starts here ########

# encode the first logical qubit
q = QuantumRegister(17,'q') #steane code demo 7 physical qubits per logical qubit, with 3 "ancilla" qubits that get rewashed
c = ClassicalRegister(2,'c') #for reading out our bell state

circuit = QuantumCircuit(q,c)

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

#the "logical"/transversal operations below 
#this is a "logical" way of implementing the quantum bell state

circuit.h(q[0])
circuit.h(q[1])
circuit.h(q[2])
circuit.h(q[3])
circuit.h(q[4])
circuit.h(q[5])
circuit.h(q[6])
circuit.cx(q[0],q[7])
circuit.cx(q[1],q[8])
circuit.cx(q[2],q[9])
circuit.cx(q[3],q[10])
circuit.cx(q[4],q[11])
circuit.cx(q[5],q[12])
circuit.cx(q[6],q[13])

#"noise"/errors below:
#circuit.x(q[4])
#circuit.z(q[6])
#circuit.x(q[10])
#circuit.z(q[12])

circuit.barrier(q)

#apply the syndrome onto "gimel" 

#bit flip detection for logical qubit 1

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

#circuit.measure(q[14],c[2]) #c[2] is for "bit2" #NO!  don't measure yet :) 
#circuit.measure(q[15],c[3]) #c[3] is for "bit1"
#circuit.measure(q[16],c[4]) #c[4] is for "bit0"

circuit.barrier(q)

#syndrome causes certain (if any) gates to apply back onto aleph or bet (not to be confused with Shor's algorithm aleph and bet)
#use binary counting!  

#bit flip correction for logical qubit 1

circuit.cx(q[16],q[0])              #1
circuit.cx(q[15],q[1])              #2
circuit.ccx(q[16],q[15],q[2])       #3
circuit.cx(q[14],q[3])              #4
circuit.ccx(q[16],q[14],q[4])       #5
circuit.ccx(q[14],q[15],q[5])       #6
#circuit.c3x(q[16],q[15],q[14],q[6]) #7
circuit.append(C3XGate(), [16, 15, 14, 6])

circuit.barrier(q)

#clean/wash the qubits for reuse

circuit.reset(q[14]) 
circuit.reset(q[15])
circuit.reset(q[16])

circuit.barrier(q)

#phase flip detection for logical qubit 1

circuit.h(q[14])
circuit.h(q[15])
circuit.h(q[16])

circuit.cx(q[14], q[0])
circuit.cx(q[14], q[2])
circuit.cx(q[14], q[4])
circuit.cx(q[14], q[6])
circuit.cx(q[15], q[1])
circuit.cx(q[15], q[2])
circuit.cx(q[15], q[5])
circuit.cx(q[15], q[6])
circuit.cx(q[16], q[3])
circuit.cx(q[16], q[4])
circuit.cx(q[16], q[5])
circuit.cx(q[16], q[6])

circuit.h(q[14])
circuit.h(q[15])
circuit.h(q[16])

circuit.barrier(q)

#phase flip correction for logical qubit 1

circuit.cx(q[16],q[0])              #1
circuit.cx(q[15],q[1])              #2
circuit.ccx(q[16],q[15],q[2])       #3
circuit.cx(q[14],q[3])              #4
circuit.ccx(q[16],q[14],q[4])       #5
circuit.ccx(q[14],q[15],q[5])       #6
#circuit.c3x(q[16],q[15],q[14],q[6]) #7
#circuit.append(C3XGate(), [16, 15, 14, 6])
#circuit.h(q[6]) #this in combination with the next two lines is a dirty workaround for a "C3Z" gate since Z=HXH
circuit.append(C3XGate(), [16, 15, 14, 6])
#circuit.h(q[6])

circuit.barrier(q)

circuit.reset(q[14]) 
circuit.reset(q[15])
circuit.reset(q[16])

circuit.barrier(q)

#apply the syndrome onto "gimel" 

#bit flip detection for logical qubit 2

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

circuit.barrier(q)

#syndrome causes certain (if any) gates to apply back onto aleph or bet (not to be confused with Shor's algorithm aleph and bet)
#use binary counting!  

#bit flip correction for logical qubit 2

circuit.cx(q[16],q[7])              #1
circuit.cx(q[15],q[8])              #2
circuit.ccx(q[16],q[15],q[9])       #3
circuit.cx(q[14],q[10])              #4
circuit.ccx(q[16],q[14],q[11])       #5
circuit.ccx(q[14],q[15],q[12])       #6
#circuit.c3x(q[16],q[15],q[14],q[6]) #7
circuit.append(C3XGate(), [16, 15, 14, 13])

circuit.barrier(q)

#clean the qubits for reuse

circuit.reset(q[14]) 
circuit.reset(q[15])
circuit.reset(q[16])

circuit.barrier(q)

#phase flip detection for logical qubit 2

circuit.h(q[14])
circuit.h(q[15])
circuit.h(q[16])

circuit.cx(q[14], q[7])
circuit.cx(q[14], q[9])
circuit.cx(q[14], q[11])
circuit.cx(q[14], q[13])
circuit.cx(q[15], q[8])
circuit.cx(q[15], q[9])
circuit.cx(q[15], q[12])
circuit.cx(q[15], q[13])
circuit.cx(q[16], q[10])
circuit.cx(q[16], q[11])
circuit.cx(q[16], q[12])
circuit.cx(q[16], q[13])

circuit.h(q[14])
circuit.h(q[15])
circuit.h(q[16])

circuit.barrier(q)

#phase flip correction for logical qubit 2
#note the "binary counting" going on here

circuit.cx(q[16],q[7])                      # 1
circuit.cx(q[15],q[8])                      # 2
circuit.ccx(q[16],q[15],q[9])               # 3
circuit.cz(q[14],q[10])                     # 4
circuit.ccx(q[16],q[14],q[11])              # 5
circuit.ccx(q[14],q[15],q[12])              # 6
circuit.append(C3XGate(), [16, 15, 14, 13]) # 7

circuit.barrier(q)

#################################################################################

#decode the data back from logical qubit 1
#idea: reverse operations of the encoding step 
#numberings in comments after code align with https://cs269q.stanford.edu/projects2019/stabilizer_code_report_Y.pdf

circuit.cx(q[4],q[1]) #2, 4
circuit.cx(q[4],q[2]) #2, 5
circuit.cx(q[4],q[3]) #2, 3

circuit.cx(q[5],q[0]) #1, 6
circuit.cx(q[5],q[2]) #1, 4
circuit.cx(q[5],q[3]) #1, 3

circuit.cx(q[6],q[0]) #0, 6
circuit.cx(q[6],q[1]) #0, 4
circuit.cx(q[6],q[3]) #0, 3

circuit.cx(q[0],q[1]) #6 (psi), 4
circuit.cx(q[0],q[2]) #6 (psi), 5

circuit.h(q[4]) #2 
circuit.h(q[5]) #1
circuit.h(q[6]) #0

#decode the data back from logical qubit 2
#note that the decoding between "aleph" and "bet" can happen in parallel - similar to the encoding step

circuit.cx(q[11],q[8])
circuit.cx(q[11],q[9])
circuit.cx(q[11],q[10])

circuit.cx(q[12],q[7])
circuit.cx(q[12],q[9])
circuit.cx(q[12],q[10])

circuit.cx(q[13],q[7])
circuit.cx(q[13],q[8])
circuit.cx(q[13],q[10])

circuit.cx(q[7],q[8])
circuit.cx(q[7],q[9])

circuit.h(q[11]) 
circuit.h(q[12])
circuit.h(q[13])

#read the actual data

circuit.barrier(q)

circuit.measure(q[0],c[0])
circuit.measure(q[7],c[1])

#IBM cloud
transpiled_circuit = transpile(circuit, backend)

#generated image is too large
#transpiled_circuit.draw(output='mpl', filename='steanecode_brisbane_transpiled.png', fold=-1)
#print("Number of operations for 'Brisbane Transpiled Circuit':")
print(dict(transpiled_circuit.count_ops()))

job = backend.run(transpiled_circuit, shots=loops)
counts = job.result().get_counts()

#print('\n')
print("Counts using the built in Qiskit 'shots'")
#print("--------------------------------------")
print(counts)

finish_time = time.time() - start_time
print('Time elapsed: ' + str(finish_time) + ' seconds')
