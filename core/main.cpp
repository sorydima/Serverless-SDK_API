/**
 * Main entry point for userver backend
 */

#include "userver_backend.hpp"
#include <userver/components/run.hpp>
#include <userver/logging/log.hpp>

int main(int argc, char* argv[]) {
    auto component_list = userver::components::MinimalServerComponentList()
        .Append<synapse::MeshHandler>()
        .Append<synapse::BlockchainHandler>()
        .Append<synapse::AIHandler>();

    return userver::utils::DaemonMain(argc, argv, component_list);
}
