import openai
import time
from typing import List, Dict, Optional, Any

MODELS = {
  'llama8b': 'meta/llama3-8b-instruct',
  'llama70b': 'meta/llama3-70b-instruct',
  'llama405b': 'meta/llama-3.1-405b-instruct',
  'mistral7b': 'mistralai/mistral-7b-instruct-v0.2',
  'gemma7b': 'google/gemma-7b',
  'nemotron340b': 'nvidia/nemotron-4-340b-instruct',
  'arctic': 'snowflake/arctic',
  'phi3mini': 'microsoft/phi-3-mini-128k-instruct',
  'deepseekv3': 'deepseek/deepseek-v3.2',
  'qwen3coder': 'qwen/qwen-3-coder',
  'kimi2.5': 'kimi/kimi-2.5'
}

class NvidiaNIMClient:
  def __init__(self, api_keys: Dict[str, List[str]], base_url: str = "https://integrate.api.nvidia.com/v1", use_aliases: bool = True):
    self.use_aliases = use_aliases
    self.clients = {}
    self.current_key_index = {}
    for alias_or_model, keys in api_keys.items():
      model = MODELS.get(alias_or_model, alias_or_model) if use_aliases else alias_or_model
      self.clients[model] = []
      for key in keys:
        self.clients[model].append(openai.OpenAI(base_url=base_url, api_key=key))
      self.current_key_index[model] = 0
    self.rate_limit_wait = 60 / 40 + 0.1

  def list_models(self):
    print("Available models (short name: full name):")
    for alias, full in MODELS.items():
      print(f"{alias}: {full}")

  def get_available_models(self) -> List[str]:
    if not self.clients:
      print("There are no initialized models/keys.")
      return []
    first_model = next(iter(self.clients))
    client = self.clients[first_model][0]
    try:
      response = client.models.list()
      models = [m.id for m in response.data]
      print(f"List of current models from API (on {first_model}):")
      for m in models:
        print(m)
      return models
    except Exception as e:
      print(f"Error fetching models list from API: {e}")
      return []

  def _get_client(self, model: str):
    clients = self.clients.get(model)
    if not clients:
      raise ValueError(f"Model {model} not found.")
    index = self.current_key_index[model]
    client = clients[index]
    self.current_key_index[model] = (index + 1) % len(clients)
    return client

  def chat_completion(self, model: str, messages: List[Dict[str, str]], max_tokens: int = 100, temperature: float = 0.7, top_p: float = 1.0, presence_penalty: float = 0.0, frequency_penalty: float = 0.0, stream: bool = False, **kwargs: Any) -> Dict:
    if self.use_aliases:
      model = MODELS.get(model, model)
    time.sleep(self.rate_limit_wait)
    client = self._get_client(model)
    try:
      response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        stream=stream,
        **kwargs
      )
      if stream:
        return response
      return response.model_dump()
    except openai.RateLimitError:
      time.sleep(60)
      return self.chat_completion(model, messages, max_tokens, temperature, top_p, presence_penalty, frequency_penalty, stream, **kwargs)
    except Exception as e:
      print(f"Error: {e}")
      return {"error": str(e)}

  def completion(self, model: str, prompt: str, max_tokens: int = 100, temperature: float = 0.7, top_p: float = 1.0, stream: bool = False, **kwargs: Any) -> Dict:
    if self.use_aliases:
      model = MODELS.get(model, model)
    time.sleep(self.rate_limit_wait)
    client = self._get_client(model)
    try:
      response = client.completions.create(
        model=model,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        stream=stream,
        **kwargs
      )
      if stream:
        return response
      return response.model_dump()
    except openai.RateLimitError:
      time.sleep(60)
      return self.completion(model, prompt, max_tokens, temperature, top_p, stream, **kwargs)
    except Exception as e:
      print(f"Error: {e}")
      return {"error": str(e)}