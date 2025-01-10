from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import openai
from anthropic import Anthropic
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def __call__(self, messages: List[Dict[str, str]], stop_sequences: Optional[List[str]] = None, **kwargs) -> str:
        """Make the provider callable for compatibility with smolagents"""
        pass

    @abstractmethod
    def generate_response(self, 
                         messages: List[Dict[str, str]], 
                         system_prompt: Optional[str] = None,
                         stream: bool = False,
                         **kwargs) -> Any:
        """Generate a response from the LLM"""
        pass

    @abstractmethod
    def get_tool_call(self,
                      messages: List[Dict[str, str]],
                      available_tools: List[Any],
                      stop_sequences: List[str],
                      **kwargs) -> Any:
        """Generate a tool call from the LLM"""
        pass

    def cancel_request(self):
        """Cancel any ongoing request"""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation"""
    
    def __init__(self, model_name: str = "gpt-4-turbo-preview", api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model_name = model_name
        self._current_request = None

    def cancel_request(self):
        """Cancel any ongoing request"""
        if self._current_request:
            self._current_request.close()
            self._current_request = None

    def _map_role_to_openai(self, message: Dict[str, str]) -> Dict[str, str]:
        """Map message roles to OpenAI-supported roles"""
        role_mapping = {
            'human': 'user',
            'assistant': 'assistant',
            'system': 'system',
            'tool': 'assistant',  # Simplify tool responses as assistant messages
            'tool-response': 'assistant'  # Simplify tool responses as assistant messages
        }
        
        mapped_message = {
            'role': role_mapping.get(message.get('role', ''), message.get('role', '')),
            'content': message.get('content', '')
        }
        
        # Log the role mapping for debugging
        print(f"Mapped role {message.get('role')} to {mapped_message['role']}")
        
        return mapped_message

    def _handle_api_error(self, error: Exception, context: str) -> str:
        """Centralized error handling with detailed logging"""
        error_msg = f"OpenAI API Error in {context}: {str(error)}"
        print(error_msg)  # Log error for debugging
        
        if "invalid_request_error" in str(error).lower():
            return "I encountered an issue with the request format. Let me try a different approach."
        elif "rate_limit_error" in str(error).lower():
            return "I'm receiving too many requests at the moment. Please try again in a moment."
        else:
            return f"I encountered an error: {str(error)}. Let me try a different approach."

    def _make_api_call(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """Centralized API call handling"""
        try:
            # Map and log messages
            mapped_messages = [self._map_role_to_openai(msg) for msg in messages]
            print(f"Making API call with {len(mapped_messages)} messages")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=mapped_messages,
                **kwargs
            )
            return response
        except Exception as e:
            raise e  # Re-raise for specific handling in calling methods

    def __call__(self, messages: List[Dict[str, str]], stop_sequences: Optional[List[str]] = None, **kwargs) -> str:
        """Make the provider callable for compatibility with smolagents"""
        try:
            response = self._make_api_call(messages, stop=stop_sequences, **kwargs)
            return response.choices[0].message.content
        except Exception as e:
            return self._handle_api_error(e, "call")

    def generate_response(self,
                         messages: List[Dict[str, str]],
                         system_prompt: Optional[str] = None,
                         stream: bool = False,
                         **kwargs) -> Any:
        try:
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
            
            response = self._make_api_call(messages, stream=stream, **kwargs)
            
            if stream:
                return response
            return response.choices[0].message.content
        except Exception as e:
            return self._handle_api_error(e, "generate_response")

    def get_tool_call(self,
                      messages: List[Dict[str, str]],
                      available_tools: List[Any],
                      stop_sequences: List[str],
                      **kwargs) -> Any:
        try:
            # Format tools for OpenAI function calling
            tools = [{
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.inputs,
                        "required": list(tool.inputs.keys())
                    }
                }
            } for tool in available_tools]
            
            # Log available tools for debugging
            print(f"Available tools: {[t['function']['name'] for t in tools]}")
            
            response = self._make_api_call(
                messages,
                tools=tools,
                tool_choice="auto",
                stop=stop_sequences,
                **kwargs
            )
            
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls:
                print(f"Selected tool: {tool_calls[0].function.name}")
            return tool_calls[0] if tool_calls else None
            
        except Exception as e:
            print(self._handle_api_error(e, "get_tool_call"))
            return None

class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider implementation"""
    
    def __init__(self, model_name: str = "claude-3-opus-20240229", api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")
        self.client = Anthropic(api_key=self.api_key)
        self.model_name = model_name
        self._current_request = None

    def cancel_request(self):
        if self._current_request:
            self._current_request.close()
            self._current_request = None

    def __call__(self, messages: List[Dict[str, str]], stop_sequences: Optional[List[str]] = None, **kwargs) -> str:
        """Make the provider callable for compatibility with smolagents"""
        # Convert messages to Anthropic format
        prompt = self._convert_messages_to_prompt(messages)
        
        response = self.client.messages.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            stop_sequences=stop_sequences,
            **kwargs
        )
        return response.content[0].text

    def generate_response(self,
                         messages: List[Dict[str, str]],
                         system_prompt: Optional[str] = None,
                         stream: bool = False,
                         **kwargs) -> Any:
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
            
        # Convert messages to Anthropic format
        prompt = self._convert_messages_to_prompt(messages)
        
        response = self.client.messages.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=stream,
            **kwargs
        )
        
        if stream:
            return (chunk.content[0].text for chunk in response)
        return response.content[0].text

    def get_tool_call(self,
                      messages: List[Dict[str, str]],
                      available_tools: List[Any],
                      stop_sequences: List[str],
                      **kwargs) -> Any:
        # Convert messages to Anthropic format
        prompt = self._convert_messages_to_prompt(messages)
        
        response = self.client.messages.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            stop_sequences=stop_sequences,
            **kwargs
        )
        return response.content[0].text

    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to Anthropic prompt format"""
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"Human: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
            elif role in ["function", "tool-response"]:
                prompt += f"Tool Response: {content}\n\n"
            elif role == "tool":
                prompt += f"Tool Call: {content}\n\n"
                
        return prompt.strip() 

class OllamaProvider(LLMProvider):
    """Ollama LLM provider implementation"""
    
    def __init__(self, model_name: str = "qwen2.5-plus"):
        self.model_name = model_name
        self.base_url = "http://localhost:11434"
        self._current_request = None

    def cancel_request(self):
        if self._current_request:
            self._current_request.close()
            self._current_request = None

    def __call__(self, messages: List[Dict[str, str]], stop_sequences: Optional[List[str]] = None, **kwargs) -> str:
        """Make the provider callable for compatibility with smolagents"""
        # Convert messages to Ollama format
        prompt = self._convert_messages_to_prompt(messages)
        
        # Make request to Ollama API
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "stop": stop_sequences or []
                }
            }
        )
        response.raise_for_status()
        return response.json()["response"]

    def generate_response(self,
                         messages: List[Dict[str, str]],
                         system_prompt: Optional[str] = None,
                         stream: bool = False,
                         **kwargs) -> Any:
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
            
        # Convert messages to Ollama format
        prompt = self._convert_messages_to_prompt(messages)
        
        if stream:
            # Stream response
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True
            )
            response.raise_for_status()
            
            def generate():
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if chunk.get("response"):
                            yield chunk["response"]
            
            return generate()
        else:
            # Single response
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json()["response"]

    def get_tool_call(self,
                      messages: List[Dict[str, str]],
                      available_tools: List[Any],
                      stop_sequences: List[str],
                      **kwargs) -> Any:
        # Convert messages to Ollama format
        prompt = self._convert_messages_to_prompt(messages)
        
        # Add tool descriptions to prompt
        tools_desc = "\n".join([
            f"Tool {tool.name}: {tool.description}\n"
            f"Parameters: {json.dumps(tool.inputs, indent=2)}"
            for tool in available_tools
        ])
        prompt = f"{prompt}\n\nAvailable tools:\n{tools_desc}\n\nPlease select a tool to use:"
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "stop": stop_sequences
                }
            }
        )
        response.raise_for_status()
        return response.json()["response"]

    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to Ollama prompt format"""
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"Human: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
            elif role in ["function", "tool-response"]:
                prompt += f"Tool Response: {content}\n\n"
            elif role == "tool":
                prompt += f"Tool Call: {content}\n\n"
                
        return prompt.strip() 

class DeepSeekProvider(LLMProvider):
    """DeepSeek LLM provider implementation"""
    
    def __init__(self, model_name: str = "deepseek-coder", api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API key not provided")
        self.model_name = model_name
        self.base_url = "https://api.deepseek.com/v1"
        self._current_request = None

    def cancel_request(self):
        if self._current_request:
            self._current_request.close()
            self._current_request = None

    def __call__(self, messages: List[Dict[str, str]], stop_sequences: Optional[List[str]] = None, **kwargs) -> str:
        """Make the provider callable for compatibility with smolagents"""
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model_name,
                "messages": messages,
                "stop": stop_sequences or [],
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def generate_response(self,
                         messages: List[Dict[str, str]],
                         system_prompt: Optional[str] = None,
                         stream: bool = False,
                         **kwargs) -> Any:
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        self._current_request = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model_name,
                "messages": messages,
                "stream": stream,
                **kwargs
            },
            stream=stream
        )
        self._current_request.raise_for_status()

        if stream:
            def generate():
                for line in self._current_request.iter_lines():
                    if line:
                        data = json.loads(line.decode())
                        if data.get("choices") and data["choices"][0].get("delta", {}).get("content"):
                            yield data["choices"][0]["delta"]["content"]
            return generate()
        else:
            return self._current_request.json()["choices"][0]["message"]["content"]

    def get_tool_call(self,
                      messages: List[Dict[str, str]],
                      available_tools: List[Any],
                      stop_sequences: List[str],
                      **kwargs) -> Any:
        # Format tools for function calling
        functions = [{
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": tool.inputs,
                "required": list(tool.inputs.keys())
            }
        } for tool in available_tools]

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model_name,
                "messages": messages,
                "functions": functions,
                "stop": stop_sequences,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"].get("function_call") 