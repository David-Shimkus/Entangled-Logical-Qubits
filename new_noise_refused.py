# File: new_noise_refused.py
# This file is where I have decided to break out the noise model logic and comments. 
# This functionality is still very experimental but unfortunately I think will become more necessary in the future.  
# The "refused" portion of the filename is a reference to the band Refused and their song New Noise.  
# 
# Revision History 
# November 14, 2023 - David Shimkus - Initial Version 
# November 26, 2023 - David Shimkus - Revisited the error generation and updated the code.  
# November 27, 2023 - David Shimkus - Injected noise example from Qiskit documentation.  

import numpy as np
from datetime import datetime
import random 

from qiskit import *
from qiskit import QuantumRegister
from qiskit import ClassicalRegister
from qiskit import QuantumCircuit
from qiskit.circuit.library import *
from qiskit_aer import AerSimulator
import qiskit_aer.noise as noise
#from qiskit_aer.noise import pauli_error
#from qiskit_aer.noise import thermal_relaxation_error # there are more options available here!
from qiskit_aer.noise import *
from qiskit import *
from qiskit import IBMQ

def get_empty_model_and_gates():

    print("Attempting to simulate EMPTY noise...")
    
    prob_1 = 0.00 # 1-qubit gate
    prob_2 = 0.00 # 2-qubit gate 

    bit_flip = pauli_error([('X', prob_1), ('I', 1 - prob_1)])

    noise_model = noise.NoiseModel()
    noise_model.add_all_qubit_quantum_error(bit_flip, ['u1', 'u2', 'u3']) # refer to the "General" unitary matrix
    basis_gates = noise_model.basis_gates

    return noise_model

def get_model_from_IBM():
    IBMQ.save_account("e37d5b53d616af7d965cdaf92e16755f74470c0e96d7966f07920940a4f3277e9d63d1891599876a5d525857cfc1b3aa73d9d3061ada98f2b2161fda489df7ef")
    IBMQ.load_account()
    provider = IBMQ.load_account()
    #service = QiskitRuntimeService()
    backend = provider.get_backend('ibm_brisbane')
    noise_model = noise.NoiseModel.from_backend(backend)
    #print(noise_model)
    return noise_model

#https://qiskit.org/ecosystem/aer/tutorials/3_building_noise_models.html
def get_model_and_gates_prebuilt():
    # T1 and T2 values for qubits 0-3
    T1s = np.random.normal(224.3e3, 10e3, 4) # normal distribution sampling, matching IBM Brisbane values
    T2s = np.random.normal(143.85e3, 10e3, 4)

    # Truncate random T2s <= T1s
    T2s = np.array([min(T2s[j], 2 * T1s[j]) for j in range(4)])

    # Instruction times (in nanoseconds)
    time_u1 = 0   # virtual gate
    time_u2 = 50  # (single X90 pulse)
    time_u3 = 100 # (two X90 pulses)
    time_cx = 300
    time_reset = 1000  # 1 microsecond
    time_measure = 1000 # 1 microsecond

    # QuantumError objects - read the Qiskit documentation for more information
    #bit_flip = pauli_error([('X', prob_1), ('I', 1 - prob_1)])
    #phase_flip = pauli_error([('Z', prob_z), ('I', 1 - prob_z)])
    errors_reset = [thermal_relaxation_error(t1, t2, time_reset)
                    for t1, t2 in zip(T1s, T2s)]
    #errors_reset = thermal_relaxation_error(T1s,)
    errors_measure = [thermal_relaxation_error(t1, t2, time_measure)
                    for t1, t2 in zip(T1s, T2s)]
    errors_u1  = [thermal_relaxation_error(t1, t2, time_u1)
                for t1, t2 in zip(T1s, T2s)]
    errors_u2  = [thermal_relaxation_error(t1, t2, time_u2)
                for t1, t2 in zip(T1s, T2s)]
    errors_u3  = [thermal_relaxation_error(t1, t2, time_u3)
                for t1, t2 in zip(T1s, T2s)]
    errors_cx = [[thermal_relaxation_error(t1a, t2a, time_cx).expand(
                thermal_relaxation_error(t1b, t2b, time_cx))
                for t1a, t2a in zip(T1s, T2s)]
                for t1b, t2b in zip(T1s, T2s)]

    # build into the noise model - set all qubits with equal probability.  
    # in actuality, different qubits may be more susceptible to error
    noise_model = noise.NoiseModel()
    noise_model.add_all_qubit_quantum_error(errors_reset, "reset")
    noise_model.add_all_qubit_quantum_error(errors_measure, "measure")
    noise_model.add_all_qubit_quantum_error(errors_u1, "u1")
    noise_model.add_all_qubit_quantum_error(errors_u2, "u2")
    noise_model.add_all_qubit_quantum_error(errors_u3, "u3")
    noise_model.add_all_qubit_quantum_error(errors_cx, "cx")

    print("Qiskit noise model: ",noise_model)

    return noise_model

#https://qiskit.org/ecosystem/aer/tutorials/3_building_noise_models.html
def get_model_and_gates():

    print("Attempting to simulate noise...")

    # TODO: adjust as needed...
    #p_reset = 0.03
    #p_meas = 0.1
    p_gate1 = 0.1

    # QuantumError objects
    #error_reset = pauli_error([('X', p_reset), ('I', 1 - p_reset)])
    #error_meas = pauli_error([('X',p_meas), ('I', 1 - p_meas)])
    error_gate1 = pauli_error([('X',p_gate1), ('I', 1 - p_gate1)])
    error_gate2 = error_gate1.tensor(error_gate1)

    # add errors to noise model
    noise_model = noise.NoiseModel()
    #noise_bit_flip.add_all_qubit_quantum_error(error_reset, "reset")
    #noise_bit_flip.add_all_qubit_quantum_error(error_meas, "measure")
    noise_model.add_all_qubit_quantum_error(error_gate1, ["u1", "u2", "u3"])
    noise_model.add_all_qubit_quantum_error(error_gate2, ["cx"])

    print("Qiskit noise model: ",noise_model)

    return noise_model

def get_model_and_gates_bad_identities():
    print("Attempting to simulate noise...")

    # TODO: adjust as needed...
    #p_reset = 0.03
    #p_meas = 0.1
    p_gate1 = 0.000001

    # QuantumError objects
    #error_reset = pauli_error([('X', p_reset), ('I', 1 - p_reset)])
    #error_meas = pauli_error([('X',p_meas), ('I', 1 - p_meas)])
    error_gate1 = pauli_error([('X',p_gate1), ('I', 1 - p_gate1)])
    #error_gate2 = error_gate1.tensor(error_gate1)

    # add errors to noise model
    noise_model = noise.NoiseModel()
    #noise_bit_flip.add_all_qubit_quantum_error(error_reset, "reset")
    #noise_bit_flip.add_all_qubit_quantum_error(error_meas, "measure")
    noise_model.add_all_qubit_quantum_error(error_gate1, ["I"])
    #noise_model.add_all_qubit_quantum_error(error_gate2, ["cx"])

    print("Qiskit noise model: ",noise_model)

    return noise_model