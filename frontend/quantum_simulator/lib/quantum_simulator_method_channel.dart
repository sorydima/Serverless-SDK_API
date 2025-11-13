import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import 'quantum_simulator_platform_interface.dart';

/// An implementation of [QuantumSimulatorPlatform] that uses method channels.
class MethodChannelQuantumSimulator extends QuantumSimulatorPlatform {
  /// The method channel used to interact with the native platform.
  @visibleForTesting
  final methodChannel = const MethodChannel('quantum_simulator');

  @override
  Future<String?> getPlatformVersion() async {
    final version = await methodChannel.invokeMethod<String>('getPlatformVersion');
    return version;
  }
}
