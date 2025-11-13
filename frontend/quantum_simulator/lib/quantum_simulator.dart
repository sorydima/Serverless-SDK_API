import 'dart:ffi';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'quantum_simulator_platform_interface.dart';

class QuantumSimulator {
  static const String _libName = 'quantum_simulator';

  static DynamicLibrary _openDynamicLibrary() {
    if (Platform.isAndroid) {
      return DynamicLibrary.open('lib$_libName.so');
    } else if (Platform.isIOS) {
      return DynamicLibrary.process();
    } else if (Platform.isLinux) {
      return DynamicLibrary.open('lib$_libName.so');
    } else if (Platform.isMacOS) {
      return DynamicLibrary.open('lib$_libName.dylib');
    } else if (Platform.isWindows) {
      return DynamicLibrary.open('$_libName.dll');
    } else {
      throw UnsupportedError('Unsupported platform');
    }
  }

  static final DynamicLibrary _nativeLib = _openDynamicLibrary();

  // FFI function signatures
  static final Pointer Function() _createSimulator = _nativeLib
      .lookup<NativeFunction<Pointer Function()>>('create_simulator')
      .asFunction();

  static final void Function(Pointer) _destroySimulator = _nativeLib
      .lookup<NativeFunction<Void Function(Pointer)>>('destroy_simulator')
      .asFunction();

  static final void Function(Pointer, Pointer<Utf8>, Int32) _addNode = _nativeLib
      .lookup<NativeFunction<Void Function(Pointer, Pointer<Utf8>, Int32)>>('add_node')
      .asFunction();

  static final void Function(Pointer, Pointer<Utf8>, Pointer<Utf8>) _addConnection = _nativeLib
      .lookup<NativeFunction<Void Function(Pointer, Pointer<Utf8>, Pointer<Utf8>)>>('add_connection')
      .asFunction();

  static final int Function(Pointer, Pointer<Utf8>, Int32, Pointer<Utf8>, Int32) _teleportQubit = _nativeLib
      .lookup<NativeFunction<Int8 Function(Pointer, Pointer<Utf8>, Int32, Pointer<Utf8>, Int32)>>('teleport_qubit')
      .asFunction();

  static final Pointer<Utf8> Function(Pointer, Pointer<Utf8>, Pointer<Utf8>, Int32) _generateSharedKey = _nativeLib
      .lookup<NativeFunction<Pointer<Utf8> Function(Pointer, Pointer<Utf8>, Pointer<Utf8>, Int32)>>('generate_shared_key')
      .asFunction();

  static final void Function(Pointer) _printNetworkState = _nativeLib
      .lookup<NativeFunction<Void Function(Pointer)>>('print_network_state')
      .asFunction();

  Pointer _simulator;

  QuantumSimulator() : _simulator = _createSimulator();

  void dispose() {
    _destroySimulator(_simulator);
  }

  void addNode(String nodeId, {int numQubits = 2}) {
    final nodeIdPtr = nodeId.toNativeUtf8();
    _addNode(_simulator, nodeIdPtr, numQubits);
    calloc.free(nodeIdPtr);
  }

  void addConnection(String node1, String node2) {
    final node1Ptr = node1.toNativeUtf8();
    final node2Ptr = node2.toNativeUtf8();
    _addConnection(_simulator, node1Ptr, node2Ptr);
    calloc.free(node1Ptr);
    calloc.free(node2Ptr);
  }

  bool teleportQubit(String sourceNode, int sourceQubit, String targetNode, int targetQubit) {
    final sourcePtr = sourceNode.toNativeUtf8();
    final targetPtr = targetNode.toNativeUtf8();
    final result = _teleportQubit(_simulator, sourcePtr, sourceQubit, targetPtr, targetQubit) != 0;
    calloc.free(sourcePtr);
    calloc.free(targetPtr);
    return result;
  }

  String generateSharedKey(String node1, String node2, {int keyLength = 128}) {
    final node1Ptr = node1.toNativeUtf8();
    final node2Ptr = node2.toNativeUtf8();
    final keyPtr = _generateSharedKey(_simulator, node1Ptr, node2Ptr, keyLength);
    final key = keyPtr.toDartString();
    calloc.free(node1Ptr);
    calloc.free(node2Ptr);
    return key;
  }

  void printNetworkState() {
    _printNetworkState(_simulator);
  }
}

class QuantumSimulatorFlutter {
  Future<String?> getPlatformVersion() {
    return QuantumSimulatorPlatform.instance.getPlatformVersion();
  }
}
