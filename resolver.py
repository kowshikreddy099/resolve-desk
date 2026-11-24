import json
import math
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
KB = json.loads((BASE / 'knowledge.json').read_text(encoding='utf-8-sig'))
STOP = set('someone please need the a to my is and i it of in an was for with when but'.split())

def tokens(text):
    return [w for w in re.findall(r'[a-z0-9]+', text.lower()) if w not in STOP]

documents = [(item, tokens(example)) for item in KB for example in item['examples']]
frequency = Counter(w for _, words in documents for w in set(words))
idf = {w: 1 + math.log((1 + len(documents)) / (1 + n)) for w, n in frequency.items()}

def vector(words):
    weights = {w: count * idf.get(w, 1) for w, count in Counter(words).items()}
    norm = math.sqrt(sum(n*n for n in weights.values())) or 1
    return {w: n/norm for w, n in weights.items()}

INDEX = [(item, vector(words)) for item, words in documents]

def analyze(text):
    query = vector(tokens(text))
    best = {}
    for item, doc in INDEX:
        score = sum(query.get(w, 0) * n for w, n in doc.items())
        if item['team'] not in best or score > best[item['team']][0]:
            best[item['team']] = (score, item, sorted(query.keys() & doc.keys()))
    first, second = sorted(best.values(), key=lambda row: -row[0])[:2]
    score, item, evidence = first
    clear = score >= .21 and score - second[0] >= .07
    return dict(team=item['team'] if clear else 'Manual review', score=round(score*100),
                evidence=evidence, priority='High' if re.search(r'\b(unauthori[sz]ed|fraud|hacked|stolen|outage)\b', text, re.I) else 'Normal',
                plan=item['plan'] if clear else 'Ask for the symptoms, timing, and desired outcome before assigning a team.')

