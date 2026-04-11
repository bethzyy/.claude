"""
Personality Assessment Frameworks — Expert-backed question banks and scoring rubrics.

Each framework contains:
- description: What it measures
- questions: Expert-designed diagnostic questions with scoring criteria
- analysis_prompt: AI prompt template for analyzing free-form responses
"""

# ============================================================
# Framework 1: CBT Cognitive Distortions (Beck/Burns)
# ============================================================
CBT_DISTORTIONS = {
    "id": "cognitive-distortions",
    "name": "认知扭曲筛查",
    "description": "基于 Aaron Beck 和 David Burns 的认知行为疗法框架，识别15种常见认知扭曲模式",
    "questions": [
        {
            "id": "cd-1",
            "dimension": "polarized_thinking",
            "title": "非黑即白思维",
            "question": "当你在一件事上没有做到完美时，你通常会怎么评价自己？请描述一个最近的例子。",
            "scoring": {
                "high": ["完美", "失败", "全部", "要么", "彻底", "完全不行", "零", "从不", "总是"],
                "low": ["还好", "可以接受", "部分", "差不多", "正常", "大多数"]
            }
        },
        {
            "id": "cd-2",
            "dimension": "mental_filter",
            "title": "心理过滤",
            "question": "上次收到包含好评和差评的反馈时，你更关注哪部分？为什么那个部分更吸引你的注意力？",
            "scoring": {
                "high": ["只看", "差评", "负面", "缺点", "忽略优点", "盯着", "放大", "最在意"],
                "low": ["平衡", "整体", "综合考虑", "都看", "客观"]
            }
        },
        {
            "id": "cd-3",
            "dimension": "mind_reading",
            "title": "读心术",
            "question": "你有没有过这样的情况——你很确定某个人对你有某种看法，但后来发现你的判断是错的？能举个例子吗？",
            "scoring": {
                "high": ["经常", "总是觉得", "肯定认为", "不用问就知道", "他们一定", "我能感觉到"],
                "low": ["偶尔", "不确定", "会去确认", "猜错过", "后来发现不是"]
            }
        },
        {
            "id": "cd-4",
            "dimension": "catastrophizing",
            "title": "灾难化",
            "question": "当一件小事出了差错时，你的思维会往哪个方向走？请描述你脑海中最常出现的'连锁反应'。",
            "scoring": {
                "high": ["完了", "毁了", "最坏", "不可挽回", "连锁", "后果严重", "越来越糟", "无法承受"],
                "low": ["小事", "没什么", "能解决", "冷静", "不影响", "可控"]
            }
        },
        {
            "id": "cd-5",
            "dimension": "overgeneralization",
            "title": "过度概括",
            "question": "你是否有过这样的经历：一次失败后就觉得'我总是这样'或'我永远做不到'？什么场景容易触发这种想法？",
            "scoring": {
                "high": ["总是", "永远", "每次都", "从不", "所有人", "从来没", "不可能"],
                "low": ["有时候", "这次", "不一定", "例外", "概率"]
            }
        },
        {
            "id": "cd-6",
            "dimension": "should_statements",
            "title": "应该思维",
            "question": "你有多经常对自己说'我应该...'、'我必须...'或'我不该...'？这些'应该'让你感觉如何？",
            "scoring": {
                "high": ["经常", "应该", "必须", "不应该", "义务", "愧疚", "做不到就", "不...就不对"],
                "low": ["偶尔", "希望", "想要", "选择", "灵活", "没有必须"]
            }
        },
        {
            "id": "cd-7",
            "dimension": "emotional_reasoning",
            "title": "情绪化推理",
            "question": "你是否有过这样的体验——因为感觉很强烈，就认为那一定是事实？比如'我感觉自己是废物，所以我一定是'。",
            "scoring": {
                "high": ["感觉就是", "因为觉得所以", "直觉告诉我", "心里觉得就是", "一定是", "骗不了自己"],
                "low": ["感觉不等于事实", "会验证", "理性分析", "证据", "客观"]
            }
        },
        {
            "id": "cd-8",
            "dimension": "personalization",
            "title": "个人化归因",
            "question": "当团队项目出了问题，即使不是你的责任，你会不会觉得'如果我当时...就好了'？请举个例子。",
            "scoring": {
                "high": ["都是我的错", "如果我", "怪自己", "我的责任", "我不够", "没做好"],
                "low": ["不是我", "大家的", "客观原因", "分清责任", "不怪自己"]
            }
        },
    ],
    "analysis_prompt": """你是一位认知行为疗法（CBT）专家。请分析用户的回答，识别以下认知扭曲模式：

1. **非黑即白思维** (Polarized Thinking) — 只看到全有或全无
2. **心理过滤** (Mental Filter) — 只关注负面，忽略正面
3. **读心术** (Mind Reading) — 假设知道别人的想法
4. **灾难化** (Catastrophizing) — 放大后果到最坏情况
5. **过度概括** (Overgeneralization) — 从一次事件推广到"总是/永远"
6. **应该思维** (Should Statements) — 用"应该/必须"束缚自己
7. **情绪化推理** (Emotional Reasoning) — 把感觉当成事实
8. **个人化** (Personalization) — 把不属于自己责任的事揽到自己身上

对每个检测到的扭曲：
- 指出具体表现（引用用户原话）
- 严重程度：high/medium/low
- 该扭曲如何影响日常生活
- 对应的改善建议（具体的认知重构练习）

输出 JSON 格式：
{
  "distortions": [
    {
      "type": "distortion_name",
      "severity": "high|medium|low",
      "evidence": "用户说的...",
      "impact": "这个扭曲会导致...",
      "reframe_exercise": "具体练习建议"
    }
  ],
  "overall_pattern": "整体认知模式描述",
  "recommended_focus": "建议优先改善的1-2个扭曲"
}""",
}


# ============================================================
# Framework 2: Goleman's 4-Domain EQ
# ============================================================
GOLEMAN_EQ = {
    "id": "eq-goleman",
    "name": "情商评估",
    "description": "基于 Daniel Goleman 的四维情商模型，评估自我认知、自我管理、社会认知、关系管理",
    "questions": [
        {
            "id": "eq-1",
            "domain": "self_awareness",
            "title": "情绪自我觉察",
            "question": "当你感到沮丧时，你通常是在反应之后才意识到自己沮丧，还是在反应之前就能觉察到？请描述一次你注意到自己情绪变化的经历。",
            "scoring": {
                "high": ["之后才意识到", "反应了才知道", "事后", "爆发了才发现", "别人提醒"],
                "low": ["立刻", "觉察到", "能感知", "意识到变化", "停下来", "深呼吸"]
            }
        },
        {
            "id": "eq-2",
            "domain": "self_awareness",
            "title": "准确自我评估",
            "question": "你觉得别人对你的评价，和你的自我评价一致吗？有没有你觉得很了解自己，但别人看到的和你不同的情况？",
            "scoring": {
                "high": ["不一致", "差别很大", "别人说我很", "没想到别人觉得", "误解"],
                "low": ["基本一致", "了解自己", "客观", "准确", "清楚"]
            }
        },
        {
            "id": "eq-3",
            "domain": "self_management",
            "title": "情绪自控力",
            "question": "上次有人在公开场合让你很生气时，你当时做了什么？事后你觉得自己的处理方式怎么样？",
            "scoring": {
                "high": ["忍不住", "当场发作", "摔门", "怼回去", "控制不住", "说出后悔的话"],
                "low": ["忍住", "深呼吸", "冷静", "私下说", "延迟反应", "控制住了"]
            }
        },
        {
            "id": "eq-4",
            "domain": "self_management",
            "title": "适应性",
            "question": "当计划突然改变时（比如临时被安排了别的任务），你的第一反应是什么？你会怎么调整？",
            "scoring": {
                "high": ["烦躁", "不爽", "反感", "抗拒", "焦虑", "打乱了节奏"],
                "low": ["灵活", "没关系", "调整", "接受", "随时可以", "OK"]
            }
        },
        {
            "id": "eq-5",
            "domain": "social_awareness",
            "title": "共情能力",
            "question": "当一个朋友向你倾诉烦恼时，你更倾向于：立刻给建议，还是先倾听并理解TA的感受？你觉得哪种更难做到？",
            "scoring": {
                "high": ["给建议", "解决问题", "觉得倾听没用", "不知道说什么", "不耐烦"],
                "low": ["先听", "理解感受", "陪伴", "共鸣", "确认TA的感受"]
            }
        },
        {
            "id": "eq-6",
            "domain": "social_awareness",
            "title": "社交信号感知",
            "question": "在群聊或会议中，你能察觉到谁被冷落、谁不高兴了吗？你是通过什么线索发现的？",
            "scoring": {
                "high": ["注意不到", "发现不了", "别人说了才知道", "不敏感", "没注意"],
                "low": ["能察觉", "表情", "语气", "沉默", "肢体语言", "细微变化"]
            }
        },
        {
            "id": "eq-7",
            "domain": "relationship_management",
            "title": "冲突处理",
            "question": "当你和重要的人（家人/朋友/同事）发生分歧时，你通常怎么处理？有没有一种你反复使用但效果不好的方式？",
            "scoring": {
                "high": ["逃避", "冷战", "争吵", "妥协自己", "不说", "忍着"],
                "low": ["沟通", "坦诚", "找到共识", "表达感受", "解决", "建设性"]
            }
        },
        {
            "id": "eq-8",
            "domain": "relationship_management",
            "title": "影响力与激励",
            "question": "你觉得你能激励身边的人吗？当你希望别人配合你做一件事时，你通常会怎么做？",
            "scoring": {
                "high": ["命令", "要求", "强迫", "说服不了", "放弃", "自己做"],
                "low": ["影响", "鼓励", "示范", "沟通", "共同目标", "感染"]
            }
        },
    ],
    "analysis_prompt": """你是一位情商（EQ）评估专家，基于 Daniel Goleman 的四维情商模型进行分析。

四个维度：
1. **自我认知** (Self-Awareness) — 能否准确识别自己的情绪、优势和局限
2. **自我管理** (Self-Management) — 能否有效调节情绪、保持适应性
3. **社会认知** (Social Awareness) — 能否感知他人情绪、理解社交动态
4. **关系管理** (Relationship Management) — 能否有效处理冲突、影响和激励他人

对每个维度：
- 给出 1-10 分（1=严重不足，10=优秀）
- 指出具体的强项和弱项（引用用户原话）
- 识别1-2个最需要改善的子能力
- 提供具体的日常练习建议

输出 JSON 格式：
{
  "dimensions": {
    "self_awareness": {"score": 4, "strengths": [...], "weaknesses": [...], "exercises": [...]},
    "self_management": {"score": 3, "strengths": [...], "weaknesses": [...], "exercises": [...]},
    "social_awareness": {"score": 5, "strengths": [...], "weaknesses": [...], "exercises": [...]},
    "relationship_management": {"score": 4, "strengths": [...], "weaknesses": [...], "exercises": [...}
  },
  "eq_total": 16,
  "top_improvements": ["改善建议1", "改善建议2"],
  "overall_pattern": "整体情商模式描述"
}""",
}


# ============================================================
# Framework 3: Growth vs Fixed Mindset (Dweck)
# ============================================================
GROWTH_MINDSET = {
    "id": "mindset",
    "name": "思维模式评估",
    "description": "基于 Carol Dweck 的成长型/固定型思维研究，评估面对挑战、努力、批评和失败的反应模式",
    "questions": [
        {
            "id": "ms-1",
            "dimension": "challenge_response",
            "title": "面对挑战",
            "question": "面对一个你从未做过、看起来很难的任务，你的第一反应是什么？请回忆一次具体的经历。",
            "scoring": {
                "fixed": ["不想做", "做不到", "太难了", "放弃了", "不是我的强项", "肯定失败"],
                "growth": ["试试看", "挑战", "学习", "机会", "有趣", "正好练练"]
            }
        },
        {
            "id": "ms-2",
            "dimension": "effort_belief",
            "title": "对努力的看法",
            "question": "你认为'努力'意味着什么？如果你需要花很长时间才能做好一件事，这说明什么？",
            "scoring": {
                "fixed": ["没天赋", "笨", "不如别人", "白费", "不够聪明", "效率低"],
                "growth": ["在进步", "学习过程", "正常", "需要时间", "积累", "值得"]
            }
        },
        {
            "id": "ms-3",
            "dimension": "criticism_response",
            "title": "面对批评",
            "question": "当你尊敬的人批评你的工作时，你的第一反应是什么？你会怎么处理这个批评？",
            "scoring": {
                "fixed": ["难受", "生气", "防御", "否定", "不在乎", "不服", "打击"],
                "growth": ["感谢", "思考", "改进", "问细节", "接受", "学习"]
            }
        },
        {
            "id": "ms-4",
            "dimension": "others_success",
            "title": "面对他人成功",
            "question": "当你身边的人在某件事上比你做得好时，你的内心感受是什么？你会怎么做？",
            "scoring": {
                "fixed": ["嫉妒", "不舒服", "比较", "焦虑", "压力", "觉得自己不行"],
                "growth": ["高兴", "学习", "请教", "激励", "参考", "取经"]
            }
        },
        {
            "id": "ms-5",
            "dimension": "setback_resilience",
            "title": "面对挫折",
            "question": "上次你在一个重要的事情上失败了之后，你花了多长时间才重新开始？是什么让你重新开始的？",
            "scoring": {
                "fixed": ["很久", "还没", "放弃了", "不敢", "阴影", "害怕再试"],
                "growth": ["很快", "总结", "分析原因", "调整", "再来一次", "没放弃"]
            }
        },
    ],
    "analysis_prompt": """你是一位思维模式评估专家，基于 Carol Dweck 的成长型/固定型思维研究。

评估五个维度：
1. **面对挑战** — 回避还是拥抱困难任务
2. **对努力的看法** — 认为努力是"没天赋的证据"还是"进步的必经之路"
3. **面对批评** — 防御还是从中学习
4. **面对他人成功** — 威胁还是激励
5. **面对挫折** — 一蹶不振还是迅速恢复

对每个维度判断：
- **fixed_score** (0-10): 固定型思维倾向分数，越高越固定
- **growth_score** (0-10): 成长型思维倾向分数，越高越成长
- 给出具体的证据（引用用户原话）
- 识别思维陷阱和转化建议

输出 JSON 格式：
{
  "dimensions": [
    {
      "name": "challenge_response",
      "fixed_score": 7,
      "growth_score": 3,
      "evidence": "用户说...",
      "trap": "具体的思维陷阱",
      "reframe": "转化建议"
    }
  ],
  "overall_mindset": "fixed|mixed|growth",
  "mindset_score": 65,
  "key_insight": "核心发现",
  "recommendation": "改善建议"
}""",
}


# ============================================================
# Framework 4: Impostor Syndrome (Clance + Young)
# ============================================================
IMPOSTOR_SYNDROME = {
    "id": "impostor-syndrome",
    "name": "冒名顶替综合征",
    "description": "基于 Clance IP Scale 和 Valerie Young 的5种亚型，识别冒名顶替倾向",
    "questions": [
        {
            "id": "is-1",
            "subtype": "perfectionist",
            "title": "完美主义者型",
            "question": "你对自己的标准有多高？当你做到90分的时候，你会觉得自己成功了吗，还是会想'那10分去哪了'？",
            "scoring": {
                "high": ["不够好", "还有差距", "必须完美", "90分不够", "差一点", "标准很高"],
                "low": ["满意", "够好了", "不错", "可以接受", "正常水平"]
            }
        },
        {
            "id": "is-2",
            "subtype": "superhero",
            "title": "超级英雄型",
            "question": "你是否觉得自己需要比别人付出多得多的努力，才能达到同样的水平？如果不加班/不额外努力，你会担心被淘汰吗？",
            "scoring": {
                "high": ["必须更努力", "比别人多", "不加班不行", "偷懒就被发现", "不敢休息"],
                "low": ["正常努力", "够用了", "不需要", "相信自己的能力"]
            }
        },
        {
            "id": "is-3",
            "subtype": "natural_genius",
            "title": "天才型",
            "question": "当你学一个新东西时，如果第一次没学会，你会怎么想？你会继续还是放弃？",
            "scoring": {
                "high": ["可能不适合", "没天赋", "别人一看就懂", "太笨了", "不是这块料"],
                "low": ["正常", "多练练", "需要时间", "慢慢来", "再试试"]
            }
        },
        {
            "id": "is-4",
            "subtype": "expert",
            "title": "专家型",
            "question": "在开始做一个新项目之前，你会不会觉得'我还不够了解'、'我还需要再学一些'，然后迟迟不敢开始？",
            "scoring": {
                "high": ["再准备一下", "还不够", "还差点", "需要多学", "不敢开始", "怕露馅"],
                "low": ["直接开始", "边做边学", "够了", "准备好了", "不需要完美准备"]
            }
        },
        {
            "id": "is-5",
            "subtype": "soloist",
            "title": "独行侠型",
            "question": "向别人求助对你来说容易吗？当你遇到困难时，你会主动寻求帮助，还是觉得求助等于承认自己不行？",
            "scoring": {
                "high": ["不好意思", "不能问", "别人会觉得我笨", "自己扛", "求助=不行"],
                "low": ["很正常", "随便问", "不丢人", "大家互相帮助", "能问就问"]
            }
        },
        {
            "id": "is-6",
            "subtype": "general",
            "title": "成功归因",
            "question": "当你获得一个成就（比如升职、获奖、完成一个项目），你心里是真的觉得'我做到了'，还是觉得'他们只是还没发现我不够好'？",
            "scoring": {
                "high": ["运气好", "碰巧", "别人帮的", "不是真的", "早晚被发现", "不安"],
                "low": ["我做到了", "实至名归", "努力的结果", "应该的", "高兴"]
            }
        },
    ],
    "analysis_prompt": """你是一位冒名顶替综合征（Impostor Syndrome）评估专家，基于 Clance IP Scale 和 Valerie Young 的5种亚型进行分析。

5种亚型：
1. **完美主义者** (Perfectionist) — 认为任何不完美都等于失败
2. **超级英雄** (Superhero) — 必须比所有人都努力才觉得自己不是骗子
3. **天才** (Natural Genius) — 认为如果不轻松搞定就说明没天赋
4. **专家** (Expert) — 觉得必须知道一切才能开始
5. **独行侠** (Soloist) — 认为求助等于承认无能

对每个亚型判断倾向程度（0-10分）。
识别用户的主要亚型组合。
给出具体的日常应对策略。

输出 JSON 格式：
{
  "subtypes": {
    "perfectionist": {"score": 8, "evidence": "..."},
    "superhero": {"score": 5, "evidence": "..."},
    "natural_genius": {"score": 3, "evidence": "..."},
    "expert": {"score": 7, "evidence": "..."},
    "soloist": {"score": 6, "evidence": "..."}
  },
  "overall_severity": "high|medium|low",
  "primary_patterns": ["专家型", "完美主义者型"],
  "key_insight": "核心发现",
  "coping_strategies": ["具体策略1", "具体策略2"]
}""",
}


# ============================================================
# Framework 5: Attachment Styles (Bowlby/Ainsworth)
# ============================================================
ATTACHMENT_STYLES = {
    "id": "attachment-styles",
    "name": "依恋风格评估",
    "description": "基于 Bowlby 和 Ainsworth 的依恋理论，评估成人的依恋模式及其对人际关系的影响",
    "questions": [
        {
            "id": "at-1",
            "dimension": "anxious_preoccupied",
            "title": "焦虑型倾向",
            "question": "当你给重要的人发消息，但对方很久没回复时，你脑子里会出现什么样的想法？你会怎么做？",
            "scoring": {
                "high": ["是不是不在乎我", "做错了什么", "被抛弃", "反复看手机", "焦虑", "患得患失"],
                "low": ["可能在忙", "无所谓", "不着急", "正常", "等一下再说"]
            }
        },
        {
            "id": "at-2",
            "dimension": "dismissive_avoidant",
            "title": "回避型倾向",
            "question": "当你和一个人关系变得很亲密时，你会有什么感觉？你会不自觉地做些什么来保持距离？",
            "scoring": {
                "high": ["不舒服", "窒息", "需要空间", "退缩", "保持距离", "太近了"],
                "low": ["温暖", "安全", "享受", "安心", "亲密", "自然"]
            }
        },
        {
            "id": "at-3",
            "dimension": "fearful_avoidant",
            "title": "恐惧型倾向",
            "question": "你是否有过这样的矛盾：既渴望和某人亲近，又害怕靠得太近会受伤？这种矛盾让你怎么做？",
            "scoring": {
                "high": ["矛盾", "想靠近又害怕", "推开又拉回来", "纠结", "不确定", "患得患失"],
                "low": ["没有这种矛盾", "要么靠近要么远离", "很确定", "清楚"]
            }
        },
        {
            "id": "at-4",
            "dimension": "trust_capacity",
            "title": "信任能力",
            "question": "你觉得大多数人值得信任吗？在什么情况下你会信任一个人？你有没有被人背叛后很难再信任的经历？",
            "scoring": {
                "high": ["很难信任", "被背叛过", "不相信", "防备", "试探", "保持警惕"],
                "low": ["大部分可以", "愿意信任", "给机会", "看人品", "正常"]
            }
        },
        {
            "id": "at-5",
            "dimension": "help_seeking",
            "title": "求助模式",
            "question": "当你遇到困难（工作或生活）时，你会向别人求助吗？什么让你犹豫？",
            "scoring": {
                "high": ["不愿意", "自己解决", "不想麻烦别人", "丢人", "不想欠人情"],
                "low": ["会问", "不介意", "互相帮助", "正常", "没什么"]
            }
        },
    ],
    "analysis_prompt": """你是一位依恋风格评估专家，基于 Bowlby 和 Ainsworth 的依恋理论。

四种依恋风格：
1. **安全型** (Secure) — 舒适地保持亲密和独立
2. **焦虑-痴迷型** (Anxious-Preoccupied) — 担心被抛弃，过度依赖
3. **回避-疏离型** (Dismissive-Avoidant) — 压抑依恋需求，过度独立
4. **恐惧-混乱型** (Fearful-Avoidant) — 渴望亲密但害怕受伤

评估用户的主要依恋风格及倾向程度。
分析该风格如何影响其人际关系和工作协作。
提供建立更安全依恋模式的具体建议。

输出 JSON 格式：
{
  "style_scores": {
    "secure": 6,
    "anxious_preoccupied": 7,
    "dismissive_avoidant": 3,
    "fearful_avoidant": 5
  },
  "primary_style": "anxious_preoccupied",
  "relationship_impact": "对人际关系的影响",
  "workplace_impact": "对工作协作的影响",
  "growth_suggestions": ["建议1", "建议2"]
}""",
}


# ============================================================
# Registry: All frameworks
# ============================================================
ALL_FRAMEWORKS = {
    "cognitive-distortions": CBT_DISTORTIONS,
    "eq-goleman": GOLEMAN_EQ,
    "mindset": GROWTH_MINDSET,
    "impostor-syndrome": IMPOSTOR_SYNDROME,
    "attachment-styles": ATTACHMENT_STYLES,
}

# Dimension ID to framework mapping
DIMENSION_ALIASES = {
    "distortions": "cognitive-distortions",
    "cognitive": "cognitive-distortions",
    "cbt": "cognitive-distortions",
    "eq": "eq-goleman",
    "emotional": "eq-goleman",
    "emotional-intelligence": "eq-goleman",
    "mindset": "mindset",
    "growth": "mindset",
    "fixed": "mindset",
    "impostor": "impostor-syndrome",
    "impostor-syndrome": "impostor-syndrome",
    "attachment": "attachment-styles",
    "依恋": "attachment-styles",
    "性格": "cognitive-distortions",  # default for Chinese "性格"
    "情商": "eq-goleman",
    "认知": "cognitive-distortions",
    "思维": "mindset",
}


def get_framework(dimension_id: str) -> dict:
    """Get framework by dimension ID or alias."""
    key = DIMENSION_ALIASES.get(dimension_id, dimension_id)
    return ALL_FRAMEWORKS.get(key)


def get_all_framework_ids() -> list[str]:
    """Get all valid framework IDs."""
    return list(ALL_FRAMEWORKS.keys())


def get_all_aliases() -> dict:
    """Get all dimension aliases."""
    return DIMENSION_ALIASES
