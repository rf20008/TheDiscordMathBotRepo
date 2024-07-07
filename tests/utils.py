import random

import disnake
import disnake.ext


def generate_many_randoms(many=1, lows=(), highs=()):
    if len(highs) != len(lows) or len(lows) != many:
        raise ValueError("the arrays given do not match")
    return (random.randint(lows[i], highs[i]) for i in range(many))


def check_embed_equality(expected, result):
    if not isinstance(result, disnake.Embed):
        raise TypeError("the result is not an Embed")
    if not isinstance(expected, disnake.Embed):
        raise TypeError("expected isn't an embed either")
    for slot in expected.__slots__:
        if slot == "colour":
            slot = "color"
        if getattr(expected, slot, None) != getattr(result, slot, None):
            raise ValueError(
                f"""The embeds don't match 
    (slot {slot}) is not the same
    the expected value is "{getattr(expected, slot, None)}"
    but the actual value is "{getattr(result, slot, None)}" """
            )
