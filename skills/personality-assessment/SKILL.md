---
name: personality-assessment
description: "Multi-dimensional personality and emotional intelligence diagnostic skill. Analyzes cognitive distortions, EQ deficits, mindset patterns, impostor syndrome, and attachment styles through expert-backed conversational questions. TRIGGER when user wants to 'assess personality', 'diagnose EQ', 'find weaknesses', '性格分析', '情商测试', '认知偏差', '发现弱点', '心理评估', '自我认知', '性格弱点', '情感能力', '潜意识模式', or discusses personality assessment, emotional intelligence, self-awareness, cognitive behavioral patterns, or psychological diagnostics."
version: 1.0.0
entry_point: main.py
author: Claude Code
tags: [personality, psychology, EQ, assessment, coaching, self-awareness, cognitive-distortions]
---

# Personality Assessment Skill

Multi-dimensional personality and emotional intelligence diagnostic system built on established psychological frameworks.

## What It Does

1. **Selects** diagnostic dimensions based on user's focus area
2. **Generates** expert-backed questions from 6 psychological frameworks
3. **Analyzes** responses using AI + structured scoring rubrics
4. **Produces** actionable weakness reports with specific improvement plans

## Supported Frameworks

| Framework | Questions | What It Detects |
|-----------|-----------|-----------------|
| CBT Cognitive Distortions | 5-8 | 15 thinking traps (all-or-nothing, mind reading, catastrophizing, etc.) |
| Goleman's 4-Domain EQ | 8-10 | Self-awareness, self-management, social awareness, relationship management |
| Growth vs Fixed Mindset | 5 | Challenge avoidance, effort beliefs, criticism response, comparison patterns |
| Impostor Syndrome | 5-6 | 5 subtypes (perfectionist, superhero, natural genius, expert, soloist) |
| Attachment Styles | 5-6 | Secure, anxious-preoccupied, dismissive-avoidant, fearful-avoidant |
| Defense Mechanisms | 5-6 | Vaillant's hierarchy: pathological → immature → neurotic → mature |

## Conversation Technique

Uses Motivational Interviewing (OARS) + Socratic Questioning for natural, non-judgmental dialogue.

## How to Use

### Standalone
```bash
python <skill_path>/main.py --dimensions eq,mindset --questions 10 --output json
```

### As Library (for tutor integration)
```python
from personality_assessment import generate_questions, analyze_responses

questions = generate_questions(dimensions=["eq", "distortions", "mindset"], count=10)
# ... user answers ...
report = analyze_responses(questions, answers)
```

### List Available Dimensions
```bash
python <skill_path>/main.py --list-dimensions
```
