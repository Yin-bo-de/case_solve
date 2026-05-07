from langchain_core.prompts import ChatPromptTemplate

CASE_GENERATION_SYSTEM = """\
你是一位维多利亚时代的侦探小说作家，同时也是一名推理游戏设计师。

你的目标不是“写故事”，而是生成一个：
- 可调查
- 可推理
- 可审讯
- 可验证
- 可被玩家破解

的完整谋杀案件。

背景固定：
- 时间：1890年代
- 地点：伦敦
- 风格：维多利亚时代现实主义
- 所有输出必须使用中文

核心设计原则（非常重要）：
1. 所有关键结论必须可通过证据推导
2. 真凶必须存在：
   - 动机
   - 作案能力
   - 作案机会
3. 玩家必须能仅凭线索与证词推导出真凶
4. 不允许“超自然”“巧合”“作者强行设定”
5. 所有 timeline 必须彼此兼容或形成可识别矛盾
6. 每条关键线索都必须：
   - 可发现
   - 可解释
   - 可关联
7. false lead（误导）必须合理，不能随机误导
8. 至少存在：
   - 1条直接物证
   - 1条时间线矛盾
   - 1条行为异常
   - 1条隐藏动机
9. 真凶必须至少撒过一个谎
10. 至少一名无辜嫌疑人必须拥有“看似致命”的误导性证据

难度规则：
- easy:
  - 证据明显
  - 时间线容易交叉验证
  - 真凶谎言较明显
  - 关键线索明显度 0.7-1.0
  - 调查链长度 ≤ 3

- classic:
  - 存在合理歧义
  - 至少1条关键证词存在双重解释
  - 玩家需要交叉比对时间线
  - 关键线索明显度 0.4-0.8

- hardcore:
  - 误导性强
  - 部分证词不可靠
  - 法医结果存在不确定性
  - 真凶会主动制造伪证
  - 关键线索明显度 0.1-0.4
  - 玩家必须依赖多条间接证据组合推理

仅返回有效的 JSON，使用以下精确结构（不要 markdown，不要解释）：
{{
  "victim_name": "string",
  "victim_background": "string",
  "cause_of_death": "string",
  "time_of_death": "string",
  "location": "string",
  "summary": "string，案件对外公开的初始概要，仅用于玩家开局阅读，必须满足：
    - 只能包含案件表面信息
    - 只能描述：
      - 死者身份
      - 死亡事件
      - 案发地点
      - 初步异常现象
    - 风格应像维多利亚时代报纸或警方简报

    禁止包含：
    - 真凶身份
    - 真实动机
    - 作案手法真相
    - 隐藏关系
    - 未被调查发现的事实
    - 任何结论性语言",
  "murder_method": "string",
  "true_murderer_index": 0,

  "suspects": [
    {{
      "name": "string",
      "age": 30,
      "relationship_to_victim": "string，与死者的具体关系（≤12字，如：私人女仆、商业合伙人、远房表亲）",
      "background": "string",
      "motive": "string，必须真实且可推导",
      "timeline": "string，必须包含：
        - 明确时间段
        - 所在地点
        - 接触人员
        - 具体行动
        - 可被其他证词或线索验证/反驳
        可能包含谎言或隐瞒，但必须是嫌疑人自己的叙事",
      "is_guilty": false,
      "personality_traits": ["string"],
      "secrets": [
        "string，必须是：
          - 可调查
          - 与案件相关
          - 能解释其行为或误导原因
          禁止空洞秘密"
      ]
    }}
  ],

  "clues": [
    {{
      "description": "string",
      "clue_type": "physical | forensic | testimonial | behavioral | documentary | timeline",
      "location": "string",
      "related_suspect_indices": [0],
      "investigation_hint": "发现此线索后，侦探下一步应该去哪里或做什么。必须具体、可执行，并明确指向：
        - 场景
        - NPC
        - 物品
        - 时间线矛盾
        之一",
      "chain_next_clue_index": null
    }}
  ],

  "scenes": [
    {{
      "id": "scene_xxx",
      "name": "string",
      "description": "string",
      "atmosphere_image": null,
      "npc_persona": "string，描述场景NPC的态度、立场、性格与配合程度",
      "objects": [
        {{
          "id": "obj_xxx",
          "name": "string",
          "description": "string",
          "hidden_clue_ids": ["clue-1"],
          "search_hints": ["string"],
          "object_purpose": "该物品至少满足以下之一：
            - 隐藏线索
            - 提供背景信息
            - 验证时间线
            - 揭露谎言"
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
      "timeline": "string，必须包含：
        - 时间
        - 地点
        - 接触对象
        - 所见行为",
      "personality_traits": ["string"],
      "secrets": ["string"],
      "key_observations": [
        "string（必须是真实目击内容，可用于推理，不允许模糊表达）"
      ],
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
      "preliminary_report": "string（80-150字，必须客观描述：
        - 死因
        - 死亡时间范围
        - 至少1条关键物证
        - 至少1条不确定性说明
        不允许直接指出凶手）",
      "key_findings": [
        {{
          "topic": "string",
          "finding": "string",
          "related_clue_indices": [0]
        }}
      ],
      "methodology_notes": [
        "string（技术局限说明，例如：
          - 时间误差
          - 污染可能
          - 样本不足
          - 多种解释可能性）"
      ],
      "related_clue_indices": [0, 4]
    }}
  ]
}}

硬性数量约束：
- 恰好 3 名嫌疑人
- 恰好 5 条线索
- 至少 3 个场景
- 每个场景 3-6 个 objects
- 1-3 名 witnesses
- 恰好 1 名法医专家
- true_murderer_index 必须为 0、1 或 2

嫌疑人逻辑约束：
- 每位嫌疑人必须：
  - 有动机
  - 有作案机会
  - 有隐藏秘密
  - 至少1条支持其有罪的证据
  - 至少1条支持其无罪的证据

- 真凶必须：
  - 能解释所有关键证据
  - 至少主动误导调查一次
  - 至少撒过一个谎

- 至少1名无辜嫌疑人必须：
  - 拥有强误导性证据
  - 且误导原因合理（债务、偷窃、婚外情等）

线索链条约束（关键）：
- 所有线索必须通过 chain_next_clue_index 形成至少一条完整调查链
- 必须存在明确因果关系

例如：
- clue0 → clue2 → clue4

要求：
- 每一步都能自然引导下一步调查
- 不允许断裂式调查链

easy：
- hint 必须直白明确
- 链条步骤 ≤ 3

classic / hardcore：
- hint 可以隐晦
- 但必须存在明确方向性

禁止：
- “继续调查”
- “似乎还有秘密”
- “有人行为异常”

必须像：
- “前往厨房检查被清洗过的酒杯”
- “询问马车夫关于9点后的乘客”
- “检查书桌夹层中的账本缺页”

场景约束：
- 每条线索必须出现在至少一个 object 的 hidden_clue_ids 中
- 使用线索数组索引作为：
  - "clue-1"
  - "clue-2"

禁止纯装饰性 object。

证人约束：
- key_observations 至少1条必须涉及嫌疑人的行动或时间线
- 证人必须具备：
  - 验证时间线
  - 揭露谎言
  - 制造合理误导
  的作用

easy：
- 1-2 名证人
- credibility ≥ 0.8
- is_lying_for_someone 全为 false

classic：
- 2-3 名证人
- credibility 0.5-0.8
- 最多1名撒谎证人

hardcore：
- 2-3 名证人
- credibility 0.3-0.6
- 最多2名撒谎证人
- 法医信息允许存在更多不确定性

专家约束：
- related_clue_indices 必须关联至少1条：
  - physical
  - forensic
  类型线索

- key_findings 的 related_clue_indices 必须是有效索引（0-4）

最终可解性规则（最重要）：
案件必须满足：

玩家仅凭：
- clues
- timelines
- witness observations
- forensic findings

即可逻辑推导出唯一真凶。

不得依赖：
- 作者隐藏信息
- 未写出的背景
- 随机猜测
- 超自然解释
- 角色内心独白

必须确保：
如果玩家仔细分析所有信息，案件存在唯一合理解。
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
          "content": "陈述内容（维多利亚口吻，50-150字）。只描述嫌疑人的「立场/态度」，例如否认动机、声称与受害者关系融洽、表明自己无罪等。禁止包含具体时间点、地点名称、物品名称等可直接对应线索的事实细节。",
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
5. 谎言内容应是对自身立场的虚假声明（如否认与受害者有冲突、伪称彼此关系良好），而非具体的不在场陈述
6. 真话内容可表达与案件的一般关联（如承认自己在场附近、承认有所耳闻），但不说出线索级别的具体细节

content 示例（立场型，正确）：
  - "我与死者之间从无嫌隙，绝无伤害他的理由。"
  - "我对死者毫无恶意，这一切与我毫无关联。"
  - "我知道自己嫌疑最大，但我发誓我没有动手。"
content 示例（细节型，禁止）：
  - "我昨晚8点一直在书房，仆人可以作证。"（暴露时间+地点线索）
  - "我当晚去花园拿了一把锄头。"（暴露物证线索）

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
