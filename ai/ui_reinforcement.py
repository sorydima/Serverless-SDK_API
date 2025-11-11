"""
AI-Driven UI Adaptation with Reinforcement Learning

This module implements reinforcement learning models to adapt the user interface
based on user behavior patterns, preferences, and interaction history.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
import os
from pathlib import Path
import random
from collections import defaultdict
import pickle

logger = logging.getLogger(__name__)

@dataclass
class UIState:
    """Represents the current state of the UI"""
    screen_name: str
    elements_visible: Set[str]
    user_context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class UIAction:
    """Represents a UI adaptation action"""
    action_type: str  # 'show', 'hide', 'reorder', 'resize', 'theme_change'
    target_element: str
    parameters: Dict[str, Any]
    confidence: float = 0.0

@dataclass
class UserInteraction:
    """Records a user interaction for learning"""
    state: UIState
    action_taken: UIAction
    reward: float
    next_state: UIState
    timestamp: datetime

class UIReinforcementLearner:
    """
    Reinforcement learning agent for UI adaptation

    Uses Q-learning with function approximation to learn optimal UI adaptations
    based on user behavior and satisfaction signals.
    """

    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.9,
                 exploration_rate: float = 0.1, model_path: str = "./models/ui_rl.pkl"):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

        # Q-table with state-action values
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        # Feature weights for function approximation
        self.feature_weights = np.random.randn(50)  # 50 features

        # Experience replay buffer
        self.experience_buffer: List[UserInteraction] = []
        self.buffer_size = 10000

        # User behavior patterns
        self.user_patterns: Dict[str, Dict[str, Any]] = {}

        # UI adaptation rules
        self.adaptation_rules = self._initialize_adaptation_rules()

        self._load_model()

    def _initialize_adaptation_rules(self) -> Dict[str, List[UIAction]]:
        """Initialize basic UI adaptation rules"""
        return {
            'dashboard': [
                UIAction('show', 'quick_actions', {'position': 'top'}),
                UIAction('hide', 'advanced_settings', {}),
                UIAction('reorder', 'navigation', {'priority': ['messages', 'contacts', 'settings']})
            ],
            'messaging': [
                UIAction('show', 'emoji_picker', {'position': 'bottom'}),
                UIAction('resize', 'input_field', {'height': 'expanded'}),
                UIAction('theme_change', 'conversation', {'style': 'minimal'})
            ],
            'settings': [
                UIAction('hide', 'developer_options', {}),
                UIAction('show', 'accessibility', {'expanded': True}),
                UIAction('reorder', 'categories', {'priority': ['privacy', 'notifications', 'appearance']})
            ]
        }

    def _load_model(self):
        """Load trained model if exists"""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.q_table = data.get('q_table', self.q_table)
                    self.feature_weights = data.get('feature_weights', self.feature_weights)
                    self.user_patterns = data.get('user_patterns', self.user_patterns)
                logger.info("Loaded UI RL model")
            except Exception as e:
                logger.error(f"Failed to load UI RL model: {e}")

    def _save_model(self):
        """Save trained model"""
        try:
            data = {
                'q_table': dict(self.q_table),
                'feature_weights': self.feature_weights,
                'user_patterns': self.user_patterns
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(data, f)
            logger.info("Saved UI RL model")
        except Exception as e:
            logger.error(f"Failed to save UI RL model: {e}")

    def _state_to_features(self, state: UIState) -> np.ndarray:
        """Convert UI state to feature vector"""
        features = []

        # Screen type encoding (one-hot)
        screens = ['dashboard', 'messaging', 'settings', 'contacts', 'profile']
        for screen in screens:
            features.append(1.0 if state.screen_name == screen else 0.0)

        # Element visibility (binary)
        common_elements = ['quick_actions', 'navigation', 'search', 'notifications',
                          'settings', 'profile', 'messages', 'contacts']
        for element in common_elements:
            features.append(1.0 if element in state.elements_visible else 0.0)

        # Time-based features
        hour = state.timestamp.hour
        features.append(np.sin(2 * np.pi * hour / 24))  # Hour sine
        features.append(np.cos(2 * np.pi * hour / 24))  # Hour cosine
        features.append(1.0 if state.timestamp.weekday() >= 5 else 0.0)  # Weekend

        # User context features
        context = state.user_context
        features.append(context.get('interaction_frequency', 0.5))
        features.append(context.get('preference_complexity', 0.5))
        features.append(context.get('device_type_mobile', 1.0))
        features.append(context.get('theme_dark', 0.0))

        # Pad to fixed size
        while len(features) < 50:
            features.append(0.0)

        return np.array(features[:50])

    def _get_state_key(self, state: UIState) -> str:
        """Get string key for state"""
        return f"{state.screen_name}_{hash(str(sorted(state.elements_visible)))}_{state.timestamp.hour}"

    def _get_action_key(self, action: UIAction) -> str:
        """Get string key for action"""
        return f"{action.action_type}_{action.target_element}_{hash(str(action.parameters))}"

    def choose_action(self, state: UIState) -> UIAction:
        """
        Choose the best action for the current state using epsilon-greedy policy
        """
        state_key = self._state_to_features(state)

        # Exploration vs exploitation
        if random.random() < self.exploration_rate:
            # Random action from adaptation rules
            screen_rules = self.adaptation_rules.get(state.screen_name, [])
            if screen_rules:
                return random.choice(screen_rules)
            else:
                # Default random action
                return UIAction('show', 'quick_actions', {})

        # Exploitation: choose best action
        best_action = None
        best_value = float('-inf')

        # Try actions from adaptation rules
        for action in self.adaptation_rules.get(state.screen_name, []):
            action_key = self._get_action_key(action)
            q_value = np.dot(state_key, self.feature_weights)

            if q_value > best_value:
                best_value = q_value
                best_action = action

        return best_action or UIAction('show', 'quick_actions', {})

    def learn_from_interaction(self, interaction: UserInteraction):
        """
        Learn from user interaction using Q-learning update
        """
        # Add to experience buffer
        self.experience_buffer.append(interaction)
        if len(self.experience_buffer) > self.buffer_size:
            self.experience_buffer.pop(0)

        # Q-learning update
        state_features = self._state_to_features(interaction.state)
        next_state_features = self._state_to_features(interaction.next_state)

        # Current Q value
        current_q = np.dot(state_features, self.feature_weights)

        # Next Q value (max over actions)
        next_q = np.dot(next_state_features, self.feature_weights)

        # TD target
        td_target = interaction.reward + self.discount_factor * next_q

        # TD error
        td_error = td_target - current_q

        # Update feature weights
        self.feature_weights += self.learning_rate * td_error * state_features

        # Update user patterns
        user_id = interaction.state.user_context.get('user_id', 'default')
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = {
                'preferred_actions': defaultdict(int),
                'screen_usage': defaultdict(int),
                'adaptation_success': []
            }

        # Track preferences
        action_key = self._get_action_key(interaction.action_taken)
        self.user_patterns[user_id]['preferred_actions'][action_key] += 1
        self.user_patterns[user_id]['screen_usage'][interaction.state.screen_name] += 1
        self.user_patterns[user_id]['adaptation_success'].append(interaction.reward)

        # Keep only recent history
        if len(self.user_patterns[user_id]['adaptation_success']) > 100:
            self.user_patterns[user_id]['adaptation_success'] = self.user_patterns[user_id]['adaptation_success'][-50:]

    def get_personalized_adaptations(self, user_id: str, current_state: UIState) -> List[UIAction]:
        """
        Get personalized UI adaptations based on user history
        """
        if user_id not in self.user_patterns:
            return self.adaptation_rules.get(current_state.screen_name, [])

        patterns = self.user_patterns[user_id]
        preferred_actions = patterns['preferred_actions']

        # Get top preferred actions
        sorted_actions = sorted(preferred_actions.items(), key=lambda x: x[1], reverse=True)
        top_actions = [action_key for action_key, _ in sorted_actions[:3]]

        # Convert back to UIAction objects
        personalized_actions = []
        for action_key in top_actions:
            # Parse action key (simplified)
            parts = action_key.split('_', 2)
            if len(parts) >= 3:
                action_type, target, params_hash = parts
                # Create action (parameters would need proper parsing in production)
                action = UIAction(action_type, target, {})
                personalized_actions.append(action)

        return personalized_actions or self.adaptation_rules.get(current_state.screen_name, [])

    def adapt_ui(self, current_state: UIState, user_id: Optional[str] = None) -> List[UIAction]:
        """
        Main method to get UI adaptations for current state
        """
        if user_id and user_id in self.user_patterns:
            # Use personalized adaptations
            actions = self.get_personalized_adaptations(user_id, current_state)
        else:
            # Use RL-based adaptation
            primary_action = self.choose_action(current_state)
            actions = [primary_action]

        # Add complementary actions based on rules
        rule_actions = self.adaptation_rules.get(current_state.screen_name, [])
        actions.extend(rule_actions[:2])  # Add up to 2 rule-based actions

        return actions[:5]  # Limit to 5 adaptations

    def provide_feedback(self, user_id: str, state: UIState, action: UIAction,
                        user_feedback: float):
        """
        Provide explicit user feedback for learning
        """
        # Create synthetic interaction for learning
        next_state = UIState(
            screen_name=state.screen_name,
            elements_visible=state.elements_visible.copy(),
            user_context=state.user_context
        )

        interaction = UserInteraction(
            state=state,
            action_taken=action,
            reward=user_feedback,
            next_state=next_state,
            timestamp=datetime.now()
        )

        self.learn_from_interaction(interaction)

    def save_model_periodically(self):
        """Save model (call this periodically)"""
        self._save_model()

    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            'experience_buffer_size': len(self.experience_buffer),
            'unique_users': len(self.user_patterns),
            'q_table_size': len(self.q_table),
            'exploration_rate': self.exploration_rate,
            'learning_rate': self.learning_rate
        }


class UIAdaptationManager:
    """
    Manages UI adaptation across different platforms and contexts
    """

    def __init__(self, learner: UIReinforcementLearner):
        self.learner = learner
        self.active_sessions: Dict[str, UIState] = {}
        self.adaptation_history: Dict[str, List[UIAction]] = defaultdict(list)

    def start_session(self, session_id: str, initial_state: UIState):
        """Start a new UI adaptation session"""
        self.active_sessions[session_id] = initial_state

    def get_adaptations(self, session_id: str) -> List[UIAction]:
        """Get UI adaptations for active session"""
        if session_id not in self.active_sessions:
            return []

        current_state = self.active_sessions[session_id]
        user_id = current_state.user_context.get('user_id')

        adaptations = self.learner.adapt_ui(current_state, user_id)
        self.adaptation_history[session_id].extend(adaptations)

        return adaptations

    def update_session_state(self, session_id: str, new_state: UIState):
        """Update the state of an active session"""
        if session_id in self.active_sessions:
            old_state = self.active_sessions[session_id]
            self.active_sessions[session_id] = new_state

            # Learn from implicit feedback (state transitions)
            # This is simplified - in practice would need explicit rewards
            reward = 0.1  # Small positive reward for continued interaction
            action = UIAction('transition', 'state', {})  # Placeholder action

            interaction = UserInteraction(
                state=old_state,
                action_taken=action,
                reward=reward,
                next_state=new_state,
                timestamp=datetime.now()
            )

            self.learner.learn_from_interaction(interaction)

    def end_session(self, session_id: str):
        """End a UI adaptation session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    def get_session_history(self, session_id: str) -> List[UIAction]:
        """Get adaptation history for a session"""
        return self.adaptation_history.get(session_id, [])


# Convenience functions
def create_ui_adaptation_system(model_path: str = "./models/ui_rl.pkl") -> UIAdaptationManager:
    """Factory function to create UI adaptation system"""
    learner = UIReinforcementLearner(model_path=model_path)
    manager = UIAdaptationManager(learner)
    return manager

# Example usage
if __name__ == "__main__":
    # Create adaptation system
    manager = create_ui_adaptation_system()

    # Simulate user session
    session_id = "user_123"
    initial_state = UIState(
        screen_name="dashboard",
        elements_visible={"navigation", "messages", "settings"},
        user_context={"user_id": "user_123", "theme_dark": True}
    )

    manager.start_session(session_id, initial_state)

    # Get adaptations
    adaptations = manager.get_adaptations(session_id)
    print(f"UI Adaptations: {[f'{a.action_type} {a.target_element}' for a in adaptations]}")

    # Simulate state change
    new_state = UIState(
        screen_name="messaging",
        elements_visible={"input_field", "emoji_picker", "send_button"},
        user_context={"user_id": "user_123", "interaction_frequency": 0.8}
    )

    manager.update_session_state(session_id, new_state)

    # Get new adaptations
    adaptations = manager.get_adaptations(session_id)
    print(f"New Adaptations: {[f'{a.action_type} {a.target_element}' for a in adaptations]}")

    manager.end_session(session_id)
