"""场景 NPC - 引导玩家自然语言探索"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import get_settings
from app.models.case import Case, Scene
from app.agents._llm_helpers import invoke_with_retry
from app.agents.prompts.scene_prompts import SCENE_SYSTEM, SCENE_SEARCH_USER


def _format_scene(scene: Scene) -> str:
    lines = [f"name: {scene.name}", f"desc: {scene.description}", "objects:"]
    for o in scene.objects:
        hidden = "yes" if o.hidden_clue_ids else "no"
        lines.append(f"  - id={o.id} name={o.name} hidden_clue={hidden} desc={o.description}")
    return "\n".join(lines)


def _format_history(history: List[Dict[str, str]], limit: int = 6) -> str:
    recent = history[-limit:]
    return "\n".join([f"{m['role']}: {m['content']}" for m in recent]) or "（无）"


def _format_clues_for_scene(case: Case, scene: Scene) -> str:
    """仅暴露与该场景对象相关的线索元数据，避免剧透其他场景信息"""
    related_ids = {cid for o in scene.objects for cid in o.hidden_clue_ids}
    related = [c for c in case.clues if c.id in related_ids]
    return "\n".join([f"  - id={c.id} type={c.clue_type} desc={c.description}" for c in related]) or "（无）"


class SceneAgent:
    def __init__(self, temperature: float = 0.5) -> None:
        settings = get_settings()
        self.temperature = temperature
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=temperature,
        )
        logger.info(f"[SceneAgent] 初始化场景NPC Agent (temperature={temperature})")

    def _build_chain(self):
        """构建场景搜索 LangChain 链"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", SCENE_SYSTEM),
            ("human", SCENE_SEARCH_USER),
        ])
        return prompt | self.llm | StrOutputParser()

    async def search(
        self,
        scene: Scene,
        case: Case,
        query: str,
        history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        logger.info(f"[SceneAgent] search scene_id={scene.id} query_len={len(query)}")
        chain = self._build_chain()
        result = await invoke_with_retry(
            chain=chain,
            inputs={
                "scene_block": _format_scene(scene),
                "clue_block": _format_clues_for_scene(case, scene),
                "history_block": _format_history(history),
                "query": query,
            },
            fallback_fn=lambda: {
                "narrative": "（场景陷入寂静，似乎暂时听不到任何回应）",
                "matched_object_ids": [],
                "clue_candidates": [],
            },
            parse_json=True,
        )
        logger.info(f"[SceneAgent] search 完成 candidates={len(result.get('clue_candidates', []))}")
        return result


_scene_singleton: Optional[SceneAgent] = None


def get_scene_agent() -> SceneAgent:
    global _scene_singleton
    if _scene_singleton is None:
        _scene_singleton = SceneAgent()
    return _scene_singleton
