#ifndef QUANTUM_SIMULATOR_HPP
#define QUANTUM_SIMULATOR_HPP

#include <string>
#include <vector>
#include <complex>
#include <unordered_map>
#include <memory>

using namespace std;
using complex_d = complex<double>;

class QuantumGate;
class Qubit;
class QuantumRegister;
class QuantumNetworkSimulator;

// FFI declarations for Flutter
extern "C" {
    QuantumNetworkSimulator* create_simulator();
    void destroy_simulator(QuantumNetworkSimulator* sim);
    void add_node(QuantumNetworkSimulator* sim, const char* node_id, int num_qubits);
    void add_connection(QuantumNetworkSimulator* sim, const char* node1, const char* node2);
    bool teleport_qubit(QuantumNetworkSimulator* sim, const char* source, int source_qubit,
                       const char* target, int target_qubit);
    const char* generate_shared_key(QuantumNetworkSimulator* sim, const char* node1,
                                   const char* node2, int key_length);
    void print_network_state(QuantumNetworkSimulator* sim);
}

#endif // QUANTUM_SIMULATOR_HPP
