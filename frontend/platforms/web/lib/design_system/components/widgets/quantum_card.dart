import 'package:flutter/material.dart';
import 'package:mesh_app/design_system/theme/colors/quantum_colors.dart';
import 'package:mesh_app/design_system/theme/shapes/quantum_shapes.dart';

class QuantumCard extends StatefulWidget {
  final Widget child;
  final VoidCallback? onTap;
  final EdgeInsetsGeometry? padding;
  final double? elevation;
  final Color? backgroundColor;
  final BorderRadius? borderRadius;
  final List<BoxShadow>? boxShadow;
  final bool enableHover;
  final bool enableQuantumEffect;

  const QuantumCard({
    super.key,
    required this.child,
    this.onTap,
    this.padding,
    this.elevation,
    this.backgroundColor,
    this.borderRadius,
    this.boxShadow,
    this.enableHover = true,
    this.enableQuantumEffect = false,
  });

  @override
  State<QuantumCard> createState() => _QuantumCardState();
}

class _QuantumCardState extends State<QuantumCard>
    with TickerProviderStateMixin {
  late AnimationController _hoverController;
  late Animation<double> _hoverAnimation;
  late AnimationController _quantumController;
  late Animation<double> _quantumAnimation;

  bool _isHovered = false;

  @override
  void initState() {
    super.initState();

    _hoverController = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );

    _hoverAnimation = Tween<double>(
      begin: 1.0,
      end: 1.02,
    ).animate(CurvedAnimation(
      parent: _hoverController,
      curve: Curves.easeOut,
    ));

    if (widget.enableQuantumEffect) {
      _quantumController = AnimationController(
        duration: const Duration(seconds: 3),
        vsync: this,
      )..repeat(reverse: true);

      _quantumAnimation = Tween<double>(
        begin: 0.0,
        end: 1.0,
      ).animate(_quantumController);
    }
  }

  @override
  void dispose() {
    _hoverController.dispose();
    if (widget.enableQuantumEffect) {
      _quantumController.dispose();
    }
    super.dispose();
  }

  void _onHover(bool isHovered) {
    setState(() {
      _isHovered = isHovered;
    });
    if (isHovered) {
      _hoverController.forward();
    } else {
      _hoverController.reverse();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return MouseRegion(
      onEnter: widget.enableHover ? (_) => _onHover(true) : null,
      onExit: widget.enableHover ? (_) => _onHover(false) : null,
      child: AnimatedBuilder(
        animation: Listenable.merge([
          _hoverAnimation,
          if (widget.enableQuantumEffect) _quantumAnimation,
        ]),
        builder: (context, child) {
          return Transform.scale(
            scale: _hoverAnimation.value,
            child: GestureDetector(
              onTap: widget.onTap,
              child: Container(
                padding: widget.padding ?? const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: widget.backgroundColor ??
                      (widget.enableQuantumEffect
                          ? QuantumColors.quantumField
                          : theme.cardColor),
                  borderRadius: widget.borderRadius ??
                      const BorderRadius.all(Radius.circular(16)),
                  border: widget.enableQuantumEffect
                      ? Border.all(
                          color: Color.lerp(
                            QuantumColors.primary,
                            QuantumColors.tertiary,
                            _quantumAnimation.value,
                          )!,
                          width: 2,
                        )
                      : null,
                  boxShadow: widget.boxShadow ??
                      [
                        BoxShadow(
                          color: (widget.enableQuantumEffect
                                  ? QuantumColors.primary
                                  : Colors.black)
                              .withOpacity(_isHovered ? 0.2 : 0.1),
                          blurRadius: _isHovered ? 16 : 8,
                          offset: Offset(0, _isHovered ? 8 : 4),
                        ),
                      ],
                  gradient: widget.enableQuantumEffect
                      ? LinearGradient(
                          colors: [
                            QuantumColors.quantumField,
                            Color.lerp(
                              QuantumColors.quantumField,
                              QuantumColors.neuralNetwork,
                              _quantumAnimation.value,
                            )!,
                          ],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        )
                      : null,
                ),
                child: widget.child,
              ),
            ),
          );
        },
      ),
    );
  }
}

// Specialized quantum card variants
class NeuralCard extends QuantumCard {
  const NeuralCard({
    super.key,
    required super.child,
    super.onTap,
    super.padding,
    super.enableHover = true,
  }) : super(
          backgroundColor: QuantumColors.neuralNetwork,
          enableQuantumEffect: false,
        );
}

class MeshCard extends QuantumCard {
  const MeshCard({
    super.key,
    required super.child,
    super.onTap,
    super.padding,
    super.enableHover = true,
  }) : super(
          backgroundColor: QuantumColors.fractalMesh,
          enableQuantumEffect: false,
        );
}

class HolographicCard extends QuantumCard {
  const HolographicCard({
    super.key,
    required super.child,
    super.onTap,
    super.padding,
    super.enableHover = true,
  }) : super(
          backgroundColor: QuantumColors.holographic,
          enableQuantumEffect: true,
        );
}
