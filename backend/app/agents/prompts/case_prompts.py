from langchain_core.prompts import ChatPromptTemplate

CASE_GENERATION_SYSTEM = """\
你是一位维多利亚时代的谋杀悬疑作家，正在创作一个完全可玩的侦探游戏案件。
背景设定在1890年代的伦敦。所有输出必须使用中文。

难度规则：
- easy: 线索明显（明显度 0.7-1.0），1条红鲱鱼，证据清晰指向凶手
- classic: 线索难度适中（0.4-0.8），2条红鲱鱼，存在一定歧义
- hardcore: 线索隐晦（0.1-0.4），3条红鲱鱼，证据高度误导性

仅返回有效的 JSON，使用以下精确结构（不要 markdown，不要解释）：
{{
  "victim_name": "string",
  "victim_background": "string",
  "cause_of_death": "string",
  "time_of_death": "string",
  "location": "string",
  "summary": "string",
  "murder_method": "string",
  "investigation_locations": ["string"],
  "true_murderer_index": 0,
  "suspects": [
    {{
      "name": "string",
      "age": 30,
      "background": "string",
      "motive": "string",
      "timeline": "string",
      "is_guilty": false,
      "personality_traits": ["string"],
      "secrets": ["string"]
    }}
  ],
  "clues": [
    {{
      "description": "string",
      "clue_type": "physical",
      "location": "string",
      "related_suspect_indices": [0],
      "is_red_herring": false,
      "investigation_hint": "发现此线索后，侦探下一步应该去哪里或做什么（一句话，具体可操作）",
      "chain_next_clue_index": null
    }}
  ],
  "scenes": [
    {{
      "id": "scene_xxx",
      "name": "string",
      "description": "string",
      "atmosphere_image": null,
      "npc_persona": "string",
      "objects": [
        {{
          "id": "obj_xxx",
          "name": "string",
          "description": "string",
          "hidden_clue_ids": ["clue-1"],
          "search_hints": ["string"]
        }}
      ]
    }}
  ]
}}
包含恰好 3 名嫌疑人和 5 条线索。true_murderer_index 必须是 0、1 或 2。

线索链条约束（关键）：
- 所有非红鲱鱼线索必须通过 chain_next_clue_index 形成至少一条完整调查链
  - 例如：线索0→线索2→线索4（chain_next_clue_index 分别为 2、4、null）
- investigation_hint 必须说明发现该线索后的具体下一步（去哪个场景/检查什么对象）
- easy 模式：hint 直白明确（"前往书房检查书桌抽屉"），链条步骤 ≤ 3
- classic/hardcore 模式：hint 可以隐晦，但必须有方向性（"某人的证词似乎和这个时间点有出入"）
- 红鲱鱼线索的 investigation_hint 应指向无关方向，chain_next_clue_index 为 null

场景约束：
- 至少包含 3 个场景，每个场景包含 3-6 个物品
- 每条非红鲱鱼线索必须出现在至少一个物品的 hidden_clue_ids 中（使用线索的数组索引作为 "clue-N"，例如第一条线索是 "clue-1"）
- 红鲱鱼线索可以出现也可以不出现在 hidden_clue_ids 中
- npc_persona 应描述场景 NPC 的性格（例如 "沉默的管家，对死者忠诚"）
"""

CASE_GENERATION_HUMAN = "生成一个谋杀悬疑案件。难度：{difficulty}"

case_generation_prompt = ChatPromptTemplate.from_messages([
    ("system", CASE_GENERATION_SYSTEM),
    ("human", CASE_GENERATION_HUMAN),
])
