import 'package:flutter/material.dart';
import 'package:mesh_app/design_system/theme/colors/quantum_colors.dart';
import 'package:mesh_app/design_system/theme/typography/quantum_typography.dart';
import 'package:mesh_app/services/ai_adaptive_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AIAdaptiveUI extends ConsumerStatefulWidget {
  final Widget child;
  final String componentId;

  const AIAdaptiveUI({
    super.key,
    required this.child,
    required this.componentId,
  });

  @override
  ConsumerState<AIAdaptiveUI> createState() => _AIAdaptiveUIState();
}

class _AIAdaptiveUIState extends ConsumerState<AIAdaptiveUI>
    with TickerProviderStateMixin {
  late AnimationController _adaptationController;
  late Animation<double> _adaptationAnimation;

  String _currentUIMode = 'standard';
  Map<String, dynamic> _userPreferences = {};

  @override
  void initState() {
    super.initState();

    _adaptationController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );

    _adaptationAnimation = CurvedAnimation(
      parent: _adaptationController,
      curve: Curves.easeInOut,
    );

    // Start adaptation animation
    _adaptationController.forward();
  }

  @override
  void dispose() {
    _adaptationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final aiService = ref.watch(aiAdaptiveServiceProvider);

    return aiService.maybeWhen(
      data: (service) {
        _currentUIMode = service.currentState.uiMode;
        _userPreferences = service.currentState.userPreferences;

        return AnimatedBuilder(
          animation: _adaptationAnimation,
          builder: (context, child) {
            return _buildAdaptedUI(context);
          },
        );
      },
      orElse: () => widget.child,
    );
  }

  Widget _buildAdaptedUI(BuildContext context) {
    switch (_currentUIMode) {
      case 'focus':
        return _buildFocusMode(context);
      case 'relax':
        return _buildRelaxMode(context);
      case 'energy':
        return _buildEnergyMode(context);
      case 'calm':
        return _buildCalmMode(context);
      case 'quantum':
        return _buildQuantumMode(context);
      default:
        return _buildStandardMode(context);
    }
  }

  Widget _buildStandardMode(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        color: Theme.of(context).cardColor,
      ),
      child: widget.child,
    );
  }

  Widget _buildFocusMode(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        color: QuantumColors.aiFocus.withOpacity(0.1),
        border: Border.all(
          color: QuantumColors.aiFocus.withOpacity(0.3),
          width: 2,
        ),
      ),
      child: Theme(
        data: Theme.of(context).copyWith(
          textTheme: QuantumTypography.textTheme.copyWith(
            bodyLarge: QuantumTypography.bodyLarge.copyWith(
              fontWeight: FontWeight.w600,
              color: QuantumColors.aiFocus,
            ),
          ),
        ),
        child: widget.child,
      ),
    );
  }

  Widget _buildRelaxMode(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        color: QuantumColors.aiRelax.withOpacity(0.1),
        border: Border.all(
          color: QuantumColors.aiRelax.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Theme(
        data: Theme.of(context).copyWith(
          textTheme: QuantumTypography.textTheme.copyWith(
            bodyLarge: QuantumTypography.bodyLarge.copyWith(
              fontSize: 18,
              height: 1.6,
              color: QuantumColors.aiRelax,
            ),
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: widget.child,
        ),
      ),
    );
  }

  Widget _buildEnergyMode(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(4),
        color: QuantumColors.aiEnergy.withOpacity(0.1),
        border: Border.all(
          color: QuantumColors.aiEnergy.withOpacity(0.5),
          width: 3,
        ),
        boxShadow: [
          BoxShadow(
            color: QuantumColors.aiEnergy.withOpacity(0.3),
            blurRadius: 10,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Theme(
        data: Theme.of(context).copyWith(
          textTheme: QuantumTypography.textTheme.copyWith(
            bodyLarge: QuantumTypography.bodyLarge.copyWith(
              fontWeight: FontWeight.w700,
              fontSize: 16,
              color: QuantumColors.aiEnergy,
            ),
          ),
        ),
        child: widget.child,
      ),
    );
  }

  Widget _buildCalmMode(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        color: QuantumColors.aiCalm.withOpacity(0.05),
        border: Border.all(
          color: QuantumColors.aiCalm.withOpacity(0.2),
          width: 1,
        ),
      ),
      child: Theme(
        data: Theme.of(context).copyWith(
          textTheme: QuantumTypography.textTheme.copyWith(
            bodyLarge: QuantumTypography.bodyLarge.copyWith(
              fontSize: 15,
              height: 1.8,
              color: QuantumColors.aiCalm,
            ),
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: widget.child,
        ),
      ),
    );
  }

  Widget _buildQuantumMode(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        gradient: LinearGradient(
          colors: [
            QuantumColors.quantumField,
            QuantumColors.neuralNetwork,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        border: Border.all(
          color: QuantumColors.primary.withOpacity(0.5),
          width: 2,
        ),
        boxShadow: [
          BoxShadow(
            color: QuantumColors.primary.withOpacity(0.2),
            blurRadius: 15,
            spreadRadius: 3,
          ),
        ],
      ),
      child: Theme(
        data: Theme.of(context).copyWith(
          textTheme: QuantumTypography.textTheme.copyWith(
            bodyLarge: QuantumTypography.quantumDisplay(
              fontSize: 16,
              color: QuantumColors.primary,
            ),
          ),
        ),
        child: widget.child,
      ),
    );
  }
}

// AI-driven component sizing
class AdaptiveSizer extends ConsumerWidget {
  final Widget child;
  final String componentId;
  final double baseSize;

  const AdaptiveSizer({
    super.key,
    required this.child,
    required this.componentId,
    required this.baseSize,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final aiService = ref.watch(aiAdaptiveServiceProvider);

    return aiService.maybeWhen(
      data: (service) {
        final preferences = service.currentState.userPreferences;
        final sizeMultiplier = preferences['${componentId}_size'] ?? 1.0;

        return Transform.scale(
          scale: sizeMultiplier,
          child: SizedBox(
            width: baseSize * sizeMultiplier,
            height: baseSize * sizeMultiplier,
            child: child,
          ),
        );
      },
      orElse: () => SizedBox(
        width: baseSize,
        height: baseSize,
        child: child,
      ),
    );
  }
}

// AI-driven layout adaptation
class AdaptiveLayout extends ConsumerWidget {
  final List<Widget> children;
  final String layoutId;

  const AdaptiveLayout({
    super.key,
    required this.children,
    required this.layoutId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final aiService = ref.watch(aiAdaptiveServiceProvider);

    return aiService.maybeWhen(
      data: (service) {
        final uiMode = service.currentState.uiMode;

        switch (uiMode) {
          case 'focus':
            return _buildFocusLayout();
          case 'relax':
            return _buildRelaxLayout();
          case 'energy':
            return _buildEnergyLayout();
          case 'calm':
            return _buildCalmLayout();
          default:
            return _buildStandardLayout();
        }
      },
      orElse: () => _buildStandardLayout(),
    );
  }

  Widget _buildStandardLayout() {
    return Column(
      children: children,
    );
  }

  Widget _buildFocusLayout() {
    return Row(
      children: children.map((child) => Expanded(child: child)).toList(),
    );
  }

  Widget _buildRelaxLayout() {
    return Column(
      children: children.map((child) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: child,
      )).toList(),
    );
  }

  Widget _buildEnergyLayout() {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      children: children,
    );
  }

  Widget _buildCalmLayout() {
    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: children.length,
      separatorBuilder: (context, index) => const SizedBox(height: 16),
      itemBuilder: (context, index) => children[index],
    );
  }
}
