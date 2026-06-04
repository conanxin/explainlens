"""Prompt templates for image generation and (future) LLM integrations.

Currently used to construct image prompts for cartoon explainer panels.
All templates are designed to produce English prompts suitable for
Stable Diffusion, DALL-E, Midjourney, etc.
"""

from __future__ import annotations

# Default image generation style
DEFAULT_STYLE = (
    "bright clean cartoon explainer style, modern, simple background, "
    "no text inside image, consistent character, educational visual metaphor, "
    "soft lighting, not yellowish"
)

# Visual metaphor catalog — maps teaching step index (0-7) to a metaphor
METAPHOR_CATALOG: list[dict] = [
    {
        "metaphor": "maze or puzzle",
        "scene": "A person stands at the entrance of a glowing maze or a giant puzzle, looking curious.",
        "characters": ["curious explorer figure", "maze walls", "puzzle pieces"],
        "composition": "Wide shot, explorer small against the puzzle",
    },
    {
        "metaphor": "magnifying glass over a map",
        "scene": "A giant magnifying glass hovers over a map of the world, highlighting one glowing spot.",
        "characters": ["magnifying glass", "world map", "glowing spot"],
        "composition": "Close-up on the magnifying glass and the highlighted area",
    },
    {
        "metaphor": "old vs new — side by side",
        "scene": "Left side: a rusty, creaky machine. Right side: a sleek, modern machine. A cartoon arrow points right.",
        "characters": ["old machine", "new machine", "arrow"],
        "composition": "Split screen, old left / new right",
    },
    {
        "metaphor": "library or knowledge tree",
        "scene": "A giant tree with glowing ideas as fruits, or a library where books float and glow.",
        "characters": ["knowledge tree", "floating books", "glowing idea fruits"],
        "composition": "Centered tree, panoramic view",
    },
    {
        "metaphor": "robot helper or assembly line",
        "scene": "A friendly robot helper arranges building blocks step by step into a beautiful structure.",
        "characters": ["friendly robot", "building blocks", "finished structure"],
        "composition": "Sequential, left-to-right progression",
    },
    {
        "metaphor": "detective with evidence board",
        "scene": "A cartoon detective pins photos and red string connections on an evidence board.",
        "characters": ["detective figure", "evidence board", "photos", "red string"],
        "composition": "Detective in foreground, board behind",
    },
    {
        "metaphor": "bridge with warning signs",
        "scene": "A bridge spanning a gap; warning signs and caution tape are visible on one side.",
        "characters": ["bridge", "gap", "warning signs", "caution tape"],
        "composition": "Side view of bridge, signs visible",
    },
    {
        "metaphor": "lightbulb moment",
        "scene": "A cartoon person stands under a giant bright lightbulb, looking enlightened and happy.",
        "characters": ["enlightened person", "giant lightbulb", "sparkles"],
        "composition": "Centered, lightbulb dominating upper half",
    },
]

# Fixed teaching step definitions
TEACHING_STEPS = [
    {
        "title": "这份内容想解决什么问题？",
        "goal": "Identify the core problem or question the content addresses.",
        "audience": "general",
        "risk": "Oversimplifying the problem may lose nuance.",
    },
    {
        "title": "为什么这个问题重要？",
        "goal": "Explain why this problem matters and what is at stake.",
        "audience": "general",
        "risk": "May overstate significance without sufficient evidence.",
    },
    {
        "title": "旧方法或常见理解有什么不足？",
        "goal": "Contrast existing approaches and highlight gaps.",
        "audience": "general",
        "risk": "Straw-manning old approaches without fair representation.",
    },
    {
        "title": "核心概念是什么？",
        "goal": "Introduce and define the key concepts clearly.",
        "audience": "general",
        "risk": "Jargon overload without sufficient explanation.",
    },
    {
        "title": "新方法或关键机制如何运作？",
        "goal": "Explain how the proposed method or mechanism works.",
        "audience": "general",
        "risk": "Technical depth may confuse non-experts.",
    },
    {
        "title": "有什么证据、案例或推理？",
        "goal": "Present evidence, data, examples, or logical reasoning.",
        "audience": "general",
        "risk": "Cherry-picking evidence creates misleading impression.",
    },
    {
        "title": "局限和风险是什么？",
        "goal": "Discuss limitations, caveats, and open questions honestly.",
        "audience": "general",
        "risk": "Undermining confidence in otherwise valid work.",
    },
    {
        "title": "一句话总结：它改变了我们什么理解？",
        "goal": "Synthesize the key takeaway and changed perspective.",
        "audience": "general",
        "risk": "Overgeneralizing may misrepresent nuanced conclusions.",
    },
]


def build_image_prompt(
    metaphor: str,
    scene_desc: str,
    extra_instructions: str = "",
    style: str = DEFAULT_STYLE,
) -> str:
    """Construct a single image generation prompt.

    Args:
        metaphor: The visual metaphor (e.g. 'maze', 'bridge').
        scene_desc: Description of the visual scene.
        extra_instructions: Any additional must-include or must-avoid notes.
        style: The style string to append.

    Returns:
        A complete English image prompt string.
    """
    parts = [
        f"Visual metaphor: {metaphor}.",
        f"Scene: {scene_desc}.",
    ]
    if extra_instructions:
        parts.append(extra_instructions)
    parts.append(style)
    return " ".join(parts)
