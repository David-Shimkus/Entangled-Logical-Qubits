# File: main.py
# Wrapper for the various Python, Qiskit, Aer, cuQuantum, IBM, and more pieces of this project.  
# This code is in support of David Shimkus' M.S. thesis defense and is provided "as-is" without support.  
# You may be able to find out more information or contact me at https://www.davidshimkus.com or https://www.siue.edu/~dashimk/.  
# Developed in partial fulfillment of M.S. in Computer Science at Southern Illinois University Edwardsville.  
#
# NOTE: for the IBM portions to work you must provide your IBM API Key in a separate file titled IBM.key (no whitespaces, headers, etc.).  
#
# Revision History 
# November 13, 2023 - David Shimkus - Initial Version.  
# November 26, 2023 - David Shimkus - Fixed bug with noise generation call.

import time
start_time = time.time()

import numpy as np
from datetime import datetime
import random 

import qiskit
from qiskit import *
from qiskit import QuantumRegister
from qiskit import ClassicalRegister
from qiskit import QuantumCircuit
from qiskit.circuit.library import *
from qiskit_aer import AerSimulator
import qiskit_aer.noise as noise
from qiskit_aer.noise import pauli_error
from qiskit_aer.noise import thermal_relaxation_error # there are more options available here!

# custom files
from new_noise_refused import *
from simple_bell_state import *
from bell_state_with_bit_phase import *
from bell_state_with_steane import *
from ibm_parameters import *
from new_noise_refused import *

print("Imports Successful")
print("Qiskit Information:")
print(qiskit.__qiskit_version__)
print("")

#TODO: check for runtime arguments

print("")
print("Welcome to my entangled logical qubits demo :)")
print("This is provided as-is without support and is intended for academic/research purposes only")
print("")
print("Please enter one of the following choices: ")
print(" 1. Apple Mac A1289 and two NVIDIA T600 GPU's - cuQuantum simulation")
print(" 2. SIUE Campus Cluster and at least one NVIDIA A200 GPU - cuQuantum simulation")
print(" 3. 'Generic' NVIDIA configuration")
print(" 4. IBM Brisbane real quantum computer (Eagle architecture)")
print(" 5. IBM simulator - 5000 qubits") 
choice1 = input("Enter your choice: ")
print("")
print("Please enter one of the following choices: ")
print(" 1. Simple Bell State with two physical qubits")
print(" 2. Bell State with bit-flip encoding (3 physical qubits per logical qubit)")
print(" 3. Bell State with phase-flip encoding (3 physical qubits per logical qubit)")
print(" 4. Bell State with DiVicenzo Encoding (5 physical qubits per logical qubit and various ancillae) - NOT IMPLEMENTED")
print(" 5. Bell State with Steane Encoding (7 physical qubits per logical qubit with 3 ancillae overall)")
print(" 6. Bell State with Shor Encoding (9 physical qubits per logical qubit)")
print(" 7. Complex Bell State with four physical qubits - NOT IMPLEMENTED")
print(" 8. Complex Bell State with four logical qubits and Steane Encoding - NOT IMPLEMENTED")
print(" 9. Complex Bell State with sixteen phsyical qubits NOT IMPLEMENTED ")
print("10. Complex Bell State with sixteen physical qubits and Steane Encoding - NOT IMPLEMENTED")
print("11. Factor a semiprime number with Shor's Algorithm - EXPERIMENTAL")
choice2 = input("Enter your choice: ")
print("")

random.seed(datetime.now().timestamp()) # alternatively random.seed(1234) for constant

shots = 1000 # TODO: seed in configuration file? 

circuit = QuantumCircuit()
counts = {}

match choice2: 
    case '1':
        print("Creating a simple bell state with two physical qubits")
        circuit = new_simple_bell_circuit()
    case '2':
        print("Creating a bell state with bit-flip encoding ONLY (6 physical qubits making up 2 logical qubits)")
        circuit = new_bit_flip_circuit()
    case '3':
        print("Creating a bell state with phase-flip encoding ONLY (6 physical qubits making up 2 logical qubits)")
        circuit = new_phase_flip_circuit()
    case '4': 
        print("NOT IMPLEMENTED YET")
    case '5':
        print("Creating a bell state with Steane QEC methods (14 physical qubits making up 2 logical qubits)")
        circuit = new_steane_circuit()

match choice1: 
    case '1' | '2' | '3':
        print("You have chosen to run a local simulation instead of an IBM cloud offering.  Do you want to simulate noise?")
        print(" 1. Yes")
        print(" 2. No")
        choice3 = input("Enter your choice: ")

        noise_model = noise.NoiseModel()

        print(choice3)

        if choice3 == '1': 
            print("")
            print("What type of noisy simulator do you want to use?")
            print(" 1. IBM Brisbane")
            print(" 2. Custom Probability for ALL gates")
            print(" 3. Custom Probability in the Noisy Channel ONLY")
            choice4 = input("Enter your choice: ")

            if choice4 == '1':
                noise_model = get_model_from_IBM()
            if choice4 == '2':
                noise_model = get_model_and_gates()
            if choice4 == '3':
                noise_model = get_model_and_gates_bad_identities()
            
            

        elif choice3 == '2':
            noise_model = get_empty_model_and_gates() # no noise added via this object

        my_simulator = AerSimulator(method='statevector',device='GPU',noise_model=noise_model)

        #multi GPU
        #TODO: tweak for specific NVIDIA configurations
        number_blocking_qubits = 22 # GPU specific parameter
        
        result = execute(circuit, my_simulator, shots=shots, 
                        blocking_enable=True, blocking_qubits=number_blocking_qubits,
                        basis_gates=noise_model.basis_gates
                ).result() 

        counts = result.get_counts()
    
    case '4':
        print("You have chosen to run this code against a cloud IBM physical quantum computer.  Please make sure your API key is seeded properly.")
        print("")
        backend = load_ibm_parameters_physical()

        transpiled_circuit = transpile(circuit, backend)

        #generated image may be too large
        try:
            transpiled_circuit.draw(output='mpl', filename='bit_flip_brisbane_transpiled.png', fold=-1)
        except:
            print("")
            print("Tried to create a diagram of the transpiled circuit but it was probably too large.  Sorry!")

        print("")
        print("Number of operations for 'Brisbane Transpiled Circuit':")
        print(dict(transpiled_circuit.count_ops()))

        print("")
        print("Please be patient, this may take a while.  You can view the status of the job in the IBM dashboard: https://quantum-computing.ibm.com/.")
        job = backend.run(transpiled_circuit, shots=shots)
        counts = job.result().get_counts()

    case '5':
        print("You have chosen to run this code against a cloud IBM simulator.  Please make sure your API key is seeded properly.")
        print("")
        backend = load_ibm_parameters_simulator() #TODO: noise simulation? 

        transpiled_circuit = transpile(circuit, backend)

        #generated image may be too large
        try:
            transpiled_circuit.draw(output='mpl', filename='bit_flip_brisbane_transpiled.png', fold=-1)
        except:
            print("")
            print("Tried to create a diagram of the transpiled circuit but it was probably too large.  Sorry!")

        print("")
        print("Number of operations for 'Brisbane Transpiled Circuit':")
        print(dict(transpiled_circuit.count_ops()))

        job = backend.run(transpiled_circuit, shots=shots)
        counts = job.result().get_counts()

print("")
print('Shots: ' + str(shots))
print("")
print("Measurements obtained (approximately 50/50 |00> and |11> states expected): ")
print(counts)
print("")
print("Gate counts: ")
print(dict(circuit.count_ops()))
finish_time = time.time() - start_time
print("")
print('Time elapsed: ' + str(finish_time) + ' seconds')
        
