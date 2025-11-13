import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mesh_app/design_system/theme/quantum_theme.dart';
import 'package:mesh_app/design_system/components/mesh_app.dart';
import 'package:mesh_app/services/mesh_service.dart';
import 'package:mesh_app/services/ai_adaptive_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize services
  await MeshService().initialize();
  await AIAdaptiveService().initialize();

  runApp(
    const ProviderScope(
      child: MeshApp(),
    ),
  );
}
