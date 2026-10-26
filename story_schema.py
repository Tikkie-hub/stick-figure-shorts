"""Shared vocabulary for the storyboard, editor and renderer."""

ACTIONS = {
    "discover",
    "think",
    "run",
    "celebrate",
    "space",
    "read",
    "knock",
    "listen",
    "open_door",
    "offer",
    "walk",
    "phone",
    "look",
}
SCENE_CHOICES = {
    "setting": {"studio", "room", "corridor", "elevator", "city", "diagram"},
    "camera": {"wide", "medium", "close", "detail"},
    "cast": {"solo", "pair", "friend", "none"},
    "prop": {"none", "phone", "bottle", "letter", "box"},
    "graphic": {"none", "spotlight", "building", "countdown", "comparison"},
    "expression": {"neutral", "worried", "surprised", "happy", "determined"},
}
SCENE_DEFAULTS = {
    "setting": "room",
    "camera": "medium",
    "cast": "solo",
    "prop": "none",
    "graphic": "none",
    "expression": "neutral",
}
