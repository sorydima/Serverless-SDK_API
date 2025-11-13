import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_tts/flutter_tts.dart';
import 'package:mesh_app/design_system/theme/colors/quantum_colors.dart';
import 'package:mesh_app/design_system/theme/typography/quantum_typography.dart';
import 'package:mesh_app/design_system/components/widgets/quantum_button.dart';

class VoiceControl extends StatefulWidget {
  final Function(String)? onCommandRecognized;
  final Function(String)? onSpeechResult;
  final bool enableTTS;

  const VoiceControl({
    super.key,
    this.onCommandRecognized,
    this.onSpeechResult,
    this.enableTTS = true,
  });

  @override
  State<VoiceControl> createState() => _VoiceControlState();
}

class _VoiceControlState extends State<VoiceControl>
    with TickerProviderStateMixin {
  late stt.SpeechToText _speech;
  late FlutterTts _flutterTts;
  bool _isListening = false;
  bool _isInitialized = false;
  String _lastWords = '';
  String _statusText = 'Tap to speak';

  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _initializeSpeech();
    _initializeTTS();

    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(
      begin: 1.0,
      end: 1.2,
    ).animate(CurvedAnimation(
      parent: _pulseController,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _speech.stop();
    _flutterTts.stop();
    super.dispose();
  }

  Future<void> _initializeSpeech() async {
    _speech = stt.SpeechToText();
    _isInitialized = await _speech.initialize(
      onStatus: _onSpeechStatus,
      onError: _onSpeechError,
    );
    setState(() {});
  }

  Future<void> _initializeTTS() async {
    _flutterTts = FlutterTts();

    // Configure TTS
    await _flutterTts.setLanguage("en-US");
    await _flutterTts.setSpeechRate(0.5);
    await _flutterTts.setVolume(1.0);
    await _flutterTts.setPitch(1.0);

    // Set completion handler
    _flutterTts.setCompletionHandler(() {
      setState(() {
        _statusText = 'Voice ready';
      });
    });
  }

  void _onSpeechStatus(String status) {
    setState(() {
      _statusText = status;
    });
  }

  void _onSpeechError(String error) {
    setState(() {
      _statusText = 'Error: $error';
      _isListening = false;
    });
  }

  Future<void> _startListening() async {
    if (!_isInitialized) return;

    setState(() {
      _isListening = true;
      _statusText = 'Listening...';
    });

    await _speech.listen(
      onResult: (result) {
        setState(() {
          _lastWords = result.recognizedWords;
          _statusText = 'Heard: $_lastWords';
        });

        widget.onSpeechResult?.call(_lastWords);
        _processVoiceCommand(_lastWords);
      },
      listenFor: const Duration(seconds: 30),
      pauseFor: const Duration(seconds: 5),
      partialResults: true,
      localeId: 'en_US',
      cancelOnError: true,
      listenMode: stt.ListenMode.confirmation,
    );
  }

  Future<void> _stopListening() async {
    await _speech.stop();
    setState(() {
      _isListening = false;
      _statusText = 'Tap to speak';
    });
  }

  void _processVoiceCommand(String command) {
    final lowerCommand = command.toLowerCase();

    // Voice commands for mesh app
    if (lowerCommand.contains('connect') || lowerCommand.contains('join')) {
      widget.onCommandRecognized?.call('connect_mesh');
      _speak('Connecting to mesh network');
    } else if (lowerCommand.contains('disconnect') || lowerCommand.contains('leave')) {
      widget.onCommandRecognized?.call('disconnect_mesh');
      _speak('Disconnecting from mesh network');
    } else if (lowerCommand.contains('ai') || lowerCommand.contains('assistant')) {
      widget.onCommandRecognized?.call('open_ai');
      _speak('Opening AI assistant');
    } else if (lowerCommand.contains('settings') || lowerCommand.contains('preferences')) {
      widget.onCommandRecognized?.call('open_settings');
      _speak('Opening settings');
    } else if (lowerCommand.contains('help') || lowerCommand.contains('what can you do')) {
      _speakAvailableCommands();
    } else {
      widget.onCommandRecognized?.call('unknown_command');
      _speak('Command not recognized. Say help for available commands.');
    }
  }

  void _speakAvailableCommands() {
    const commands = '''
      Available voice commands:
      Connect to mesh - Join the mesh network
      Disconnect from mesh - Leave the mesh network
      Open AI assistant - Start AI conversation
      Open settings - Access app settings
      Help - List available commands
    ''';
    _speak(commands);
  }

  Future<void> _speak(String text) async {
    if (!widget.enableTTS) return;

    await _flutterTts.speak(text);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Voice control button
        AnimatedBuilder(
          animation: _pulseAnimation,
          builder: (context, child) {
            return Transform.scale(
              scale: _isListening ? _pulseAnimation.value : 1.0,
              child: GestureDetector(
                onTap: _isListening ? _stopListening : _startListening,
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      colors: _isListening
                          ? [QuantumColors.aiFocus, QuantumColors.primary]
                          : [QuantumColors.secondary, QuantumColors.secondaryContainer],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: (_isListening ? QuantumColors.aiFocus : QuantumColors.secondary)
                            .withOpacity(0.3),
                        blurRadius: 12,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: Icon(
                    _isListening ? Icons.mic : Icons.mic_none,
                    color: Colors.white,
                    size: 32,
                  ),
                ),
              ),
            );
          },
        ),

        const SizedBox(height: 16),

        // Status text
        Text(
          _statusText,
          style: QuantumTypography.bodyMedium.copyWith(
            color: _isListening ? QuantumColors.aiFocus : QuantumColors.onSurface,
          ),
          textAlign: TextAlign.center,
        ),

        // Last recognized words
        if (_lastWords.isNotEmpty) ...[
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: QuantumColors.surfaceVariant,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              '"$_lastWords"',
              style: QuantumTypography.bodyMedium.copyWith(
                fontStyle: FontStyle.italic,
              ),
              textAlign: TextAlign.center,
            ),
          ),
        ],

        const SizedBox(height: 16),

        // Quick action buttons
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            QuantumButton(
              text: 'Help',
              type: QuantumButtonType.secondary,
              onPressed: _speakAvailableCommands,
            ),
            const SizedBox(width: 8),
            QuantumButton(
              text: 'Test TTS',
              type: QuantumButtonType.secondary,
              onPressed: () => _speak('Voice control is working'),
            ),
          ],
        ),
      ],
    );
  }
}

// Accessibility wrapper widget
class AccessibleVoiceControl extends StatelessWidget {
  final Widget child;
  final Function(String)? onCommandRecognized;

  const AccessibleVoiceControl({
    super.key,
    required this.child,
    this.onCommandRecognized,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        child,
        Positioned(
          bottom: 20,
          right: 20,
          child: Semantics(
            label: 'Voice control button',
            hint: 'Tap to activate voice commands',
            child: FloatingActionButton(
              onPressed: () {
                showModalBottomSheet(
                  context: context,
                  backgroundColor: Colors.transparent,
                  builder: (context) => Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: Theme.of(context).scaffoldBackgroundColor,
                      borderRadius: const BorderRadius.vertical(
                        top: Radius.circular(20),
                      ),
                    ),
                    child: VoiceControl(
                      onCommandRecognized: onCommandRecognized,
                    ),
                  ),
                );
              },
              backgroundColor: QuantumColors.primary,
              child: const Icon(
                Icons.mic,
                color: Colors.white,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
