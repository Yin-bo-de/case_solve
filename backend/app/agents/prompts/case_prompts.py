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
      "relationship_to_victim": "string，与死者的具体关系（≤12字，如：私人女仆、商业合伙人、远房表亲）",
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
  ],
  "witnesses": [
    {{
      "name": "string",
      "age": 30,
      "occupation": "string",
      "relationship_to_case": "string",
      "timeline": "string",
      "personality_traits": ["string"],
      "secrets": ["string"],
      "key_observations": ["string（证人确实目击的事实，至少 1 条）"],
      "is_lying_for_someone": false,
      "bribed_by_suspect_index": null,
      "related_suspect_indices": [0],
      "credibility": 0.7
    }}
  ],
  "experts": [
    {{
      "name": "string",
      "title": "皇家法医",
      "expertise": ["法医病理", "毒物分析"],
      "preliminary_report": "string（80-150字，客观描述死因、死亡时间、现场关键物证）",
      "key_findings": [
        {{
          "topic": "string",
          "finding": "string",
          "related_clue_indices": [0]
        }}
      ],
      "methodology_notes": ["string（技术局限说明，如时间推断误差范围）"],
      "related_clue_indices": [0, 4]
    }}
  ]
}}
包含恰好 3 名嫌疑人和 5 条线索。true_murderer_index 必须是 0、1 或 2。
每位嫌疑人的 relationship_to_victim 必须填写（≤12字），描述其与死者的具体关系，如「私人女仆」「商业合伙人」「远房表亲」。

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

证人约束：
- 包含 1-3 名证人（目击者、邻居、雇员等）
- 每名证人的 related_suspect_indices 必须包含至少 1 个有效的嫌疑人索引（0-2）
- key_observations 中至少 1 条必须涉及某嫌疑人的时间线或行动
- easy 难度：1-2 名证人，credibility ≥ 0.8，is_lying_for_someone 全为 false
- classic 难度：2-3 名证人，credibility 0.5-0.8，最多 1 名 is_lying_for_someone=true
- hardcore 难度：2-3 名证人，credibility 0.3-0.6，最多 2 名 is_lying_for_someone=true
- bribed_by_suspect_index 为撒谎证人被收买的嫌疑人索引，其他证人设为 null

专家约束：
- 恰好包含 1 名法医专家
- related_clue_indices 必须覆盖至少 1 条非红鲱鱼物证线索（physical 或 forensic 类型）
- preliminary_report 必须客观描述死因、死亡时间窗口、至少 1 条现场关键物证，不能提及嫌疑人姓名
- key_findings 的 related_clue_indices 必须是有效的线索索引（0-4）
- hardcore 难度：preliminary_report 留出更多模糊细节，methodology_notes 中标注更多不确定性
"""

CASE_GENERATION_HUMAN = "生成一个谋杀悬疑案件。难度：{difficulty}"

case_generation_prompt = ChatPromptTemplate.from_messages([
    ("system", CASE_GENERATION_SYSTEM),
    ("human", CASE_GENERATION_HUMAN),
])

SUSPECT_STATEMENTS_GENERATION_SYSTEM = """\
你是一位维多利亚时代谋杀悬疑游戏的编剧，正在为案件中的每位嫌疑人设计审讯陈述。
每条陈述都将是玩家在审讯阶段可以向嫌疑人出示线索进行对质的对象。

任务：为每位嫌疑人设计 2-4 条陈述。陈述必须符合案件真相，部分为谎言，部分为真话。
谎言必须可以被案件中已存在的线索反驳。

输出格式（严格 JSON，不要 markdown，不要解释）：
{{
  "suspects_statements": [
    {{
      "suspect_id": "suspect-1",
      "statements": [
        {{
          "id": "stmt-s1-1",
          "content": "陈述内容（维多利亚口吻，50-150字）",
          "is_lie": false,
          "refutable_by_clue_ids": [],
          "revealed_when_broken": false
        }}
      ]
    }}
  ]
}}

陈述设计规则：
1. 每位嫌疑人必须有 2-4 条陈述
2. 真凶（is_guilty=true）必须至少有 2 条 is_lie=true 的谎言，且每条谎言的 refutable_by_clue_ids 非空
3. 无辜嫌疑人可以有 0-1 条谎言，其余为真话
4. 至少 1 名嫌疑人（最好是真凶）持有 ≥2 条谎言链
5. 谎言内容应与嫌疑人的时间线、动机、背景相关
6. 真话内容可提供有用信息，帮助玩家推理

弱绑定约束（必须遵守）：
- refutable_by_clue_ids 中的每个 clue_id 必须是案件中真实存在的线索 id
- 每个 clue_id 对应的线索，其 related_suspect_ids 必须包含当前 suspect_id
- 不满足上述约束的 refutable_by_clue_ids 将被视为非法，导致陈述被拒绝
- 若某条陈述是谎言但找不到合适的 clue 来反驳，可将其设为 is_lie=false（改为真话）

revealed_when_broken 规则：
- 只有真凶的陈述中，最多 1 条可设为 revealed_when_broken=true
- 该陈述在嫌疑人状态变为 broken（崩溃）时，会额外揭露关键信息
- 内容应涉及案件核心真相（如作案动机、手法细节）
"""

SUSPECT_STATEMENTS_GENERATION_HUMAN = """\
案件概要：{case_summary}
案件真相：{murder_method}
真凶ID：{true_murderer_id}
难度：{difficulty}

案件线索列表（每条线索包含 id、description、related_suspect_ids）：
{clues_block}

嫌疑人列表（包含 id、name、background、motive、timeline、is_guilty）：
{suspects_block}

请为每位嫌疑人设计陈述。确保所有 refutable_by_clue_ids 严格指向上述线索列表中存在且 related_suspect_ids 包含该嫌疑人的线索。
"""

suspect_statements_generation_prompt = ChatPromptTemplate.from_messages([
    ("system", SUSPECT_STATEMENTS_GENERATION_SYSTEM),
    ("human", SUSPECT_STATEMENTS_GENERATION_HUMAN),
])
