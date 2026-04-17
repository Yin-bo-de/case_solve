"""
LLM 调用通用封装：统一重试 / 超时 / 日志 / 降级
"""
import asyncio
import json
import time
from typing import Any, Callable, Optional
from loguru import logger


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
    last_error = None
    for attempt in range(max_retries + 1):
        t0 = time.perf_counter()
        try:
            result = await asyncio.wait_for(chain.ainvoke(inputs), timeout=timeout)
            elapsed = time.perf_counter() - t0
            logger.info(f"[LLMHelper] 调用成功 (attempt={attempt+1}, elapsed={elapsed:.2f}s)")

            if parse_json and isinstance(result, str):
                # 去除 markdown 代码块
                cleaned = result.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                return json.loads(cleaned.strip())
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
