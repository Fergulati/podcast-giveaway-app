import os
import random
import re
from typing import Dict, List


def load_transcript(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _words(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", text)


def generate_question(transcript: str) -> Dict[str, object]:
    words = _words(transcript)
    if len(words) < 4:
        return {"question": "Transcript too short", "options": []}
    idx = random.randrange(len(words))
    correct = words[idx]
    options = {correct}
    while len(options) < 4:
        options.add(random.choice(words))
    options_list = list(options)
    random.shuffle(options_list)
    question = f"Which word appears in the transcript near position {idx + 1}?"
    return {"question": question, "options": options_list}
