"""
Offline GenAI Assistant with GPT-like Capabilities

This module implements an offline AI assistant using local language models
that provides GPT-like conversational capabilities without internet dependency.
"""

import asyncio
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple, Any, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
import os
from pathlib import Path
import pickle
import hashlib
from collections import defaultdict, deque
import threading
import time

# Optional imports for different model backends
try:
    import transformers
    from transformers import AutoTokenizer, AutoModelForCausalLM
    _HAS_TRANSFORMERS = True
except ImportError:
    _HAS_TRANSFORMERS = False

try:
    import llama_cpp
    _HAS_LLAMA_CPP = True
except ImportError:
    _HAS_LLAMA_CPP = False

logger = logging.getLogger(__name__)

@dataclass
class ConversationMessage:
    """Represents a message in the conversation"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConversationContext:
    """Context for the current conversation"""
    conversation_id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    context_window: int = 10  # Number of recent messages to keep
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    session_start: datetime = field(default_factory=datetime.now)

@dataclass
class AssistantResponse:
    """Response from the AI assistant"""
    content: str
    confidence: float
    tokens_used: int
    processing_time: float
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class LocalLanguageModel:
    """
    Wrapper for local language model inference
    Supports multiple backends: Transformers, Llama.cpp, etc.
    """

    def __init__(self, model_path: str, model_type: str = "auto",
                 max_tokens: int = 512, temperature: float = 0.7):
        self.model_path = Path(model_path)
        self.model_type = model_type
        self.max_tokens = max_tokens
        self.temperature = temperature

        self.model = None
        self.tokenizer = None
        self.is_loaded = False

        # Model-specific configurations
        self.configs = {
            'transformers': {
                'device': 'cpu',  # Use CPU for offline operation
                'torch_dtype': torch.float32,
                'low_cpu_mem_usage': True
            },
            'llama_cpp': {
                'n_ctx': 2048,
                'n_threads': max(1, os.cpu_count() // 2),
                'n_batch': 512
            }
        }

    def load_model(self) -> bool:
        """Load the language model"""
        try:
            if self.model_type == 'auto':
                # Auto-detect based on available libraries and file extensions
                if _HAS_LLAMA_CPP and self.model_path.suffix in ['.gguf', '.bin']:
                    self.model_type = 'llama_cpp'
                elif _HAS_TRANSFORMERS:
                    self.model_type = 'transformers'
                else:
                    raise RuntimeError("No supported model backend available")

            if self.model_type == 'transformers' and _HAS_TRANSFORMERS:
                self._load_transformers_model()
            elif self.model_type == 'llama_cpp' and _HAS_LLAMA_CPP:
                self._load_llama_cpp_model()
            else:
                raise RuntimeError(f"Unsupported model type: {self.model_type}")

            self.is_loaded = True
            logger.info(f"Loaded {self.model_type} model from {self.model_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def _load_transformers_model(self):
        """Load model using Transformers library"""
        config = self.configs['transformers']

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            local_files_only=True
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            device_map=config['device'],
            torch_dtype=config['torch_dtype'],
            low_cpu_mem_usage=config['low_cpu_mem_usage'],
            local_files_only=True
        )

        # Set padding token if not present
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _load_llama_cpp_model(self):
        """Load model using Llama.cpp"""
        config = self.configs['llama_cpp']

        self.model = llama_cpp.Llama(
            model_path=str(self.model_path),
            n_ctx=config['n_ctx'],
            n_threads=config['n_threads'],
            n_batch=config['n_batch'],
            verbose=False
        )

    async def generate_response(self, prompt: str, context: List[Dict[str, str]] = None,
                              **kwargs) -> AssistantResponse:
        """Generate a response from the model"""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        try:
            if self.model_type == 'transformers':
                response = await self._generate_transformers(prompt, context, **kwargs)
            elif self.model_type == 'llama_cpp':
                response = await self._generate_llama_cpp(prompt, context, **kwargs)
            else:
                raise RuntimeError(f"Unsupported model type: {self.model_type}")

            processing_time = time.time() - start_time

            return AssistantResponse(
                content=response['text'],
                confidence=response.get('confidence', 0.8),
                tokens_used=response.get('tokens_used', 0),
                processing_time=processing_time,
                suggestions=response.get('suggestions', []),
                metadata=response.get('metadata', {})
            )

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return AssistantResponse(
                content="I apologize, but I'm having trouble generating a response right now.",
                confidence=0.0,
                tokens_used=0,
                processing_time=time.time() - start_time,
                metadata={'error': str(e)}
            )

    async def _generate_transformers(self, prompt: str, context: List[Dict[str, str]] = None,
                                   **kwargs) -> Dict[str, Any]:
        """Generate using Transformers"""
        # Format conversation
        if context:
            conversation = self._format_conversation_transformers(context + [{"role": "user", "content": prompt}])
        else:
            conversation = prompt

        inputs = self.tokenizer(conversation, return_tensors="pt", padding=True, truncation=True)

        # Move to appropriate device
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                **kwargs
            )

        # Decode response
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract only the new part
        if context:
            response_text = full_response[len(conversation):].strip()
        else:
            response_text = full_response.strip()

        return {
            'text': response_text,
            'tokens_used': len(outputs[0]),
            'confidence': 0.8,  # Placeholder
            'suggestions': []
        }

    async def _generate_llama_cpp(self, prompt: str, context: List[Dict[str, str]] = None,
                                **kwargs) -> Dict[str, Any]:
        """Generate using Llama.cpp"""
        # Format conversation
        if context:
            conversation = self._format_conversation_llama(context + [{"role": "user", "content": prompt}])
        else:
            conversation = prompt

        # Generate response
        response = self.model(
            conversation,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            echo=False,
            **kwargs
        )

        return {
            'text': response['choices'][0]['text'].strip(),
            'tokens_used': response['usage']['total_tokens'],
            'confidence': 0.8,  # Placeholder
            'suggestions': []
        }

    def _format_conversation_transformers(self, messages: List[Dict[str, str]]) -> str:
        """Format conversation for Transformers models"""
        formatted = ""
        for msg in messages:
            role = msg['role']
            content = msg['content']
            if role == 'system':
                formatted += f"System: {content}\n"
            elif role == 'user':
                formatted += f"User: {content}\n"
            elif role == 'assistant':
                formatted += f"Assistant: {content}\n"
        formatted += "Assistant:"
        return formatted

    def _format_conversation_llama(self, messages: List[Dict[str, str]]) -> str:
        """Format conversation for Llama models"""
        formatted = ""
        for msg in messages:
            role = msg['role']
            content = msg['content']
            if role == 'system':
                formatted += f"<|system|>\n{content}\n"
            elif role == 'user':
                formatted += f"<|user|>\n{content}\n"
            elif role == 'assistant':
                formatted += f"<|assistant|>\n{content}\n"
        formatted += "<|assistant|>\n"
        return formatted

    def unload_model(self):
        """Unload the model to free memory"""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        self.model = None
        self.tokenizer = None
        self.is_loaded = False

        # Force garbage collection
        import gc
        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

class ConversationManager:
    """
    Manages conversations and context for the AI assistant
    """

    def __init__(self, max_conversations: int = 100, context_window: int = 10):
        self.max_conversations = max_conversations
        self.context_window = context_window
        self.conversations: Dict[str, ConversationContext] = {}
        self.conversation_cache: Dict[str, ConversationContext] = {}

        # Conversation persistence
        self.cache_file = Path("./cache/conversations.pkl")
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        self._load_cache()

    def _load_cache(self):
        """Load conversation cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    self.conversation_cache = pickle.load(f)
                logger.info(f"Loaded {len(self.conversation_cache)} cached conversations")
            except Exception as e:
                logger.error(f"Failed to load conversation cache: {e}")

    def _save_cache(self):
        """Save conversation cache"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.conversation_cache, f)
        except Exception as e:
            logger.error(f"Failed to save conversation cache: {e}")

    def create_conversation(self, user_id: str, system_prompt: str = None) -> str:
        """Create a new conversation"""
        conversation_id = f"{user_id}_{int(time.time())}_{hashlib.md5(user_id.encode()).hexdigest()[:8]}"

        context = ConversationContext(
            conversation_id=conversation_id,
            context_window=self.context_window
        )

        if system_prompt:
            system_msg = ConversationMessage(
                role='system',
                content=system_prompt
            )
            context.messages.append(system_msg)

        self.conversations[conversation_id] = context

        # Clean up old conversations
        if len(self.conversations) > self.max_conversations:
            oldest_id = min(self.conversations.keys(),
                          key=lambda x: self.conversations[x].session_start)
            self.conversation_cache[oldest_id] = self.conversations[oldest_id]
            del self.conversations[oldest_id]

        return conversation_id

    def add_message(self, conversation_id: str, message: ConversationMessage):
        """Add a message to the conversation"""
        if conversation_id not in self.conversations:
            # Try to load from cache
            if conversation_id in self.conversation_cache:
                self.conversations[conversation_id] = self.conversation_cache[conversation_id]
                del self.conversation_cache[conversation_id]
            else:
                raise ValueError(f"Conversation {conversation_id} not found")

        context = self.conversations[conversation_id]
        context.messages.append(message)

        # Maintain context window
        if len(context.messages) > context.context_window:
            context.messages = context.messages[-context.context_window:]

    def get_conversation_context(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation context for model input"""
        if conversation_id not in self.conversations:
            return []

        context = self.conversations[conversation_id]
        return [
            {"role": msg.role, "content": msg.content}
            for msg in context.messages
        ]

    def update_user_preferences(self, conversation_id: str, preferences: Dict[str, Any]):
        """Update user preferences for the conversation"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].user_preferences.update(preferences)

    def get_user_preferences(self, conversation_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        if conversation_id in self.conversations:
            return self.conversations[conversation_id].user_preferences
        return {}

    def end_conversation(self, conversation_id: str):
        """End and archive a conversation"""
        if conversation_id in self.conversations:
            self.conversation_cache[conversation_id] = self.conversations[conversation_id]
            del self.conversations[conversation_id]
            self._save_cache()

class GenAIAssistant:
    """
    Main GenAI Assistant class providing offline GPT-like capabilities
    """

    def __init__(self, model_path: str, model_type: str = "auto",
                 system_prompt: str = None):
        self.model = LocalLanguageModel(model_path, model_type)
        self.conversation_manager = ConversationManager()
        self.system_prompt = system_prompt or self._default_system_prompt()

        # Assistant capabilities
        self.capabilities = {
            'general_chat': True,
            'code_help': True,
            'task_planning': True,
            'offline_operation': True,
            'context_awareness': True
        }

        # Response cache for performance
        self.response_cache: Dict[str, AssistantResponse] = {}
        self.cache_ttl = timedelta(minutes=30)

    def _default_system_prompt(self) -> str:
        """Default system prompt for the assistant"""
        return """You are Katya AI, an advanced AI assistant designed for privacy, security, and decentralization.
You operate offline and provide helpful, accurate responses while maintaining user privacy.
You have access to various tools and can help with:
- General questions and conversation
- Technical assistance and coding help
- Task planning and organization
- Privacy-focused advice
- Decentralized system operations

Always be helpful, truthful, and maintain user privacy. If you don't know something, say so clearly."""

    async def initialize(self) -> bool:
        """Initialize the assistant by loading the model"""
        return self.model.load_model()

    async def chat(self, message: str, conversation_id: Optional[str] = None,
                  user_id: str = "default") -> AssistantResponse:
        """Have a conversation with the assistant"""
        # Create conversation if needed
        if not conversation_id:
            conversation_id = self.conversation_manager.create_conversation(
                user_id, self.system_prompt
            )

        # Add user message
        user_msg = ConversationMessage(role='user', content=message)
        self.conversation_manager.add_message(conversation_id, user_msg)

        # Get conversation context
        context = self.conversation_manager.get_conversation_context(conversation_id)

        # Check cache
        cache_key = hashlib.md5(str(context).encode()).hexdigest()
        if cache_key in self.response_cache:
            cached_response = self.response_cache[cache_key]
            if datetime.now() - cached_response.metadata.get('timestamp', datetime.min) < self.cache_ttl:
                return cached_response

        # Generate response
        response = await self.model.generate_response(
            prompt=message,
            context=context[:-1]  # Exclude the current message
        )

        # Add assistant response to conversation
        assistant_msg = ConversationMessage(
            role='assistant',
            content=response.content,
            metadata={'confidence': response.confidence, 'tokens': response.tokens_used}
        )
        self.conversation_manager.add_message(conversation_id, assistant_msg)

        # Cache response
        response.metadata['timestamp'] = datetime.now()
        response.metadata['conversation_id'] = conversation_id
        self.response_cache[cache_key] = response

        # Clean old cache entries
        self._clean_cache()

        return response

    async def stream_chat(self, message: str, conversation_id: Optional[str] = None,
                         user_id: str = "default") -> AsyncGenerator[str, None]:
        """Stream conversation responses (simplified streaming)"""
        response = await self.chat(message, conversation_id, user_id)

        # Simulate streaming by yielding words
        words = response.content.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)  # Small delay for streaming effect

    def get_conversation_history(self, conversation_id: str) -> List[ConversationMessage]:
        """Get conversation history"""
        if conversation_id in self.conversation_manager.conversations:
            return self.conversation_manager.conversations[conversation_id].messages
        elif conversation_id in self.conversation_manager.conversation_cache:
            return self.conversation_manager.conversation_cache[conversation_id].messages
        return []

    def update_user_preferences(self, conversation_id: str, preferences: Dict[str, Any]):
        """Update user preferences"""
        self.conversation_manager.update_user_preferences(conversation_id, preferences)

    def get_capabilities(self) -> Dict[str, bool]:
        """Get assistant capabilities"""
        return self.capabilities.copy()

    def _clean_cache(self):
        """Clean expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, response in self.response_cache.items()
            if now - response.metadata.get('timestamp', datetime.min) > self.cache_ttl
        ]

        for key in expired_keys:
            del self.response_cache[key]

    async def shutdown(self):
        """Shutdown the assistant"""
        self.model.unload_model()
        self.conversation_manager._save_cache()

    def get_stats(self) -> Dict[str, Any]:
        """Get assistant statistics"""
        return {
            'active_conversations': len(self.conversation_manager.conversations),
            'cached_conversations': len(self.conversation_manager.conversation_cache),
            'cache_size': len(self.response_cache),
            'model_loaded': self.model.is_loaded,
            'model_type': self.model.model_type
        }


# Convenience functions
async def create_genai_assistant(model_path: str, model_type: str = "auto") -> GenAIAssistant:
    """Factory function to create GenAI assistant"""
    assistant = GenAIAssistant(model_path, model_type)
    if await assistant.initialize():
        return assistant
    else:
        raise RuntimeError("Failed to initialize GenAI assistant")

# Example usage
async def test_genai_assistant():
    """Test the GenAI assistant"""
    # This would need a local model file
    # assistant = await create_genai_assistant("./models/gpt2")

    # For testing without model:
    print("GenAI Assistant module loaded successfully")
    print("To use: await create_genai_assistant('/path/to/model')")

if __name__ == "__main__":
    asyncio.run(test_genai_assistant())
