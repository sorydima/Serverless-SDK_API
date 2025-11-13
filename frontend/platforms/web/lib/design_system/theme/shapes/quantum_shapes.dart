import 'package:flutter/material.dart';

class QuantumShapes {
  // Basic shapes
  static const RoundedRectangleBorder cardShape = RoundedRectangleBorder(
    borderRadius: BorderRadius.all(Radius.circular(16)),
  );

  static const RoundedRectangleBorder buttonShape = RoundedRectangleBorder(
    borderRadius: BorderRadius.all(Radius.circular(12)),
  );

  static const RoundedRectangleBorder dialogShape = RoundedRectangleBorder(
    borderRadius: BorderRadius.all(Radius.circular(28)),
  );

  static const RoundedRectangleBorder chipShape = RoundedRectangleBorder(
    borderRadius: BorderRadius.all(Radius.circular(8)),
  );

  // Neural network inspired shapes
  static ShapeBorder neuralNodeShape = const CircleBorder();

  static ShapeBorder neuralConnectionShape = const RoundedRectangleBorder(
    borderRadius: BorderRadius.all(Radius.circular(4)),
  );

  // Quantum field shapes
  static ShapeBorder quantumFieldShape = RoundedRectangleBorder(
    borderRadius: BorderRadius.all(Radius.circular(24)),
    side: const BorderSide(
      color: Color(0xFF0066CC),
      width: 2,
      style: BorderStyle.solid,
    ),
  );

  static ShapeBorder fractalShape = RoundedRectangleBorder(
    borderRadius: BorderRadius.all(Radius.circular(20)),
    side: const BorderSide(
      color: Color(0xFF9C27B0),
      width: 1.5,
      style: BorderStyle.solid,
    ),
  );

  // Mesh network shapes
  static ShapeBorder meshNodeShape = const CircleBorder(
    side: BorderSide(
      color: Color(0xFF4CAF50),
      width: 3,
    ),
  );

  static ShapeBorder meshConnectionShape = RoundedRectangleBorder(
    borderRadius: BorderRadius.all(Radius.circular(2)),
    side: const BorderSide(
      color: Color(0xFFFF9800),
      width: 2,
    ),
  );

  // Holographic shapes
  static ShapeBorder holographicShape = RoundedRectangleBorder(
    borderRadius: BorderRadius.all(Radius.circular(16)),
    side: const BorderSide(
      color: Color(0xFFFCE4EC),
      width: 1,
    ),
  );

  // Adaptive shapes based on context
  static ShapeBorder getAdaptiveShape(BuildContext context, {String? type}) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    switch (type) {
      case 'quantum':
        return RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(24)),
          side: BorderSide(
            color: isDark ? const Color(0xFF2196F3) : const Color(0xFF0066CC),
            width: 2,
          ),
        );
      case 'neural':
        return RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(12)),
          side: BorderSide(
            color: isDark ? const Color(0xFF9C27B0) : const Color(0xFF705575),
            width: 1.5,
          ),
        );
      case 'mesh':
        return RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(8)),
          side: BorderSide(
            color: isDark ? const Color(0xFF4CAF50) : const Color(0xFF2E7D32),
            width: 2,
          ),
        );
      default:
        return cardShape;
    }
  }

  // Custom path shapes for advanced UI
  static Path createNeuralPath(Size size) {
    final path = Path();
    final width = size.width;
    final height = size.height;

    // Create a neural network-like path
    path.moveTo(0, height / 2);
    path.quadraticBezierTo(width / 4, 0, width / 2, height / 2);
    path.quadraticBezierTo(3 * width / 4, height, width, height / 2);

    return path;
  }

  static Path createQuantumFieldPath(Size size) {
    final path = Path();
    final width = size.width;
    final height = size.height;

    // Create a quantum field-like wavy path
    path.moveTo(0, height / 2);
    for (double i = 0; i <= width; i += 20) {
      final y = height / 2 + 10 * (i / width - 0.5).abs() * (i % 40 == 0 ? 1 : -1);
      path.lineTo(i, y);
    }

    return path;
  }

  static Path createFractalPath(Size size, {int iterations = 3}) {
    final path = Path();
    final width = size.width;
    final height = size.height;

    // Simple fractal tree pattern
    void drawFractal(double x, double y, double angle, double length, int depth) {
      if (depth == 0) return;

      final endX = x + length * angle.cos();
      final endY = y + length * angle.sin();

      path.moveTo(x, y);
      path.lineTo(endX, endY);

      drawFractal(endX, endY, angle - 0.5, length * 0.7, depth - 1);
      drawFractal(endX, endY, angle + 0.5, length * 0.7, depth - 1);
    }

    drawFractal(width / 2, height, -1.57, height / 3, iterations);
    return path;
  }
}

// Extension for double to provide trigonometric functions
extension Trigonometry on double {
  double get cos => cos();
  double get sin => sin();
}
