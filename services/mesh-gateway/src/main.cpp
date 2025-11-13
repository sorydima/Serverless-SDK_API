#include <userver/components/minimal_server_component_list.hpp>
#include <userver/utils/daemon_run.hpp>

#include "mesh_gateway_handler.hpp"

int main(int argc, char* argv[]) {
    auto component_list = userver::components::MinimalServerComponentList()
        .Append<MeshGatewayHandler>();

    return userver::utils::DaemonMain(argc, argv, component_list);
}
