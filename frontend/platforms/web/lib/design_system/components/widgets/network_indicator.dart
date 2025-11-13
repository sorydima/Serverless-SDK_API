import 'package:flutter/material.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:mesh_app/design_system/theme/colors/quantum_colors.dart';
import 'package:mesh_app/design_system/theme/typography/quantum_typography.dart';
import 'package:mesh_app/services/mesh_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class NetworkIndicator extends ConsumerStatefulWidget {
  const NetworkIndicator({super.key});

  @override
  ConsumerState<NetworkIndicator> createState() => _NetworkIndicatorState();
}

class _NetworkIndicatorState extends ConsumerState<NetworkIndicator>
    with TickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  ConnectivityResult _connectivityResult = ConnectivityResult.none;
  MeshStatus _meshStatus = MeshStatus.disconnected;

  @override
  void initState() {
    super.initState();

    // Pulse animation for connection status
    _pulseController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(
      begin: 0.8,
      end: 1.2,
    ).animate(CurvedAnimation(
      parent: _pulseController,
      curve: Curves.easeInOut,
    ));

    // Initialize connectivity monitoring
    _initConnectivity();
    _initMeshStatus();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _initConnectivity() async {
    final result = await Connectivity().checkConnectivity();
    setState(() {
      _connectivityResult = result;
    });

    // Listen for connectivity changes
    Connectivity().onConnectivityChanged.listen((result) {
      setState(() {
        _connectivityResult = result;
      });
    });
  }

  void _initMeshStatus() {
    final meshService = ref.read(meshServiceProvider);
    meshService.maybeWhen(
      data: (service) {
        // Listen to mesh status changes
        service.statusStream.listen((status) {
          setState(() {
            _meshStatus = status;
          });
        });
      },
      orElse: () {},
    );
  }

  @override
  Widget build(BuildContext context) {
    final isOnline = _connectivityResult != ConnectivityResult.none;
    final meshConnected = _meshStatus == MeshStatus.connected;

    return AnimatedBuilder(
      animation: _pulseAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: meshConnected ? _pulseAnimation.value : 1.0,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: _getBackgroundColor(),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: _getBorderColor(),
                width: 2,
              ),
              boxShadow: [
                BoxShadow(
                  color: _getShadowColor(),
                  blurRadius: 8,
                  spreadRadius: 1,
                ),
              ],
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  _getStatusIcon(),
                  color: _getIconColor(),
                  size: 16,
                ),
                const SizedBox(width: 6),
                Text(
                  _getStatusText(),
                  style: QuantumTypography.meshIndicator(
                    color: _getTextColor(),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Color _getBackgroundColor() {
    if (!isOnline) return QuantumColors.meshOffline.withOpacity(0.9);
    if (meshConnected) return QuantumColors.meshOnline.withOpacity(0.9);
    return QuantumColors.meshConnecting.withOpacity(0.9);
  }

  Color _getBorderColor() {
    if (!isOnline) return QuantumColors.meshOffline;
    if (meshConnected) return QuantumColors.meshOnline;
    return QuantumColors.meshConnecting;
  }

  Color _getShadowColor() {
    if (!isOnline) return QuantumColors.meshOffline.withOpacity(0.3);
    if (meshConnected) return QuantumColors.meshOnline.withOpacity(0.3);
    return QuantumColors.meshConnecting.withOpacity(0.3);
  }

  IconData _getStatusIcon() {
    if (!isOnline) return Icons.wifi_off;
    if (meshConnected) return Icons.wifi;
    return Icons.wifi_find;
  }

  Color _getIconColor() {
    if (!isOnline) return Colors.white;
    if (meshConnected) return Colors.white;
    return Colors.white;
  }

  String _getStatusText() {
    if (!isOnline) return 'OFFLINE';
    if (meshConnected) return 'MESH';
    return 'CONNECTING';
  }

  Color _getTextColor() {
    return Colors.white;
  }
}
