import 'package:flutter/material.dart';
import 'package:mesh_app/design_system/components/widgets/quantum_button.dart';
import 'package:mesh_app/design_system/components/widgets/quantum_card.dart';
import 'package:mesh_app/design_system/components/widgets/holographic_effect.dart';
import 'package:mesh_app/design_system/theme/colors/quantum_colors.dart';
import 'package:mesh_app/design_system/theme/typography/quantum_typography.dart';
import 'package:mesh_app/services/ai_adaptive_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen>
    with TickerProviderStateMixin {
  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeIn,
    ));

    _fadeController.forward();
  }

  @override
  void dispose() {
    _fadeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final aiService = ref.watch(aiAdaptiveServiceProvider);
    final isQuantumMode = aiService.maybeWhen(
      data: (state) => state.themeMode == 'quantum',
      orElse: () => false,
    );

    return Scaffold(
      backgroundColor: isQuantumMode
          ? QuantumColors.quantumField
          : Theme.of(context).scaffoldBackgroundColor,
      body: Stack(
        children: [
          // Background effects
          if (isQuantumMode) ...[
            const FractalBackground(
              child: SizedBox.expand(),
            ),
            const NeuralNetworkEffect(
              child: SizedBox.expand(),
            ),
          ],

          // Main content
          FadeTransition(
            opacity: _fadeAnimation,
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header
                  Text(
                    'Welcome to Mesh Network',
                    style: QuantumTypography.quantumDisplay(
                      fontSize: 32,
                      color: QuantumColors.primary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Decentralized communication powered by AI',
                    style: QuantumTypography.neuralText(
                      fontSize: 18,
                      color: QuantumColors.onSurface,
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Action buttons
                  Row(
                    children: [
                      Expanded(
                        child: QuantumButton(
                          text: 'Connect to Mesh',
                          type: QuantumButtonType.quantum,
                          icon: Icons.wifi,
                          onPressed: () {
                            // TODO: Implement mesh connection
                          },
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: QuantumButton(
                          text: 'AI Assistant',
                          type: QuantumButtonType.neural,
                          icon: Icons.smart_toy,
                          onPressed: () {
                            // TODO: Open AI assistant
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 32),

                  // Feature cards
                  Text(
                    'Features',
                    style: QuantumTypography.headlineSmall,
                  ),
                  const SizedBox(height: 16),

                  GridView.count(
                    crossAxisCount: MediaQuery.of(context).size.width > 600 ? 3 : 2,
                    crossAxisSpacing: 16,
                    mainAxisSpacing: 16,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    children: [
                      HolographicCard(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.wifi_tethering,
                              size: 48,
                              color: QuantumColors.primary,
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'Mesh Networking',
                              style: QuantumTypography.titleMedium,
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Peer-to-peer communication without internet',
                              style: QuantumTypography.bodySmall,
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                        onTap: () {
                          // TODO: Navigate to mesh settings
                        },
                      ),

                      NeuralCard(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.psychology,
                              size: 48,
                              color: QuantumColors.secondary,
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'AI Adaptation',
                              style: QuantumTypography.titleMedium,
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Interface adapts to your behavior patterns',
                              style: QuantumTypography.bodySmall,
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                        onTap: () {
                          // TODO: Navigate to AI settings
                        },
                      ),

                      MeshCard(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.security,
                              size: 48,
                              color: QuantumColors.tertiary,
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'End-to-End Encryption',
                              style: QuantumTypography.titleMedium,
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Secure communication across all platforms',
                              style: QuantumTypography.bodySmall,
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                        onTap: () {
                          // TODO: Navigate to security settings
                        },
                      ),

                      QuantumCard(
                        enableQuantumEffect: true,
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.science,
                              size: 48,
                              color: QuantumColors.primary,
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'Quantum Computing',
                              style: QuantumTypography.titleMedium,
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Graph-based ML training on device networks',
                              style: QuantumTypography.bodySmall,
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                        onTap: () {
                          // TODO: Navigate to quantum features
                        },
                      ),
                    ],
                  ),

                  const SizedBox(height: 32),

                  // Status section
                  QuantumCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Network Status',
                          style: QuantumTypography.titleLarge,
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            Container(
                              width: 12,
                              height: 12,
                              decoration: BoxDecoration(
                                color: QuantumColors.meshOnline,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Mesh Network: Connected',
                              style: QuantumTypography.bodyMedium,
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            Container(
                              width: 12,
                              height: 12,
                              decoration: BoxDecoration(
                                color: QuantumColors.aiFocus,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'AI Mode: Adaptive',
                              style: QuantumTypography.bodyMedium,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
