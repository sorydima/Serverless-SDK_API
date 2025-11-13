import 'package:plugin_platform_interface/plugin_platform_interface.dart';

import 'quantum_simulator_method_channel.dart';

abstract class QuantumSimulatorPlatform extends PlatformInterface {
  /// Constructs a QuantumSimulatorPlatform.
  QuantumSimulatorPlatform() : super(token: _token);

  static final Object _token = Object();

  static QuantumSimulatorPlatform _instance = MethodChannelQuantumSimulator();

  /// The default instance of [QuantumSimulatorPlatform] to use.
  ///
  /// Defaults to [MethodChannelQuantumSimulator].
  static QuantumSimulatorPlatform get instance => _instance;

  /// Platform-specific implementations should set this with their own
  /// platform-specific class that extends [QuantumSimulatorPlatform] when
  /// they register themselves.
  static set instance(QuantumSimulatorPlatform instance) {
    PlatformInterface.verifyToken(instance, _token);
    _instance = instance;
  }

  Future<String?> getPlatformVersion() {
    throw UnimplementedError('platformVersion() has not been implemented.');
  }
}
