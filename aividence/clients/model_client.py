"""ModelClient for handling interactions with language models."""
import logging
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from aividence.config import DEFAULT_TEMPERATURE, logger

class ModelClient:
    """
    A wrapper class to handle interactions with different language models.
    Supports OpenAI, Anthropic, and Ollama models.
    """
    
    def __init__(self, model_name: str, api_key: Optional[str] = None, 
                 base_url: Optional[str] = None, verbose: bool = False):
        """
        Initialize the model client.
        
        Args:
            model_name: Name of the model to use
            api_key: API key for the model service
            base_url: Base URL for the model service (used with Ollama models)
            verbose: Whether to enable verbose logging
        """
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.verbose = verbose
        self.chat_model = self._initialize_model()
        if self.verbose:
            logger.info(f"Chat model initialized: {model_name}")
    
    def _initialize_model(self) -> BaseChatModel:
        """Initialize the appropriate chat model based on the model name."""
        if self.verbose:
            logger.info(f"Initializing chat model: {self.model_name}")
            
        if "gpt" in self.model_name.lower() or "openai" in self.model_name.lower():
            from langchain_openai import ChatOpenAI
            if self.verbose:
                logger.info(f"Using OpenAI model: {self.model_name}")
            return ChatOpenAI(
                model_name=self.model_name,
                openai_api_key=self.api_key,
                temperature=DEFAULT_TEMPERATURE
            )
        elif "ollama" in self.model_name.lower():
            from langchain_community.chat_models import ChatOllama
            if self.verbose:
                logger.info(f"Using Ollama model: {self.model_name} with base URL: {self.base_url or 'http://localhost:11434'}")
            return ChatOllama(
                model=self.model_name,
                base_url=self.base_url or "http://localhost:11434"
            )
        elif "anthropic" in self.model_name.lower() or "claude" in self.model_name.lower():
            from langchain_anthropic import ChatAnthropic
            if self.verbose:
                logger.info(f"Using Anthropic model: {self.model_name}")
            return ChatAnthropic(
                model_name=self.model_name,
                anthropic_api_key=self.api_key,
                temperature=DEFAULT_TEMPERATURE
            )
        else:
            error_msg = f"Unsupported model: {self.model_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def run(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Run a chat completion.
        
        Args:
            prompt: The user prompt to send to the model
            system_prompt: Optional system prompt to set context
            
        Returns:
            The model's response as a string
        """
        if self.verbose:
            logger.info(f"Running chat completion with model: {self.model_name}")
            logger.debug(f"System prompt: {system_prompt}")
            logger.debug(f"User prompt: {prompt}")
            
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        if self.verbose:
            logger.info(f"Sending request to model with {len(messages)} messages")
            
        response = self.chat_model.invoke(messages)
        
        if self.verbose:
            logger.info(f"Received response from model")
            logger.debug(f"Response content length: {len(response.content)}")
            
        return response.content