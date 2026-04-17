from langchain_core.prompts import ChatPromptTemplate

CASE_GENERATION_SYSTEM = """\
You are a Victorian era murder mystery writer creating a fully playable detective game case.
Set in 1890s London. All output must be in Chinese.

Difficulty rules:
- easy: clues are obvious (obviousness 0.7-1.0), 1 red herring, evidence points clearly to killer
- classic: clues moderate (0.4-0.8), 2 red herrings, some ambiguity
- hardcore: clues subtle (0.1-0.4), 3 red herrings, highly misleading evidence

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
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
      "is_red_herring": false
    }}
  ]
}}
Include exactly 3 suspects and 5 clues. true_murderer_index must be 0, 1, or 2.
"""

CASE_GENERATION_HUMAN = "Generate a murder mystery case. Difficulty: {difficulty}"

case_generation_prompt = ChatPromptTemplate.from_messages([
    ("system", CASE_GENERATION_SYSTEM),
    ("human", CASE_GENERATION_HUMAN),
])
