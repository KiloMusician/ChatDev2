import subprocess
import json
import yaml
import time
import logging
from easydict import EasyDict
import openai
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))
import os
from abc import ABC, abstractmethod
import tiktoken
from typing import Any, Dict
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential
)
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
if 'BASE_URL' in os.environ:
    BASE_URL = os.environ['BASE_URL']
else:
    BASE_URL = None

def getFilesFromType(sourceDir, filetype):
    files = []
    for root, directories, filenames in os.walk(sourceDir):
        for filename in filenames:
            if filename.endswith(filetype):
                files.append(os.path.join(root, filename))
    return files

def cmd(command: str):
    print(">> {}".format(command))
    text = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE).stdout
    return text

def get_easyDict_from_filepath(path: str):
    # print(path)
    if path.endswith('.json'):
        with open(path, 'r', encoding="utf-8") as file:
            config_map = json.load(file, strict=False)
            config_easydict = EasyDict(config_map)
            return config_easydict
    if path.endswith('.yaml'):
        file_data = open(path, 'r', encoding="utf-8").read()
        config_map = yaml.load(file_data, Loader=yaml.FullLoader)
        config_easydict = EasyDict(config_map)
        return config_easydict
    return None


def calc_max_token(messages, model):
    string = "\n".join([message["content"] for message in messages])
    encoding = tiktoken.encoding_for_model(model)
    num_prompt_tokens = len(encoding.encode(string))
    gap_between_send_receive = 50
    num_prompt_tokens += gap_between_send_receive

    num_max_token_map = {
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
        "gpt-3.5-turbo-0613": 4096,
        "gpt-3.5-turbo-16k-0613": 16384,
        "gpt-4": 8192,
        "gpt-4-0613": 8192,
        "gpt-4-32k": 32768,
        "gpt-4o": 4096, #100000
        "gpt-4o-mini": 16384, #100000
    }
    num_max_token = num_max_token_map[model]
    num_max_completion_tokens = num_max_token - num_prompt_tokens
    return num_max_completion_tokens


class ModelBackend(ABC):
    r"""Base class for different model backends.
    May be OpenAI API, a local LLM, a stub for unit tests, etc."""

    @abstractmethod
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        r"""Runs the query to the backend model.

        Raises:
            RuntimeError: if the return value from OpenAI API
            is not a dict that is expected.

        Returns:
            Dict[str, Any]: All backends must return a dict in OpenAI format.
        """
        pass

class OpenAIModel(ModelBackend):
    r"""OpenAI API in a unified ModelBackend interface."""

    def __init__(self, model_type, model_config_dict: Dict[str, Any] = None) -> None:
        super().__init__()
        self.model_type = model_type
        self.model_config_dict = model_config_dict
        if self.model_config_dict is None:
            self.model_config_dict = {"temperature": 0.2,
                                "top_p": 1.0,
                                "n": 1,
                                "stream": False,
                                "frequency_penalty": 0.0,
                                "presence_penalty": 0.0,
                                "logit_bias": {},
                                }
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    @retry(wait=wait_exponential(min=5, max=60), stop=stop_after_attempt(5))
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        # Extract messages from args or kwargs
        if 'messages' in kwargs:
            messages = kwargs['messages']
        elif args and len(args) > 0:
            messages = args[0]
        else:
            raise ValueError("No messages provided to OpenAI API")
            
        # Initialize OpenAI client with only valid parameters
        try:
            client_kwargs = {}
            if OPENAI_API_KEY:
                client_kwargs['api_key'] = OPENAI_API_KEY
            if BASE_URL:
                client_kwargs['base_url'] = BASE_URL
            
            client = openai.OpenAI(**client_kwargs)
        except Exception as e:
            print(f"Error initializing OpenAI client in utils.py: {e}")
            # Fallback with minimal client
            client = openai.OpenAI(api_key=OPENAI_API_KEY or "")

        try:
            string = "\n".join([message["content"] for message in messages])
            encoding = tiktoken.encoding_for_model(self.model_type)
            num_prompt_tokens = len(encoding.encode(string))
            gap_between_send_receive = 15 * len(messages)
            num_prompt_tokens += gap_between_send_receive

            num_max_token_map = {
                "gpt-3.5-turbo": 4096,
                "gpt-3.5-turbo-16k": 16384,
                "gpt-3.5-turbo-0613": 4096,
                "gpt-3.5-turbo-16k-0613": 16384,
                "gpt-4": 8192,
                "gpt-4-0613": 8192,
                "gpt-4-32k": 32768,
                "gpt-4o": 4096, #100000
                "gpt-4o-mini": 16384, #100000
            }
            
            num_max_token = num_max_token_map[self.model_type]
            num_max_completion_tokens = num_max_token - num_prompt_tokens
            self.model_config_dict['max_tokens'] = num_max_completion_tokens
            
            response = client.chat.completions.create(
                messages=messages,
                model="gpt-3.5-turbo-16k",
                temperature=0.2,
                top_p=1.0,
                n=1,
                stream=False,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                logit_bias={},
                max_tokens=num_max_completion_tokens
            )
            
            # Convert response to dict format
            response_dict = {
                "choices": [
                    {
                        "message": {
                            "content": choice.message.content,
                            "role": choice.message.role
                        },
                        "finish_reason": choice.finish_reason
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                } if response.usage else {}
            }
            
            if response.usage:
                log_and_print_online(
                    "InstructionStar generation:\n**[OpenAI_Usage_Info Receive]**\nprompt_tokens: {}\ncompletion_tokens: {}\ntotal_tokens: {}\n".format(
                        response.usage.prompt_tokens, response.usage.completion_tokens,
                        response.usage.total_tokens))
                self.prompt_tokens += response.usage.prompt_tokens
                self.completion_tokens += response.usage.completion_tokens
                self.total_tokens += response.usage.total_tokens
            
            return response_dict
        except Exception as e:
            log_and_print_online(f"Error in OpenAI API call: {e}")
            # Return fallback response
            return {
                "choices": [
                    {
                        "message": {
                            "content": "API error occurred",
                            "role": "assistant"
                        },
                        "finish_reason": "error"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }

    
def now():
    return time.strftime("%Y%m%d%H%M%S", time.localtime())

def log_and_print_online(content=None):
    if  content is not None:
        print(content)
        logging.info(content)
