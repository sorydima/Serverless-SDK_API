import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class QuantumTypography {
  // Light theme text theme
  static TextTheme get textTheme => TextTheme(
        displayLarge: GoogleFonts.quantumSans(
          fontSize: 57,
          fontWeight: FontWeight.w400,
          height: 1.12,
          letterSpacing: -0.25,
        ),
        displayMedium: GoogleFonts.quantumSans(
          fontSize: 45,
          fontWeight: FontWeight.w400,
          height: 1.16,
          letterSpacing: 0,
        ),
        displaySmall: GoogleFonts.quantumSans(
          fontSize: 36,
          fontWeight: FontWeight.w400,
          height: 1.22,
          letterSpacing: 0,
        ),
        headlineLarge: GoogleFonts.neuralDisplay(
          fontSize: 32,
          fontWeight: FontWeight.w400,
          height: 1.25,
          letterSpacing: 0,
        ),
        headlineMedium: GoogleFonts.neuralDisplay(
          fontSize: 28,
          fontWeight: FontWeight.w400,
          height: 1.29,
          letterSpacing: 0,
        ),
        headlineSmall: GoogleFonts.neuralDisplay(
          fontSize: 24,
          fontWeight: FontWeight.w400,
          height: 1.33,
          letterSpacing: 0,
        ),
        titleLarge: GoogleFonts.quantumSans(
          fontSize: 22,
          fontWeight: FontWeight.w500,
          height: 1.27,
          letterSpacing: 0,
        ),
        titleMedium: GoogleFonts.quantumSans(
          fontSize: 16,
          fontWeight: FontWeight.w500,
          height: 1.5,
          letterSpacing: 0.15,
        ),
        titleSmall: GoogleFonts.quantumSans(
          fontSize: 14,
          fontWeight: FontWeight.w500,
          height: 1.43,
          letterSpacing: 0.1,
        ),
        bodyLarge: GoogleFonts.quantumSans(
          fontSize: 16,
          fontWeight: FontWeight.w400,
          height: 1.5,
          letterSpacing: 0.15,
        ),
        bodyMedium: GoogleFonts.quantumSans(
          fontSize: 14,
          fontWeight: FontWeight.w400,
          height: 1.43,
          letterSpacing: 0.25,
        ),
        bodySmall: GoogleFonts.quantumSans(
          fontSize: 12,
          fontWeight: FontWeight.w400,
          height: 1.33,
          letterSpacing: 0.4,
        ),
        labelLarge: GoogleFonts.quantumSans(
          fontSize: 14,
          fontWeight: FontWeight.w500,
          height: 1.43,
          letterSpacing: 0.1,
        ),
        labelMedium: GoogleFonts.quantumSans(
          fontSize: 12,
          fontWeight: FontWeight.w500,
          height: 1.33,
          letterSpacing: 0.5,
        ),
        labelSmall: GoogleFonts.quantumSans(
          fontSize: 11,
          fontWeight: FontWeight.w500,
          height: 1.45,
          letterSpacing: 0.5,
        ),
      );

  static TextTheme get primaryTextTheme => textTheme.apply(
        bodyColor: Colors.white,
        displayColor: Colors.white,
      );

  // Dark theme text theme
  static TextTheme get textThemeDark => textTheme.apply(
        bodyColor: const Color(0xFFE6E1E5),
        displayColor: const Color(0xFFE6E1E5),
      );

  static TextTheme get primaryTextThemeDark => textThemeDark;

  // Specific text styles
  static TextStyle get headlineSmall => textTheme.headlineSmall!;
  static TextStyle get headlineSmallDark => textThemeDark.headlineSmall!;

  static TextStyle get labelLarge => textTheme.labelLarge!;
  static TextStyle get labelLargeDark => textThemeDark.labelLarge!;

  static TextStyle get bodyLarge => textTheme.bodyLarge!;
  static TextStyle get bodyLargeDark => textThemeDark.bodyLarge!;

  static TextStyle get bodyMedium => textTheme.bodyMedium!;
  static TextStyle get bodyMediumDark => textThemeDark.bodyMedium!;

  // Quantum-specific text styles
  static TextStyle quantumDisplay({
    double fontSize = 24,
    FontWeight fontWeight = FontWeight.w600,
    Color color = const Color(0xFF0066CC),
  }) =>
      GoogleFonts.neuralDisplay(
        fontSize: fontSize,
        fontWeight: fontWeight,
        color: color,
        letterSpacing: -0.5,
        shadows: [
          Shadow(
            color: color.withOpacity(0.3),
            offset: const Offset(0, 2),
            blurRadius: 4,
          ),
        ],
      );

  static TextStyle neuralText({
    double fontSize = 16,
    FontWeight fontWeight = FontWeight.w400,
    Color color = const Color(0xFF1A1C1E),
  }) =>
      GoogleFonts.quantumSans(
        fontSize: fontSize,
        fontWeight: fontWeight,
        color: color,
        letterSpacing: 0.25,
      );

  static TextStyle meshIndicator({
    double fontSize = 12,
    FontWeight fontWeight = FontWeight.w600,
    Color color = const Color(0xFF4CAF50),
  }) =>
      GoogleFonts.quantumSans(
        fontSize: fontSize,
        fontWeight: fontWeight,
        color: color,
        letterSpacing: 1.0,
      ).copyWith(
        fontFeatures: [const FontFeature.tabularFigures()],
      );

  // Accessibility text styles
  static TextStyle accessibleText({
    double fontSize = 18,
    FontWeight fontWeight = FontWeight.w400,
    Color color = const Color(0xFF1A1C1E),
  }) =>
      GoogleFonts.quantumSans(
        fontSize: fontSize,
        fontWeight: fontWeight,
        color: color,
        height: 1.5,
        letterSpacing: 0.5,
      );

  static TextStyle highContrastText({
    double fontSize = 16,
    FontWeight fontWeight = FontWeight.w600,
    Color color = const Color(0xFF000000),
  }) =>
      GoogleFonts.quantumSans(
        fontSize: fontSize,
        fontWeight: fontWeight,
        color: color,
        letterSpacing: 0.25,
      );
}
