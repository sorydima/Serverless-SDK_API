import 'package:flutter/material.dart';
import 'package:mesh_app/design_system/theme/quantum_theme.dart';
import 'package:mesh_app/design_system/components/screens/home_screen.dart';
import 'package:mesh_app/design_system/components/widgets/network_indicator.dart';
import 'package:mesh_app/services/ai_adaptive_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class MeshApp extends ConsumerStatefulWidget {
  const MeshApp({super.key});

  @override
  ConsumerState<MeshApp> createState() => _MeshAppState();
}

class _MeshAppState extends ConsumerState<MeshApp> with WidgetsBindingObserver {
  ThemeMode _themeMode = ThemeMode.system;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangePlatformBrightness() {
    super.didChangePlatformBrightness();
    // Adaptive theme based on system brightness
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final aiService = ref.watch(aiAdaptiveServiceProvider);

    return MaterialApp(
      title: 'Mesh App',
      debugShowCheckedModeBanner: false,

      // Adaptive theme based on AI preferences and system settings
      theme: aiService.maybeWhen(
        data: (aiState) => aiState.themeMode == 'quantum'
            ? QuantumTheme.quantumTheme
            : QuantumTheme.lightTheme,
        orElse: () => QuantumTheme.lightTheme,
      ),

      darkTheme: aiService.maybeWhen(
        data: (aiState) => aiState.themeMode == 'quantum'
            ? QuantumTheme.quantumTheme
            : QuantumTheme.darkTheme,
        orElse: () => QuantumTheme.darkTheme,
      ),

      themeMode: _themeMode,

      home: const Stack(
        children: [
          HomeScreen(),
          // Network indicator overlay
          Positioned(
            top: 50,
            right: 16,
            child: NetworkIndicator(),
          ),
        ],
      ),

      // Custom scroll behavior for web
      scrollBehavior: const MaterialScrollBehavior().copyWith(
        scrollbars: true,
      ),
    );
  }
}
