import 'package:flutter/material.dart';
import 'package:mesh_app/design_system/theme/colors/quantum_colors.dart';
import 'package:mesh_app/design_system/theme/typography/quantum_typography.dart';
import 'package:mesh_app/design_system/theme/shapes/quantum_shapes.dart';

class QuantumTheme {
  static ThemeData get lightTheme => ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        colorScheme: ColorScheme.fromSeed(
          seedColor: QuantumColors.primary,
          brightness: Brightness.light,
        ),

        // Custom colors
        primaryColor: QuantumColors.primary,
        scaffoldBackgroundColor: QuantumColors.background,
        cardColor: QuantumColors.surface,

        // Typography
        textTheme: QuantumTypography.textTheme,
        primaryTextTheme: QuantumTypography.primaryTextTheme,

        // Component themes
        appBarTheme: AppBarTheme(
          backgroundColor: QuantumColors.surface,
          foregroundColor: QuantumColors.onSurface,
          elevation: 0,
          centerTitle: true,
          titleTextStyle: QuantumTypography.headlineSmall,
        ),

        cardTheme: CardTheme(
          color: QuantumColors.surface,
          elevation: 2,
          shape: QuantumShapes.cardShape,
          margin: const EdgeInsets.all(8),
        ),

        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: QuantumColors.primary,
            foregroundColor: QuantumColors.onPrimary,
            shape: QuantumShapes.buttonShape,
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            textStyle: QuantumTypography.labelLarge,
          ),
        ),

        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: QuantumColors.primary,
            side: BorderSide(color: QuantumColors.primary, width: 2),
            shape: QuantumShapes.buttonShape,
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            textStyle: QuantumTypography.labelLarge,
          ),
        ),

        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: QuantumColors.surfaceVariant,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: QuantumColors.outline),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: QuantumColors.outline),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: QuantumColors.primary, width: 2),
          ),
          labelStyle: QuantumTypography.bodyLarge,
          hintStyle: QuantumTypography.bodyMedium.copyWith(
            color: QuantumColors.onSurfaceVariant,
          ),
        ),

        // Custom extensions
        extensions: <ThemeExtension<dynamic>>[
          QuantumColors.light(),
        ],
      );

  static ThemeData get darkTheme => ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: QuantumColors.primary,
          brightness: Brightness.dark,
        ),

        // Custom colors
        primaryColor: QuantumColors.primary,
        scaffoldBackgroundColor: QuantumColors.backgroundDark,
        cardColor: QuantumColors.surfaceDark,

        // Typography
        textTheme: QuantumTypography.textThemeDark,
        primaryTextTheme: QuantumTypography.primaryTextThemeDark,

        // Component themes
        appBarTheme: AppBarTheme(
          backgroundColor: QuantumColors.surfaceDark,
          foregroundColor: QuantumColors.onSurfaceDark,
          elevation: 0,
          centerTitle: true,
          titleTextStyle: QuantumTypography.headlineSmallDark,
        ),

        cardTheme: CardTheme(
          color: QuantumColors.surfaceDark,
          elevation: 2,
          shape: QuantumShapes.cardShape,
          margin: const EdgeInsets.all(8),
        ),

        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: QuantumColors.primary,
            foregroundColor: QuantumColors.onPrimary,
            shape: QuantumShapes.buttonShape,
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            textStyle: QuantumTypography.labelLargeDark,
          ),
        ),

        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: QuantumColors.primary,
            side: BorderSide(color: QuantumColors.primary, width: 2),
            shape: QuantumShapes.buttonShape,
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            textStyle: QuantumTypography.labelLargeDark,
          ),
        ),

        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: QuantumColors.surfaceVariantDark,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: QuantumColors.outlineDark),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: QuantumColors.outlineDark),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: QuantumColors.primary, width: 2),
          ),
          labelStyle: QuantumTypography.bodyLargeDark,
          hintStyle: QuantumTypography.bodyMediumDark.copyWith(
            color: QuantumColors.onSurfaceVariantDark,
          ),
        ),

        // Custom extensions
        extensions: <ThemeExtension<dynamic>>[
          QuantumColors.dark(),
        ],
      );

  // Quantum-specific themes
  static ThemeData get quantumTheme => lightTheme.copyWith(
        // Add quantum field effects
        scaffoldBackgroundColor: QuantumColors.quantumField,
        cardColor: QuantumColors.neuralNetwork,
      );

  static ThemeData get adaptiveTheme(BuildContext context) {
    // AI-driven theme adaptation based on user preferences and context
    final brightness = MediaQuery.of(context).platformBrightness;
    return brightness == Brightness.dark ? darkTheme : lightTheme;
  }
}
