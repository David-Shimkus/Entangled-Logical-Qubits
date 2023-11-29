# File: ibm_parameters.py
#
# Revision History:
# November 14, 2023 - David Shimkus - Initial Version 

#TODO: dynamically load some of the information in a file, etc.
#TODO: check to see if the account is already "loaded" before loading (for cleaner output)

from qiskit import *
from qiskit import IBMQ

def load_ibm_parameters_physical():
    IBMQ.save_account("e37d5b53d616af7d965cdaf92e16755f74470c0e96d7966f07920940a4f3277e9d63d1891599876a5d525857cfc1b3aa73d9d3061ada98f2b2161fda489df7ef")
    IBMQ.load_account()
    provider = IBMQ.load_account()

    backend = provider.get_backend('ibm_brisbane')
    return backend

def load_ibm_parameters_simulator():
    IBMQ.save_account("e37d5b53d616af7d965cdaf92e16755f74470c0e96d7966f07920940a4f3277e9d63d1891599876a5d525857cfc1b3aa73d9d3061ada98f2b2161fda489df7ef")
    IBMQ.load_account()
    provider = IBMQ.load_account()

    backend = provider.get_backend('ibm_stabilizer') # 5000 qubits??
    return backend