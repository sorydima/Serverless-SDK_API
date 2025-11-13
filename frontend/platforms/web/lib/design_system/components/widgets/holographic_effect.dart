import 'package:flutter/material.dart';
import 'dart:ui' as ui;
import 'package:mesh_app/design_system/theme/colors/quantum_colors.dart';

class HolographicEffect extends StatefulWidget {
  final Widget child;
  final double intensity;
  final Duration duration;

  const HolographicEffect({
    super.key,
    required this.child,
    this.intensity = 1.0,
    this.duration = const Duration(seconds: 3),
  });

  @override
  State<HolographicEffect> createState() => _HolographicEffectState();
}

class _HolographicEffectState extends State<HolographicEffect>
    with TickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: widget.duration,
      vsync: this,
    )..repeat(reverse: true);

    _animation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.sine,
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return CustomPaint(
          painter: HolographicPainter(
            progress: _animation.value,
            intensity: widget.intensity,
          ),
          child: widget.child,
        );
      },
    );
  }
}

class HolographicPainter extends CustomPainter {
  final double progress;
  final double intensity;

  HolographicPainter({
    required this.progress,
    required this.intensity,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2 * intensity
      ..shader = ui.Gradient.linear(
        Offset.zero,
        Offset(size.width, size.height),
        [
          QuantumColors.primary.withOpacity(0.3 * intensity),
          QuantumColors.tertiary.withOpacity(0.3 * intensity),
          QuantumColors.secondary.withOpacity(0.3 * intensity),
        ],
        [0.0, progress, 1.0],
      );

    // Draw holographic border
    final rect = Rect.fromLTWH(0, 0, size.width, size.height);
    final rrect = RRect.fromRectAndRadius(rect, const Radius.circular(16));

    canvas.drawRRect(rrect, paint);

    // Draw scanning line effect
    final scanPaint = Paint()
      ..style = PaintingStyle.fill
      ..color = QuantumColors.primary.withOpacity(0.1 * intensity);

    final scanY = size.height * progress;
    canvas.drawRect(
      Rect.fromLTWH(0, scanY - 2, size.width, 4),
      scanPaint,
    );
  }

  @override
  bool shouldRepaint(HolographicPainter oldDelegate) {
    return oldDelegate.progress != progress ||
           oldDelegate.intensity != intensity;
  }
}

// Fractal background effect
class FractalBackground extends StatefulWidget {
  final Widget child;
  final int iterations;

  const FractalBackground({
    super.key,
    required this.child,
    this.iterations = 4,
  });

  @override
  State<FractalBackground> createState() => _FractalBackgroundState();
}

class _FractalBackgroundState extends State<FractalBackground>
    with TickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 10),
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return CustomPaint(
          painter: FractalPainter(
            progress: _controller.value,
            iterations: widget.iterations,
          ),
          child: widget.child,
        );
      },
    );
  }
}

class FractalPainter extends CustomPainter {
  final double progress;
  final int iterations;

  FractalPainter({
    required this.progress,
    required this.iterations,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1
      ..color = QuantumColors.primary.withOpacity(0.1);

    void drawFractal(double x, double y, double angle, double length, int depth) {
      if (depth == 0) return;

      final endX = x + length * angle.cos();
      final endY = y + length * angle.sin();

      canvas.drawLine(Offset(x, y), Offset(endX, endY), paint);

      final newLength = length * 0.7;
      drawFractal(endX, endY, angle - 0.5 + progress * 0.2, newLength, depth - 1);
      drawFractal(endX, endY, angle + 0.5 + progress * 0.2, newLength, depth - 1);
    }

    // Draw multiple fractal trees
    for (int i = 0; i < 3; i++) {
      final startX = size.width * (0.2 + i * 0.3);
      drawFractal(startX, size.height, -1.57, size.height * 0.3, iterations);
    }
  }

  @override
  bool shouldRepaint(FractalPainter oldDelegate) {
    return oldDelegate.progress != progress ||
           oldDelegate.iterations != iterations;
  }
}

// Neural network visualization
class NeuralNetworkEffect extends StatefulWidget {
  final Widget child;
  final int nodes;

  const NeuralNetworkEffect({
    super.key,
    required this.child,
    this.nodes = 20,
  });

  @override
  State<NeuralNetworkEffect> createState() => _NeuralNetworkEffectState();
}

class _NeuralNetworkEffectState extends State<NeuralNetworkEffect>
    with TickerProviderStateMixin {
  late AnimationController _controller;
  late List<Offset> _nodePositions;
  late List<List<int>> _connections;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 5),
      vsync: this,
    )..repeat();

    _generateNetwork();
  }

  void _generateNetwork() {
    _nodePositions = [];
    _connections = [];

    // Generate random node positions
    for (int i = 0; i < widget.nodes; i++) {
      _nodePositions.add(Offset.zero); // Will be set in paint
    }

    // Generate connections
    for (int i = 0; i < widget.nodes; i++) {
      _connections.add([]);
      for (int j = 0; j < widget.nodes; j++) {
        if (i != j && (i - j).abs() <= 3) {
          _connections[i].add(j);
        }
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return CustomPaint(
          painter: NeuralPainter(
            progress: _controller.value,
            nodePositions: _nodePositions,
            connections: _connections,
          ),
          child: widget.child,
        );
      },
    );
  }
}

class NeuralPainter extends CustomPainter {
  final double progress;
  final List<Offset> nodePositions;
  final List<List<int>> connections;

  NeuralPainter({
    required this.progress,
    required this.nodePositions,
    required this.connections,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final nodePaint = Paint()
      ..style = PaintingStyle.fill
      ..color = QuantumColors.primary.withOpacity(0.6);

    final connectionPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1
      ..color = QuantumColors.secondary.withOpacity(0.3);

    // Update node positions in a grid-like pattern with animation
    for (int i = 0; i < nodePositions.length; i++) {
      final row = i ~/ 5;
      final col = i % 5;
      final x = size.width * (0.1 + col * 0.16) + 10 * (progress * 2 - 1);
      final y = size.height * (0.1 + row * 0.16) + 5 * (progress * 2 - 1);
      nodePositions[i] = Offset(x, y);

      canvas.drawCircle(nodePositions[i], 4, nodePaint);
    }

    // Draw connections
    for (int i = 0; i < connections.length; i++) {
      for (int j in connections[i]) {
        if (i < j) { // Avoid drawing connections twice
          canvas.drawLine(
            nodePositions[i],
            nodePositions[j],
            connectionPaint,
          );
        }
      }
    }
  }

  @override
  bool shouldRepaint(NeuralPainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}
