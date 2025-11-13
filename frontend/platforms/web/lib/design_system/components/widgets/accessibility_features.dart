import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:mesh_app/design_system/theme/colors/quantum_colors.dart';
import 'package:mesh_app/design_system/theme/typography/quantum_typography.dart';
import 'package:mesh_app/design_system/components/widgets/quantum_button.dart';

class AccessibilityFeatures extends StatefulWidget {
  final Widget child;
  final bool enableVoiceOver;
  final bool enableHighContrast;
  final bool enableLargeText;
  final bool enableReducedMotion;

  const AccessibilityFeatures({
    super.key,
    required this.child,
    this.enableVoiceOver = true,
    this.enableHighContrast = false,
    this.enableLargeText = false,
    this.enableReducedMotion = false,
  });

  @override
  State<AccessibilityFeatures> createState() => _AccessibilityFeaturesState();
}

class _AccessibilityFeaturesState extends State<AccessibilityFeatures> {
  late FlutterTts _flutterTts;
  late stt.SpeechToText _speechToText;

  bool _isInitialized = false;
  bool _isHighContrast = false;
  bool _isLargeText = false;
  bool _isReducedMotion = false;

  @override
  void initState() {
    super.initState();
    _initializeAccessibility();
  }

  @override
  void dispose() {
    _flutterTts.stop();
    super.dispose();
  }

  Future<void> _initializeAccessibility() async {
    _flutterTts = FlutterTts();
    _speechToText = stt.SpeechToText();

    await _flutterTts.setLanguage("en-US");
    await _flutterTts.setSpeechRate(0.8);
    await _flutterTts.setVolume(1.0);
    await _flutterTts.setPitch(1.0);

    _isInitialized = await _speechToText.initialize();

    setState(() {
      _isHighContrast = widget.enableHighContrast;
      _isLargeText = widget.enableLargeText;
      _isReducedMotion = widget.enableReducedMotion;
    });
  }

  Future<void> _speak(String text) async {
    if (widget.enableVoiceOver) {
      await _flutterTts.speak(text);
    }
  }

  void _toggleHighContrast() {
    setState(() {
      _isHighContrast = !_isHighContrast;
    });
    _speak(_isHighContrast ? "High contrast mode enabled" : "High contrast mode disabled");
  }

  void _toggleLargeText() {
    setState(() {
      _isLargeText = !_isLargeText;
    });
    _speak(_isLargeText ? "Large text mode enabled" : "Large text mode disabled");
  }

  void _toggleReducedMotion() {
    setState(() {
      _isReducedMotion = !_isReducedMotion;
    });
    _speak(_isReducedMotion ? "Reduced motion enabled" : "Reduced motion disabled");
  }

  @override
  Widget build(BuildContext context) {
    return Theme(
      data: _buildAccessibleTheme(Theme.of(context)),
      child: Stack(
        children: [
          widget.child,
          if (widget.enableVoiceOver)
            Positioned(
              bottom: 20,
              left: 20,
              child: FloatingActionButton(
                onPressed: () => _showAccessibilityMenu(context),
                backgroundColor: _isHighContrast ? Colors.black : QuantumColors.primary,
                child: Icon(
                  Icons.accessibility,
                  color: _isHighContrast ? Colors.white : Colors.white,
                ),
              ),
            ),
        ],
      ),
    );
  }

  ThemeData _buildAccessibleTheme(ThemeData baseTheme) {
    if (_isHighContrast) {
      return baseTheme.copyWith(
        brightness: Brightness.light,
        primaryColor: Colors.black,
        scaffoldBackgroundColor: Colors.white,
        cardColor: Colors.white,
        textTheme: QuantumTypography.textTheme.copyWith(
          bodyLarge: QuantumTypography.highContrastText(),
          bodyMedium: QuantumTypography.highContrastText(fontSize: 14),
          bodySmall: QuantumTypography.highContrastText(fontSize: 12),
          headlineLarge: QuantumTypography.highContrastText(fontSize: 24),
          headlineMedium: QuantumTypography.highContrastText(fontSize: 20),
          headlineSmall: QuantumTypography.highContrastText(fontSize: 18),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.black,
            foregroundColor: Colors.white,
            side: const BorderSide(color: Colors.black, width: 2),
          ),
        ),
      );
    }

    if (_isLargeText) {
      return baseTheme.copyWith(
        textTheme: QuantumTypography.textTheme.copyWith(
          bodyLarge: QuantumTypography.accessibleText(fontSize: 20),
          bodyMedium: QuantumTypography.accessibleText(fontSize: 18),
          bodySmall: QuantumTypography.accessibleText(fontSize: 16),
          headlineLarge: QuantumTypography.accessibleText(fontSize: 32),
          headlineMedium: QuantumTypography.accessibleText(fontSize: 28),
          headlineSmall: QuantumTypography.accessibleText(fontSize: 24),
        ),
      );
    }

    return baseTheme;
  }

  void _showAccessibilityMenu(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: _isHighContrast ? Colors.white : Theme.of(context).cardColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => Container(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Accessibility Settings',
              style: _isHighContrast
                  ? QuantumTypography.highContrastText(fontSize: 20)
                  : QuantumTypography.headlineSmall,
            ),
            const SizedBox(height: 24),
            _buildAccessibilityOption(
              'High Contrast',
              _isHighContrast,
              _toggleHighContrast,
            ),
            const SizedBox(height: 16),
            _buildAccessibilityOption(
              'Large Text',
              _isLargeText,
              _toggleLargeText,
            ),
            const SizedBox(height: 16),
            _buildAccessibilityOption(
              'Reduced Motion',
              _isReducedMotion,
              _toggleReducedMotion,
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: QuantumButton(
                    text: 'Voice Commands',
                    type: QuantumButtonType.secondary,
                    onPressed: () => _showVoiceCommands(context),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: QuantumButton(
                    text: 'Screen Reader',
                    type: QuantumButtonType.secondary,
                    onPressed: () => _startScreenReader(context),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAccessibilityOption(String title, bool isEnabled, VoidCallback onToggle) {
    return InkWell(
      onTap: onToggle,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
        decoration: BoxDecoration(
          border: Border.all(
            color: _isHighContrast ? Colors.black : QuantumColors.outline,
            width: 2,
          ),
          borderRadius: BorderRadius.circular(8),
          color: isEnabled
              ? (_isHighContrast ? Colors.black : QuantumColors.primary.withOpacity(0.1))
              : Colors.transparent,
        ),
        child: Row(
          children: [
            Expanded(
              child: Text(
                title,
                style: _isHighContrast
                    ? QuantumTypography.highContrastText()
                    : QuantumTypography.bodyLarge,
              ),
            ),
            Icon(
              isEnabled ? Icons.check_circle : Icons.circle_outlined,
              color: isEnabled
                  ? (_isHighContrast ? Colors.white : QuantumColors.primary)
                  : (_isHighContrast ? Colors.black : QuantumColors.onSurfaceVariant),
            ),
          ],
        ),
      ),
    );
  }

  void _showVoiceCommands(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: _isHighContrast ? Colors.white : Theme.of(context).cardColor,
        title: Text(
          'Voice Commands',
          style: _isHighContrast
              ? QuantumTypography.highContrastText()
              : QuantumTypography.headlineSmall,
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildVoiceCommand('Connect to mesh', 'Join mesh network'),
            _buildVoiceCommand('Disconnect', 'Leave mesh network'),
            _buildVoiceCommand('Open AI assistant', 'Start AI conversation'),
            _buildVoiceCommand('Settings', 'Open app settings'),
            _buildVoiceCommand('Help', 'Show available commands'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text(
              'Close',
              style: _isHighContrast
                  ? QuantumTypography.highContrastText()
                  : QuantumTypography.labelLarge,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVoiceCommand(String command, String description) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '"$command"',
            style: _isHighContrast
                ? QuantumTypography.highContrastText(fontSize: 16, fontWeight: FontWeight.w600)
                : QuantumTypography.bodyMedium.copyWith(fontWeight: FontWeight.w600),
          ),
          Text(
            description,
            style: _isHighContrast
                ? QuantumTypography.highContrastText(fontSize: 14)
                : QuantumTypography.bodySmall,
          ),
        ],
      ),
    );
  }

  void _startScreenReader(BuildContext context) {
    _speak('Screen reader activated. Navigating through interface elements.');
    // TODO: Implement screen reader navigation
  }
}

// Screen reader focusable widget
class ScreenReaderFocusable extends StatefulWidget {
  final Widget child;
  final String label;
  final String hint;
  final VoidCallback? onFocus;
  final VoidCallback? onActivate;

  const ScreenReaderFocusable({
    super.key,
    required this.child,
    required this.label,
    this.hint = '',
    this.onFocus,
    this.onActivate,
  });

  @override
  State<ScreenReaderFocusable> createState() => _ScreenReaderFocusableState();
}

class _ScreenReaderFocusableState extends State<ScreenReaderFocusable> {
  bool _hasFocus = false;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: widget.label,
      hint: widget.hint,
      focused: _hasFocus,
      child: Focus(
        onFocusChange: (hasFocus) {
          setState(() {
            _hasFocus = hasFocus;
          });
          if (hasFocus) {
            widget.onFocus?.call();
          }
        },
        onKey: (node, event) {
          if (event.logicalKey.keyLabel == 'Enter' || event.logicalKey.keyLabel == ' ') {
            widget.onActivate?.call();
            return KeyEventResult.handled;
          }
          return KeyEventResult.ignored;
        },
        child: Container(
          decoration: _hasFocus ? BoxDecoration(
            border: Border.all(
              color: QuantumColors.primary,
              width: 2,
            ),
            borderRadius: BorderRadius.circular(4),
          ) : null,
          child: widget.child,
        ),
      ),
    );
  }
}

// Keyboard navigation helper
class KeyboardNavigation extends StatelessWidget {
  final Widget child;
  final Map<LogicalKeyboardKey, VoidCallback> keyHandlers;

  const KeyboardNavigation({
    super.key,
    required this.child,
    required this.keyHandlers,
  });

  @override
  Widget build(BuildContext context) {
    return Focus(
      onKey: (node, event) {
        final handler = keyHandlers[event.logicalKey];
        if (handler != null) {
          handler();
          return KeyEventResult.handled;
        }
        return KeyEventResult.ignored;
      },
      child: child,
    );
  }
}
