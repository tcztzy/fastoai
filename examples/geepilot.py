import json

from openai import OpenAI
from pydantic import BaseModel


class Primer3Parameters(BaseModel):
    sequence_id: str
    sequence_template: str
    primer_task: str = "generic"
    primer_pick_left_primer: bool = True
    primer_pick_internal_oligo: bool = False
    primer_pick_right_primer: bool = True
    primer_opt_size: int = 20
    primer_min_size: int = 18
    primer_max_size: int = 22
    primer_product_size_range: str = "75-150"
    primer_explain_flag: int = 1


client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")

SYSTEM_PROMPT = f"""
Your name is GeePilot, you are a very good bioinformatics scientist.
You are very familiar with Primer3, a widely used tool for designing CRISPR primers.
You are currently working on a project to design primers for a new gene sequence.
The Primer3's parameters are very important for designing primers.
Primer3's input parameter can be described in following json schema: {json.dumps(Primer3Parameters.model_json_schema())}"""

print(
    client.chat.completions.create(
        model="llama3",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "Can you show me an example of how to use Primer3 to design primers for a gene sequence? Just show me the parameters that I need to provide to Primer3.",
            },
        ],
        response_format={"type": "json_object"},
    )
)
