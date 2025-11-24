# backend.py 的完整修改版本

import openai
from openai import OpenAI
import time
import os
import httpx
import json
import tiktoken

# 设置DeepSeek API密钥（从环境变量获取）。为安全起见，不要在代码中硬编码密钥。
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def count_tokens(messages, model="deepseek-chat"):
    """Calculate the number of tokens in messages"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # DeepSeek使用与GPT相同的编码
        encoding = tiktoken.get_encoding("cl100k_base")
    
    num_tokens = 0
    for message in messages:
        if isinstance(message, dict):
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                if isinstance(value, str):
                    num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += -1
        elif isinstance(message, str):
            num_tokens += len(encoding.encode(message))
    
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


def adjust_max_tokens(messages, model='deepseek-chat', desired_max_tokens=4096):
    """Intelligently adjust max_tokens to avoid exceeding model limits"""
    
    # Context length limits for different models
    model_limits = {
        'deepseek-chat': 32768,  # DeepSeek Chat的上下文窗口大小
        'deepseek-coder': 32768,  # DeepSeek Coder的上下文窗口大小
        'gpt-3.5-turbo': 16385,  # 保留原有配置
        'gpt-4': 16385,
    }
    
    # Get the maximum context length for the model
    max_context_length = model_limits.get(model, 32768)  # 默认使用DeepSeek的上下文长度
    
    # Calculate input message token count
    input_tokens = count_tokens(messages, model)
    
    # Calculate available tokens, leaving some margin
    available_tokens = max_context_length - input_tokens - 100  # Leave 100 tokens margin
    
    # Adjust max_tokens
    if available_tokens <= 0:
        print(f"⚠️ Warning: Input too long ({input_tokens} tokens), truncating...")
        adjusted_max_tokens = min(512, max_context_length // 4)
        truncated_messages = truncate_messages(messages, max_context_length - adjusted_max_tokens - 100)
        return truncated_messages, adjusted_max_tokens
    else:
        adjusted_max_tokens = min(desired_max_tokens, available_tokens)
        print(f"📊 Token info: Input={input_tokens}, Available={available_tokens}, Using={adjusted_max_tokens}")
        return messages, max(adjusted_max_tokens, 256)


def truncate_messages(messages, max_tokens):
    """Truncate message history to fit token limit"""
    if not messages:
        return messages
    
    truncated = []
    
    # If first message is system message, keep it
    if messages and isinstance(messages[0], dict) and messages[0].get('role') == 'system':
        truncated.append(messages[0])
        remaining_messages = messages[1:]
    else:
        remaining_messages = messages
    
    current_tokens = count_tokens(truncated)
    for message in reversed(remaining_messages):
        message_tokens = count_tokens([message])
        if current_tokens + message_tokens <= max_tokens:
            truncated.insert(-1 if truncated and truncated[0].get('role') == 'system' else 0, message)
            current_tokens += message_tokens
        else:
            break
    
    print(f"📝 Truncated messages: {len(messages)} -> {len(truncated)} messages")
    return truncated


def call_chatgpt(prompt, model='deepseek-chat', stop=None, temperature=0., top_p=0.95,
                max_tokens=128, echo=False, majority_at=None):
    # Ensure API key is available
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is not set. Please set the environment variable DEEPSEEK_API_KEY before running.")

    # 使用DeepSeek API
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1"
    )
    
    # 智能调整token计数
    adjusted_prompt, adjusted_max_tokens = adjust_max_tokens(prompt, model, max_tokens)
    
    num_completions = majority_at if majority_at is not None else 1
    num_completions_batch_size = 5  # DeepSeek可能限制批量大小
    
    completions = []
    
    for i in range(20 * (num_completions // num_completions_batch_size + 1)):
        try:
            requested_completions = min(num_completions_batch_size, num_completions - len(completions))
            
            # 构建请求参数
            request_params = {
                "model": model,
                "messages": adjusted_prompt,
                "max_tokens": adjusted_max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stream": False
            }
            
            # 只有需要多个completion时才设置n
            if requested_completions > 1:
                request_params["n"] = requested_completions
            
            response = client.chat.completions.create(**request_params)
            
            # 提取响应内容
            if hasattr(response, 'choices'):
                completions.extend([choice.message.content for choice in response.choices])
            else:
                # 处理单个响应的情况
                completions.append(response.choices[0].message.content)
            
            if len(completions) >= num_completions:
                return completions[:num_completions]
            
        except openai.BadRequestError as e:
            error_message = str(e)
            if "context_length_exceeded" in error_message or "maximum context length" in error_message:
                print(f"🔄 Context length exceeded, reducing max_tokens from {adjusted_max_tokens} to {adjusted_max_tokens // 2}")
                adjusted_max_tokens = max(adjusted_max_tokens // 2, 256)
                adjusted_prompt, adjusted_max_tokens = adjust_max_tokens(
                    adjusted_prompt, model, adjusted_max_tokens
                )
                continue
            else:
                print(f"❌ API Error: {error_message}")
                raise e
        
        except openai.RateLimitError as e:
            wait_time = min((i + 1) * 5, 60)  # 指数退避，最多等待60秒
            print(f"⏳ Rate limit hit, waiting {wait_time} seconds...")
            time.sleep(wait_time)
        
        except openai.APIConnectionError as e:
            print(f"🔌 Connection error, retrying... {e}")
            time.sleep(5)
        
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            if i < 3:
                adjusted_max_tokens = max(adjusted_max_tokens // 2, 256)
                print(f"🔄 Retrying with reduced max_tokens: {adjusted_max_tokens}")
                time.sleep(5)
                continue
            else:
                raise e
    
    raise RuntimeError('Failed to call DeepSeek API after multiple attempts')