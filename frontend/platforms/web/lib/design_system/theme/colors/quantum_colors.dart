import 'package:flutter/material.dart';

class QuantumColors {
  // Primary colors
  static const Color primary = Color(0xFF0066CC);
  static const Color onPrimary = Color(0xFFFFFFFF);
  static const Color primaryContainer = Color(0xFFD1E4FF);
  static const Color onPrimaryContainer = Color(0xFF001D36);

  // Secondary colors
  static const Color secondary = Color(0xFF565F71);
  static const Color onSecondary = Color(0xFFFFFFFF);
  static const Color secondaryContainer = Color(0xFFDAE2F9);
  static const Color onSecondaryContainer = Color(0xFF131C2B);

  // Tertiary colors
  static const Color tertiary = Color(0xFF705575);
  static const Color onTertiary = Color(0xFFFFFFFF);
  static const Color tertiaryContainer = Color(0xFFFBD7FC);
  static const Color onTertiaryContainer = Color(0xFF28132E);

  // Error colors
  static const Color error = Color(0xFFBA1A1A);
  static const Color onError = Color(0xFFFFFFFF);
  static const Color errorContainer = Color(0xFFFFDAD6);
  static const Color onErrorContainer = Color(0xFF410002);

  // Background colors
  static const Color background = Color(0xFFFEFBFF);
  static const Color onBackground = Color(0xFF1A1C1E);
  static const Color surface = Color(0xFFFEFBFF);
  static const Color onSurface = Color(0xFF1A1C1E);
  static const Color surfaceVariant = Color(0xFFE7E0EC);
  static const Color onSurfaceVariant = Color(0xFF49454F);

  // Dark theme colors
  static const Color backgroundDark = Color(0xFF0F1419);
  static const Color onBackgroundDark = Color(0xFFE6E1E5);
  static const Color surfaceDark = Color(0xFF0F1419);
  static const Color onSurfaceDark = Color(0xFFE6E1E5);
  static const Color surfaceVariantDark = Color(0xFF49454F);
  static const Color onSurfaceVariantDark = Color(0xFFCAC4D0);

  // Outline colors
  static const Color outline = Color(0xFF79747E);
  static const Color outlineDark = Color(0xFF938F99);

  // Quantum-specific colors
  static const Color quantumField = Color(0xFFE8F4FD);
  static const Color neuralNetwork = Color(0xFFF3E5F5);
  static const Color fractalMesh = Color(0xFFE3F2FD);
  static const Color holographic = Color(0xFFFCE4EC);

  // Mesh networking colors
  static const Color meshOnline = Color(0xFF4CAF50);
  static const Color meshOffline = Color(0xFFF44336);
  static const Color meshConnecting = Color(0xFFFF9800);
  static const Color meshWeak = Color(0xFFFFC107);

  // AI adaptive colors
  static const Color aiFocus = Color(0xFF2196F3);
  static const Color aiRelax = Color(0xFF4CAF50);
  static const Color aiEnergy = Color(0xFFFF5722);
  static const Color aiCalm = Color(0xFF9C27B0);

  // Accessibility colors
  static const Color highContrast = Color(0xFF000000);
  static const Color lowVision = Color(0xFFFFEB3B);

  // Gradients
  static const LinearGradient quantumGradient = LinearGradient(
    colors: [primary, tertiary],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient neuralGradient = LinearGradient(
    colors: [secondary, primary],
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
  );

  static const LinearGradient meshGradient = LinearGradient(
    colors: [meshOnline, meshWeak],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  // Extension for theme access
  static QuantumColors light() => const QuantumColors._light();
  static QuantumColors dark() => const QuantumColors._dark();

  const QuantumColors._light();
  const QuantumColors._dark();
}

extension QuantumColorsExtension on BuildContext {
  QuantumColors get quantumColors {
    final isDark = Theme.of(this).brightness == Brightness.dark;
    return isDark ? QuantumColors.dark() : QuantumColors.light();
  }
}
