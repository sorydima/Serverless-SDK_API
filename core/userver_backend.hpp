/**
 * Userver Backend Header for SynapseSDK
 *
 * Header file for userver-based backend services.
 */

#pragma once

#include <userver/components/minimal_server_component_list.hpp>
#include <userver/server/handlers/http_handler_base.hpp>

namespace synapse {

// Forward declarations
class MeshHandler;
class BlockchainHandler;
class AIHandler;

// Component list for userver
using ComponentList = userver::components::MinimalServerComponentList;

}  // namespace synapse
