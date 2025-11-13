#pragma once

#include "ai_core_handler.hpp"

#include <queue>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>

namespace ai_core {

class InferenceEngine {
public:
    InferenceEngine();
    ~InferenceEngine();

    InferenceResult RunInference(const InferenceRequest& request);

private:
    void InferenceWorker();
    InferenceResult ProcessInferenceRequest(const InferenceRequest& request);

    std::queue<InferenceRequest> request_queue_;
    std::mutex queue_mutex_;
    std::condition_variable queue_cv_;
    std::thread worker_thread_;
    std::atomic<bool> running_{true};
};

}  // namespace ai_core
