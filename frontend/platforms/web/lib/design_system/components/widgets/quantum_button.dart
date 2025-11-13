import 'package:flutter/material.dart';
import 'package:mesh_app/design_system/theme/colors/quantum_colors.dart';
import 'package:mesh_app/design_system/theme/shapes/quantum_shapes.dart';
import 'package:mesh_app/design_system/theme/typography/quantum_typography.dart';

enum QuantumButtonType {
  primary,
  secondary,
  quantum,
  neural,
  mesh,
}

class QuantumButton extends StatefulWidget {
  final String text;
  final VoidCallback? onPressed;
  final QuantumButtonType type;
  final bool isLoading;
  final IconData? icon;
  final double? width;
  final double? height;

  const QuantumButton({
    super.key,
    required this.text,
    this.onPressed,
    this.type = QuantumButtonType.primary,
    this.isLoading = false,
    this.icon,
    this.width,
    this.height,
  });

  @override
  State<QuantumButton> createState() => _QuantumButtonState();
}

class _QuantumButtonState extends State<QuantumButton>
    with TickerProviderStateMixin {
  late AnimationController _scaleController;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _scaleController = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 0.95,
    ).animate(CurvedAnimation(
      parent: _scaleController,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _scaleController.dispose();
    super.dispose();
  }

  void _onTapDown(TapDownDetails details) {
    _scaleController.forward();
  }

  void _onTapUp(TapUpDetails details) {
    _scaleController.reverse();
  }

  void _onTapCancel() {
    _scaleController.reverse();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _scaleAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _scaleAnimation.value,
          child: GestureDetector(
            onTapDown: _onTapDown,
            onTapUp: _onTapUp,
            onTapCancel: _onTapCancel,
            onTap: widget.isLoading ? null : widget.onPressed,
            child: Container(
              width: widget.width,
              height: widget.height ?? 48,
              decoration: BoxDecoration(
                gradient: _getGradient(),
                borderRadius: BorderRadius.circular(12),
                border: _getBorder(),
                boxShadow: _getShadow(),
              ),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: widget.isLoading ? null : widget.onPressed,
                  splashColor: _getSplashColor(),
                  highlightColor: _getHighlightColor(),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (widget.icon != null && !widget.isLoading) ...[
                          Icon(
                            widget.icon,
                            color: _getTextColor(),
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                        ],
                        if (widget.isLoading) ...[
                          SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation<Color>(
                                _getTextColor(),
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                        ],
                        Text(
                          widget.text,
                          style: QuantumTypography.labelLarge.copyWith(
                            color: _getTextColor(),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  LinearGradient _getGradient() {
    switch (widget.type) {
      case QuantumButtonType.primary:
        return const LinearGradient(
          colors: [Color(0xFF0066CC), Color(0xFF0052A3)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        );
      case QuantumButtonType.secondary:
        return const LinearGradient(
          colors: [Color(0xFF565F71), Color(0xFF3E4759)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        );
      case QuantumButtonType.quantum:
        return const LinearGradient(
          colors: [Color(0xFF0066CC), Color(0xFF9C27B0)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        );
      case QuantumButtonType.neural:
        return const LinearGradient(
          colors: [Color(0xFF4CAF50), Color(0xFF2E7D32)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        );
      case QuantumButtonType.mesh:
        return const LinearGradient(
          colors: [Color(0xFFFF9800), Color(0xFFF57C00)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        );
    }
  }

  Border? _getBorder() {
    switch (widget.type) {
      case QuantumButtonType.secondary:
        return Border.all(
          color: const Color(0xFF79747E),
          width: 1,
        );
      default:
        return null;
    }
  }

  List<BoxShadow> _getShadow() {
    return [
      BoxShadow(
        color: _getShadowColor().withOpacity(0.3),
        blurRadius: 8,
        offset: const Offset(0, 4),
      ),
    ];
  }

  Color _getShadowColor() {
    switch (widget.type) {
      case QuantumButtonType.primary:
        return const Color(0xFF0066CC);
      case QuantumButtonType.quantum:
        return const Color(0xFF0066CC);
      case QuantumButtonType.neural:
        return const Color(0xFF4CAF50);
      case QuantumButtonType.mesh:
        return const Color(0xFFFF9800);
      default:
        return const Color(0xFF565F71);
    }
  }

  Color _getSplashColor() {
    return _getTextColor().withOpacity(0.1);
  }

  Color _getHighlightColor() {
    return _getTextColor().withOpacity(0.05);
  }

  Color _getTextColor() {
    switch (widget.type) {
      case QuantumButtonType.secondary:
        return const Color(0xFF1A1C1E);
      default:
        return Colors.white;
    }
  }
}
