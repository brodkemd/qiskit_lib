from qiskit import *
from qiskit import IBMQ
from qiskit.providers import backend, provider
from qiskit.tools.monitor import job_monitor
from qiskit.ignis.mitigation.measurement import (complete_meas_cal, CompleteMeasFitter)

# pass in your cicuit to see what the current state vector is
def print_state_vector(quantum_circuit):
    backend = Aer.get_backend('statevector_simulator')
    job = backend.run(quantum_circuit)
    result = job.result()
    
    print(result.get_statevector(quantum_circuit, decimals=3))
    

# runs the circuit on the qasm_simulator
def simulated_execution(quantum_circuit, how_many_times_to_run_it):
    simulator = Aer.get_backend('qasm_simulator')
    result = execute(quantum_circuit, backend=simulator, shots=how_many_times_to_run_it).result()

    return result
    

def run_on_real_machine(quantum_circuit, how_many_times_to_run_it):
    # loading my account
    IBMQ.load_account()

    # telling it where to look for the quantum devices
    provider = IBMQ.get_provider('ibm-q')

    # list that holds all of the names of the devices
    devices = []

    # iteration counter
    i = 0
    # loops through all of the devices available to me
    for device in provider.backends():
        # this excludes simulators from the list of real devices, this is good lol
        if device.name().count("simulator") != 0:
            continue

        # adding the current device to the list
        devices.append(device)

        # printing the iteration of the loop to be used as an option for the user later, the device name, 
        # how many other jobs are in the queue, and the number of Qbits each device can handle
        print(f"{i} : {device.name()} has {device.status().pending_jobs} queued")

        i = i + 1

    # essentially asking the user what device they want
    option = int(input("What device? (input the integer before the \":\" in each line): "))

    # getting the device the user wanted
    print("You choose:", devices[option])
    backend = provider.get_backend(devices[option].name().strip()) # for some reason the name of the device has extra whitespaces so I strip them
    
    # running the circuit on that device
    job = execute(quantum_circuit, backend=backend, shots=how_many_times_to_run_it, optimization_level=0)

    # telling the user their job id
    print(job.job_id())

    # monitoring the status of the user's circuit
    job_monitor(job)

    # returning the result of the user's circuit execution on a real machine
    return job.result()


# migates some of the noise of a quantum cicuit on real hardware, I wish I could put comments in the function itseld
# but I dont really know how it works that well, go look at qiskit documentation
def mitigate(quantum_circuit, shots, real_result):
    cal_circuits, state_labels = complete_meas_cal(qr=quantum_circuit.qregs[0], circlabel='measerrormitigationcal')

    print("- READ THIS: The following list is where you choose to run the calibration circuits")
    cal_results = run_on_real_machine(cal_circuits, shots)

    meas_fitter = CompleteMeasFitter(cal_results, state_labels)
    
    # plots the result of the calibration
    #meas_fitter.plot_calibration()

    meas_filter = meas_fitter.filter

    # return the result of the passed in circuit but with less noise
    return meas_filter.apply(real_result)