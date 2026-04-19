"""全局视角裁决官 - 判定推理是否成立"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import get_settings
from app.models.case import Case, Clue, Inference
from app.agents._llm_helpers import invoke_with_retry
from app.agents.prompts.oracle_prompts import (
    ORACLE_SYSTEM,
    VERIFY_INFERENCE_USER,
    VERIFY_ACCUSATION_USER,
)


def _format_case_truth(case: Case) -> str:
    """把 case 序列化为裁决官可读的真相 block"""
    lines = [
        f"victim: {case.victim_name}",
        f"cause_of_death: {case.cause_of_death}",
        f"murder_method: {case.murder_method}",
        f"true_murderer_id: {case.true_murderer_id}",
        "suspects:",
    ]
    for s in case.suspects:
        lines.append(f"  - id={s.id} name={s.name} guilty={s.is_guilty} motive={s.motive}")
    lines.append("clues:")
    for c in case.clues:
        lines.append(
            f"  - id={c.id} type={c.clue_type} red_herring={c.is_red_herring} desc={c.description}"
        )
    return "\n".join(lines)


def _format_clues_block(clues: List[Clue]) -> str:
    return "\n".join(
        [f"  - id={c.id} label={c.user_label or c.description[:30]}" for c in clues]
    )


class OracleAgent:
    """裁决官：低温度、严格事实对齐"""

    def __init__(self, temperature: float = 0.2) -> None:
        settings = get_settings()
        self.temperature = temperature
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=temperature,
        )
        logger.info(f"[OracleAgent] 初始化裁决官 (temperature={temperature})")

    def _build_chain(self, user_template: str):
        """构建 system + user 的 LangChain 链，输出原始字符串供 parse_json 处理"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", ORACLE_SYSTEM),
            ("human", user_template),
        ])
        return prompt | self.llm | StrOutputParser()

    async def verify_inference(
        self,
        case: Case,
        clues: List[Clue],
        conclusion: str,
    ) -> Dict[str, Any]:
        logger.info(
            f"[OracleAgent] verify_inference 启动 clue_count={len(clues)} conclusion_len={len(conclusion)}"
        )
        chain = self._build_chain(VERIFY_INFERENCE_USER)
        result = await invoke_with_retry(
            chain=chain,
            inputs={
                "case_truth": _format_case_truth(case),
                "clues_block": _format_clues_block(clues),
                "conclusion": conclusion,
            },
            fallback_fn=lambda: {
                "verdict": "partial",
                "score": 0.5,
                "explanation": "裁决官暂时不在，请稍后再试。",
                "missing_links": [],
                "misused_clues": [],
            },
            parse_json=True,
        )
        logger.info(f"[OracleAgent] verify_inference 完成 verdict={result.get('verdict')}")
        return result

    async def verify_accusation(
        self,
        case: Case,
        suspect_id: str,
        reasoning_records: List[Inference],
    ) -> Dict[str, Any]:
        logger.info(
            f"[OracleAgent] verify_accusation 启动 suspect_id={suspect_id} record_count={len(reasoning_records)}"
        )
        suspect = next((s for s in case.suspects if s.id == suspect_id), None)
        records_block = "\n".join(
            [
                f"  - id={r.id} verdict={r.verification_result} content={r.content[:80]}"
                for r in reasoning_records
            ]
        ) or "  （无）"

        chain = self._build_chain(VERIFY_ACCUSATION_USER)
        result = await invoke_with_retry(
            chain=chain,
            inputs={
                "case_truth": _format_case_truth(case),
                "suspect_name": suspect.name if suspect else "未知",
                "suspect_id": suspect_id,
                "true_murderer_id": case.true_murderer_id or "",
                "records_block": records_block,
            },
            fallback_fn=lambda: {
                "is_correct": (suspect_id == case.true_murderer_id),
                "score": 0.5,
                "verdict_explanation": "裁决官暂时不在，仅按真凶 id 给出降级判定。",
                "key_evidence_used": [],
                "missing_critical_evidence": [],
            },
            parse_json=True,
        )
        logger.info(f"[OracleAgent] verify_accusation 完成 is_correct={result.get('is_correct')}")
        return result


_oracle_singleton: Optional[OracleAgent] = None


def get_oracle_agent() -> OracleAgent:
    global _oracle_singleton
    if _oracle_singleton is None:
        _oracle_singleton = OracleAgent()
    return _oracle_singleton
