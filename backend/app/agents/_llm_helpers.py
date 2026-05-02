"""
LLM 调用通用封装：统一重试 / 超时 / 日志 / 降级
"""
import asyncio
import json
import time
from typing import Any, Callable, Optional, List, Dict
from loguru import logger


def estimate_token_count(text: str, model: str = "gpt-4") -> int:
    """
    使用 tiktoken 估算文本的 token 数量。
    如果 tiktoken 不可用或网络下载失败，则按字符数粗略估算（1 token ≈ 4 个中文字符或 0.75 个英文单词）。
    """
    try:
        import tiktoken
        # 优先使用 gpt-4 编码器，失败则使用 cl100k_base
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # 粗略估算：按字符数（涵盖 ImportError、网络下载失败等所有异常）
        return len(text) // 4 + 1


def truncate_messages_by_token(
    messages: List[Dict[str, str]],
    max_tokens: int,
    model: str = "gpt-4",
) -> List[Dict[str, str]]:
    """
    按 token 预算截断消息列表，保留最近的消息。
    策略：从旧到新截断，直到总 token < max_tokens。
    始终保留最后一条消息（用户最新消息）。

    Args:
        messages: 消息列表，每条含 role 和 content
        max_tokens: 最大允许 token 数
        model: 模型名称，用于选择 tiktoken 编码器

    Returns:
        截断后的消息列表
    """
    if not messages:
        return messages

    # 单条消息超长时，对 content 进行截断（保留最近部分）
    def _truncate_single(content: str, budget: int) -> str:
        try:
            import tiktoken
            try:
                enc = tiktoken.encoding_for_model(model)
            except KeyError:
                enc = tiktoken.get_encoding("cl100k_base")
            tokens = enc.encode(content)
            if len(tokens) <= budget:
                return content
            # 保留尾部 token（最近的信息通常更重要）
            truncated = enc.decode(tokens[-budget:])
            return truncated
        except Exception:
            # tiktoken 不可用时按字符粗略截断
            return content[-budget * 4:]

    total_tokens = 0
    # 逆序遍历，从最新的消息开始累加 token
    keep_count = 0
    for msg in reversed(messages):
        content = msg.get("content", "")
        msg_tokens = estimate_token_count(content, model)
        if total_tokens + msg_tokens <= max_tokens:
            total_tokens += msg_tokens
            keep_count += 1
        else:
            break

    if keep_count == 0:
        # 连最后一条都超预算，截断最后一条的 content
        last = messages[-1]
        content = last.get("content", "")
        truncated_content = _truncate_single(content, max_tokens)
        return [{**last, "content": truncated_content}]

    return messages[-keep_count:]


async def invoke_with_retry(
    chain,
    inputs: dict,
    fallback_fn: Optional[Callable] = None,
    max_retries: int = 2,
    timeout: float = 30.0,
    parse_json: bool = False,
) -> Any:
    """
    带重试/超时/日志/降级的 LLM 链调用。

    Args:
        chain: LangChain Runnable（prompt | llm | parser）
        inputs: 链输入字典
        fallback_fn: API 失败时的降级函数（无参数，返回默认值）
        max_retries: 最大重试次数
        timeout: 单次调用超时（秒）
        parse_json: 是否将输出字符串解析为 JSON

    Returns:
        LLM 输出或 fallback_fn() 的返回值
    """
    # 估算输入 token 数（基于 inputs 字典的 JSON 序列化）
    try:
        inputs_text = json.dumps(inputs, ensure_ascii=False, default=str)
        estimated_tokens = estimate_token_count(inputs_text)
    except Exception:
        estimated_tokens = 0

    if estimated_tokens > 10000:
        logger.warning(f"[LLMHelper] 上下文接近上限 (estimated_tokens={estimated_tokens})")
    else:
        logger.info(f"[LLMHelper] 预估输入 token: {estimated_tokens}")

    last_error = None
    for attempt in range(max_retries + 1):
        t0 = time.perf_counter()
        try:
            result = await asyncio.wait_for(chain.ainvoke(inputs), timeout=timeout)
            elapsed = time.perf_counter() - t0
            logger.info(f"[LLMHelper] 调用成功 (attempt={attempt+1}, elapsed={elapsed:.2f}s, estimated_tokens={estimated_tokens})")
            logger.info(f"result: {result}")
            if parse_json and isinstance(result, str):
                # 去除 markdown 代码块
                cleaned = result.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                try:
                    return json.loads(cleaned.strip())
                except json.JSONDecodeError as json_err:
                    elapsed = time.perf_counter() - t0
                    logger.warning(
                        f"[LLMHelper] JSON 解析失败，输出可能被截断 "
                        f"(attempt={attempt+1}, elapsed={elapsed:.2f}s, output_len={len(result)}, err={json_err})"
                    )
                    # JSON 截断不会因重试而改善，直接跳出循环进 fallback
                    last_error = json_err
                    break
            return result

        except asyncio.TimeoutError:
            elapsed = time.perf_counter() - t0
            logger.warning(f"[LLMHelper] 超时 (attempt={attempt+1}, elapsed={elapsed:.2f}s)")
            last_error = TimeoutError(f"LLM call timed out after {timeout}s")
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.warning(f"[LLMHelper] 调用失败 (attempt={attempt+1}, elapsed={elapsed:.2f}s): {e}")
            last_error = e

        if attempt < max_retries:
            await asyncio.sleep(1.0 * (attempt + 1))

    if fallback_fn is not None:
        logger.warning(f"[LLMHelper] 所有重试失败，使用降级方案: {last_error}")
        return fallback_fn()

    raise last_error
