#include <iostream>
#include <vector>
#include <complex>
#include <cmath>
#include <random>
#include <memory>
#include <string>
#include <unordered_map>

using namespace std;
using complex_d = complex<double>;

// Quantum gate definitions
class QuantumGate {
public:
    virtual ~QuantumGate() = default;
    virtual vector<vector<complex_d>> get_matrix() const = 0;
    virtual string get_name() const = 0;
};

class PauliX : public QuantumGate {
public:
    vector<vector<complex_d>> get_matrix() const override {
        return {{0, 1}, {1, 0}};
    }
    string get_name() const override { return "Pauli-X"; }
};

class PauliY : public QuantumGate {
public:
    vector<vector<complex_d>> get_matrix() const override {
        return {{0, complex_d(0, -1)}, {complex_d(0, 1), 0}};
    }
    string get_name() const override { return "Pauli-Y"; }
};

class PauliZ : public QuantumGate {
public:
    vector<vector<complex_d>> get_matrix() const override {
        return {{1, 0}, {0, -1}};
    }
    string get_name() const override { return "Pauli-Z"; }
};

class Hadamard : public QuantumGate {
public:
    vector<vector<complex_d>> get_matrix() const override {
        double inv_sqrt2 = 1.0 / sqrt(2.0);
        return {{inv_sqrt2, inv_sqrt2}, {inv_sqrt2, -inv_sqrt2}};
    }
    string get_name() const override { return "Hadamard"; }
};

class CNOT : public QuantumGate {
public:
    vector<vector<complex_d>> get_matrix() const override {
        return {
            {1, 0, 0, 0},
            {0, 1, 0, 0},
            {0, 0, 0, 1},
            {0, 0, 1, 0}
        };
    }
    string get_name() const override { return "CNOT"; }
};

// Qubit class
class Qubit {
private:
    complex_d alpha, beta; // |psi> = alpha|0> + beta|1>

public:
    Qubit() : alpha(1.0, 0.0), beta(0.0, 0.0) {}
    Qubit(complex_d a, complex_d b) : alpha(a), beta(b) { normalize(); }

    void normalize() {
        double norm = sqrt(norm(alpha) + norm(beta));
        if (norm > 0) {
            alpha /= norm;
            beta /= norm;
        }
    }

    complex_d get_alpha() const { return alpha; }
    complex_d get_beta() const { return beta; }

    double measure() {
        random_device rd;
        mt19937 gen(rd());
        uniform_real_distribution<> dis(0.0, 1.0);

        double prob_0 = norm(alpha);
        return dis(gen) < prob_0 ? 0.0 : 1.0;
    }

    void apply_gate(const QuantumGate& gate) {
        auto matrix = gate.get_matrix();
        complex_d new_alpha = matrix[0][0] * alpha + matrix[0][1] * beta;
        complex_d new_beta = matrix[1][0] * alpha + matrix[1][1] * beta;
        alpha = new_alpha;
        beta = new_beta;
        normalize();
    }
};

// Quantum register (multi-qubit system)
class QuantumRegister {
private:
    vector<Qubit> qubits;
    int num_qubits;

public:
    QuantumRegister(int n) : num_qubits(n) {
        qubits.resize(n);
    }

    int get_num_qubits() const { return num_qubits; }

    Qubit& get_qubit(int index) {
        if (index >= 0 && index < num_qubits) {
            return qubits[index];
        }
        throw out_of_range("Qubit index out of range");
    }

    vector<double> measure_all() {
        vector<double> results;
        for (auto& qubit : qubits) {
            results.push_back(qubit.measure());
        }
        return results;
    }

    void apply_single_gate(int qubit_index, const QuantumGate& gate) {
        if (qubit_index >= 0 && qubit_index < num_qubits) {
            qubits[qubit_index].apply_gate(gate);
        }
    }

    void apply_cnot(int control_index, int target_index) {
        if (control_index >= 0 && control_index < num_qubits &&
            target_index >= 0 && target_index < num_qubits) {
            CNOT cnot;
            // Simplified CNOT implementation for single qubits
            // In a full implementation, this would need tensor products
            if (qubits[control_index].measure() == 1.0) {
                qubits[target_index].apply_gate(PauliX());
            }
        }
    }
};

// Quantum network simulator
class QuantumNetworkSimulator {
private:
    unordered_map<string, unique_ptr<QuantumRegister>> nodes;
    unordered_map<string, vector<string>> connections;

public:
    void add_node(const string& node_id, int num_qubits = 2) {
        nodes[node_id] = make_unique<QuantumRegister>(num_qubits);
    }

    void add_connection(const string& node1, const string& node2) {
        connections[node1].push_back(node2);
        connections[node2].push_back(node1);
    }

    QuantumRegister* get_node(const string& node_id) {
        auto it = nodes.find(node_id);
        return it != nodes.end() ? it->second.get() : nullptr;
    }

    vector<string> get_neighbors(const string& node_id) {
        auto it = connections.find(node_id);
        return it != connections.end() ? it->second : vector<string>();
    }

    // Simulate quantum teleportation between connected nodes
    bool teleport_qubit(const string& source_node, int source_qubit,
                       const string& target_node, int target_qubit) {
        auto source_reg = get_node(source_node);
        auto target_reg = get_node(target_node);

        if (!source_reg || !target_reg) return false;

        // Check if nodes are connected
        auto neighbors = get_neighbors(source_node);
        if (find(neighbors.begin(), neighbors.end(), target_node) == neighbors.end()) {
            return false;
        }

        // Simplified teleportation protocol
        // In reality, this would involve EPR pairs and classical communication
        try {
            auto& source_q = source_reg->get_qubit(source_qubit);
            auto& target_q = target_reg->get_qubit(target_qubit);

            // Entangle qubits (simplified)
            Hadamard h;
            source_q.apply_gate(h);

            // Measure source qubit
            double measurement = source_q.measure();

            // Apply correction to target based on measurement
            if (measurement == 1.0) {
                PauliX x;
                target_q.apply_gate(x);
            }

            return true;
        } catch (const out_of_range&) {
            return false;
        }
    }

    // Simulate quantum key distribution (BB84 protocol simplified)
    string generate_shared_key(const string& node1, const string& node2, int key_length = 128) {
        auto reg1 = get_node(node1);
        auto reg2 = get_node(node2);

        if (!reg1 || !reg2) return "";

        string key = "";
        Hadamard h;
        PauliX x;

        for (int i = 0; i < key_length; ++i) {
            // Alice prepares random bit and basis
            int bit = rand() % 2;
            int basis = rand() % 2;

            Qubit qubit;
            if (bit == 1) qubit.apply_gate(x);
            if (basis == 1) qubit.apply_gate(h);

            // Bob measures in random basis
            int bob_basis = rand() % 2;
            if (bob_basis == 1) qubit.apply_gate(h);

            double measurement = qubit.measure();

            // If bases match, keep the bit
            if (basis == bob_basis) {
                key += (measurement == 1.0 ? '1' : '0');
            }
        }

        return key.substr(0, key_length); // Ensure exact length
    }

    void print_network_state() {
        cout << "Quantum Network State:" << endl;
        cout << "Nodes: " << nodes.size() << endl;
        for (const auto& pair : nodes) {
            cout << "  " << pair.first << ": " << pair.second->get_num_qubits() << " qubits" << endl;
        }
        cout << "Connections:" << endl;
        for (const auto& pair : connections) {
            cout << "  " << pair.first << " -> ";
            for (const auto& neighbor : pair.second) {
                cout << neighbor << " ";
            }
            cout << endl;
        }
    }
};

// FFI interface for Flutter integration
extern "C" {

QuantumNetworkSimulator* create_simulator() {
    return new QuantumNetworkSimulator();
}

void destroy_simulator(QuantumNetworkSimulator* sim) {
    delete sim;
}

void add_node(QuantumNetworkSimulator* sim, const char* node_id, int num_qubits) {
    sim->add_node(string(node_id), num_qubits);
}

void add_connection(QuantumNetworkSimulator* sim, const char* node1, const char* node2) {
    sim->add_connection(string(node1), string(node2));
}

bool teleport_qubit(QuantumNetworkSimulator* sim, const char* source, int source_qubit,
                   const char* target, int target_qubit) {
    return sim->teleport_qubit(string(source), source_qubit, string(target), target_qubit);
}

const char* generate_shared_key(QuantumNetworkSimulator* sim, const char* node1,
                               const char* node2, int key_length) {
    static string last_key;
    last_key = sim->generate_shared_key(string(node1), string(node2), key_length);
    return last_key.c_str();
}

void print_network_state(QuantumNetworkSimulator* sim) {
    sim->print_network_state();
}

} // extern "C"
