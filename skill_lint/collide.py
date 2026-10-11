"""Trigger-collision maths: Jaccard on token sets plus TF-IDF cosine."""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from .textutil import tokens, trigger_phrases


@dataclass
class Collision:
    a: object
    b: object
    jaccard: float
    cosine: float
    score: float
    shared_triggers: list = field(default_factory=list)
    shared_terms: list = field(default_factory=list)

    def to_dict(self):
        return {"a": self.a.label, "b": self.b.label, "jaccard": round(self.jaccard, 3),
                "cosine": round(self.cosine, 3), "score": round(self.score, 3),
                "shared_triggers": self.shared_triggers, "shared_terms": self.shared_terms}


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def idf_table(docs: list) -> dict:
    n = len(docs)
    df = Counter()
    for d in docs:
        df.update(set(d))
    return {t: math.log((1 + n) / (1 + c)) + 1.0 for t, c in df.items()}


def tfidf_vec(doc: list, idf: dict) -> dict:
    tf = Counter(doc)
    return {t: (1 + math.log(c)) * idf.get(t, 1.0) for t, c in tf.items()}


def cosine(u: dict, v: dict) -> float:
    if not u or not v:
        return 0.0
    dot = sum(w * v.get(t, 0.0) for t, w in u.items())
    nu = math.sqrt(sum(w * w for w in u.values()))
    nv = math.sqrt(sum(w * w for w in v.values()))
    return dot / (nu * nv) if nu and nv else 0.0


def find_collisions(skills, threshold: float = 0.45, min_tokens: int = 3):
    """Return Collision objects for pairs at or above *threshold*, highest first.

    score = max(jaccard, cosine). Two skills that share an identical quoted or
    listed trigger phrase are always reported (score is floored at the threshold).
    """
    usable = [s for s in skills if s.description]
    docs = [tokens(s.name.replace("-", " ") + " " + s.description) for s in usable]
    idf = idf_table(docs)
    vecs = [tfidf_vec(d, idf) for d in docs]
    sets = [set(d) for d in docs]
    trig = [set(trigger_phrases(s.description)) for s in usable]
    out = []
    for i in range(len(usable)):
        if len(sets[i]) < min_tokens:
            continue
        for j in range(i + 1, len(usable)):
            if len(sets[j]) < min_tokens:
                continue
            if usable[i].name and usable[i].name == usable[j].name:
                continue  # duplicates are SKL012's job
            jac = jaccard(sets[i], sets[j])
            cos = cosine(vecs[i], vecs[j])
            shared_t = sorted(trig[i] & trig[j])
            score = max(jac, cos)
            if shared_t:
                score = max(score, threshold)
            if score >= threshold:
                shared_terms = sorted(sets[i] & sets[j], key=lambda t: (-idf.get(t, 0), t))[:6]
                out.append(Collision(usable[i], usable[j], jac, cos, score, shared_t, shared_terms))
    out.sort(key=lambda c: (-c.score, c.a.label, c.b.label))
    return out
