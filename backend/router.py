"""Conservative keyword routing: ambiguity is an explicit result, never a guess."""
import re
from typing import Literal
from pydantic import BaseModel

Kind = Literal['card', 'video']


class Route(BaseModel):
    intent: Literal['card', 'video', 'revision', 'clarification']
    target: Kind | None = None
    reason: str


def route_prompt(prompt: str, previous_target: Kind | None = None) -> Route:
    text = prompt.casefold()
    def has(pattern: str) -> bool:
        return bool(re.search(pattern, text))
    card = has(r'\b(cards?|cardback|deck)\b|بطاق|كرت')
    video = has(r'\b(video|ugc|advertisement|advert|reel|footage|clip)\b|فيديو|اعلان|إعلان')
    revision = has(r'\b(change|revise|modify|replace|instead|previous|make it|opening hook)\b|غيّر|غير|السابق|عدّل|عدل')
    if card and video:
        return Route(intent='clarification', reason='Should this run create a card or a video? Please request one asset at a time.')
    target = 'card' if card else 'video' if video else None
    if revision:
        if previous_target and (target is None or target == previous_target):
            return Route(intent='revision', target=previous_target, reason='Revision linked to the selected brief. No asset has been generated yet.')
        return Route(intent='clarification', reason='Select a matching previous run, or describe a new card or video to create.')
    if target:
        return Route(intent=target, target=target, reason=f'Explicit {target} keywords detected by the local rule-based router.')
    if previous_target and has(r'\b(blue|green|gold|red|shorter|longer|darker|lighter)\b'):
        return Route(intent='revision', target=previous_target, reason='Style adjustment linked to the selected brief.')
    return Route(intent='clarification', reason='Would you like a card design or a video advertisement? Include that in your next prompt.')
