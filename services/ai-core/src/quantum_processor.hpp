#pragma once

#include <userver/formats/json.hpp>
#include <string>

namespace ai_core {

class QuantumProcessor {
public:
    QuantumProcessor();
    ~QuantumProcessor() = default;

    userver::formats::json::Value GetStatus() const;
    bool ExecuteQuantumCircuit(const std::string& circuit_description);
    userver::formats::json::Value MeasureQubits(int num_qubits);

private:
    void InitializeQuantumSimulator();
    void SimulateQuantumNoise();

    int available_qubits_;
    double coherence_time_us_;
    double gate_fidelity_;
};

}  // namespace ai_core
