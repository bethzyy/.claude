# Three-Party Discussion Mechanism

## Overview

**参与者**: User + Agent Smith (CTO) + Dan (COO)

**目标**: 通过三方协作，做出全面、平衡的决策

---

## Activation Mechanisms

### 方式 1: Explicit Skill Calls

```
User: "@smith @dan let's discuss [topic]"
→ 同时激活 Smith 和 Dan
→ 两个 Agent 各自分析
→ 系统整合双方观点
→ User 做最终决策
```

### 方式 2: Keywords in User Message

**Smith 触发词**:
- "Smith", "CTO", "技术", "架构", "market", "business"
- "feasibility", "technical", "pricing"

**Dan 触发词**:
- "Dan", "COO", "文档", "version", "release"
- "legal", "compliance", "risk", "license"

**同时触发**:
```
User: "Smith and Dan, should we build X?"
→ Smith: Technical + Business analysis
→ Dan: Legal + Process review
→ Integrated: Full decision matrix
```

### 方式 3: Context-Based Automatic Activation

系统自动检测问题类型：

**技术问题** → 激活 Smith
**文档/版本问题** → 激活 Dan
**综合决策** → 同时激活两者

---

## Discussion Workflow

### Phase 1: Problem Statement (User)

**输入要素**:
- 问题/决策点
- 期望结果
- 约束条件（时间、预算、资源）

**示例**:
```
User: "Should we expand Job Search Suite to international markets?
       Constraints: 2-3 month timeline, limited budget"
```

### Phase 2: Smith Analysis (CTO)

**分析维度**:
1. **Technical Feasibility** (30%)
   - Can we build it?
   - Technical risks
   - Dependencies

2. **Market Opportunity** (20%)
   - Market size
   - Competition
   - Differentiation

3. **Business Viability** (15%)
   - Revenue potential
   - Cost structure
   - Unit economics

**输出格式**:
```
## Smith's Analysis

### Executive Summary
- ✅ Technical feasibility: 8/10 (APIs available)
- ✅ Market opportunity: 9/10 (blue ocean)
- ⚠️ Legal risk: 6/10 (LinkedIn scraping)

### Detailed Analysis
[Technical details...]

### Recommendation
**GO** with confidence: 75%

- Proceed with official API approach
- 2-3 month timeline realistic
- Expected ROI: 300% in 6 months
```

### Phase 3: Dan Review (COO)

**分析维度**:
1. **Legal & Compliance** (10%)
   - ToS review
   - IP protection
   - License compatibility

2. **Documentation Impact** (10%)
   - API docs update
   - User guides
   - Version control

3. **Process Requirements** (10%)
   - Release workflow
   - Testing procedures
   - Maintenance burden

**输出格式**:
```
## Dan's Review

### Legal & Compliance
⚠️ Medium Risk
- LinkedIn API requires approval (1-2 weeks)
- Scraping violates ToS (use official API)
- License compatibility: ✅ (MIT dependencies)

### Documentation & Process
- Update workload: Medium (2-3 weeks)
- Release complexity: High (new APIs)
- Maintenance burden: Medium (API changes)

### Process Requirements
- API application: Week 1-2
- Implementation: Week 3-10
- Documentation: Week 11-12
- Testing: Week 11-12

### Recommendation
**CONDITIONAL GO**

Approve IF:
- Legal review cleared
- Documentation budget allocated
- Testing plan approved
```

### Phase 4: Integration (CEO/System)

**综合评分**:
```
维度                Smith    Dan    合计
------------------------------------------
平台适配度          8/10    -      8/10
技术可行性          9/10    -      9/10
市场竞争            9/10    -      9/10
成本和难度          7/10    7/10   7/10
法律和合规风险      -       6/10   6/10

总分: 7.8/10
```

**决策建议**:
```
## Integrated Decision

### Final Score: 7.8/10

### Recommendation: ✅ GO (First Priority)

### Rationale:
- Strong technical feasibility (Smith: 9/10)
- Excellent market opportunity (Smith: 9/10)
- Acceptable legal risk (Dan: 6/10)
- Manageable documentation burden (Dan: 7/10)

### Conditions:
1. Legal clearance from LinkedIn API
2. Official API approach (no scraping)
3. Documentation budget: 2-3 weeks
4. Timeline: 2-3 months

### Action Items:
Owner          Task                          Deadline
------------------------------------------------
Smith          API application              Week 2
Smith          Technical design             Week 4
Dan            Legal review                 Week 2
Dan            Documentation plan           Week 4
Both           Implementation               Week 5-10
Dan            Release preparation          Week 11-12

### Next Steps:
1. ✅ Smith: Submit LinkedIn API application
2. ✅ Dan: Prepare legal review checklist
3. ✅ User: Approve budget allocation
```

### Phase 5: User Decision

**用户收到**:
- Smith 的技术/商业分析
- Dan 的法律/流程审查
- 系统的整合建议

**用户决定**:
- ✅ Go (批准)
- ❌ No-Go (拒绝)
- 🔄 Revise (要求修改)

---

## Interaction Patterns

### Pattern 1: Sequential Discussion

```
User → Smith (技术分析)
     ↓
User → Dan (法律审查)
     ↓
User → System (整合)
     ↓
User Decision
```

### Pattern 2: Parallel Discussion (推荐)

```
User → Smith + Dan (同时激活)
     ↓
Smith: 技术/商业分析
Dan: 法律/流程审查
     ↓
System: 整合
     ↓
User Decision
```

### Pattern 3: Iterative Discussion

```
Round 1: Smith + Dan 初步分析
    ↓
User: "What if we change X?"
    ↓
Round 2: Smith + Dan 重新评估
    ↓
User Decision
```

---

## Example Conversations

### Example 1: Project Evaluation

```
User: "@smith @dan Should we build Job Search Suite v2.0?"

## Smith's Analysis:
- Technical feasibility: 8/10
- Market opportunity: 9/10 (blue ocean!)
- Business case: Strong
- Recommendation: GO ✅

## Dan's Review:
- Legal risk: 6/10 (LinkedIn scraping)
- Documentation: Medium effort
- Process: New API integration
- Recommendation: CONDITIONAL GO ⚠️

## Integrated:
Score: 7.8/10 → GO with conditions:
1. Use official API (no scraping)
2. Legal review required
3. 2-3 month timeline

User: "Approved, proceed with Phase 1"
```

### Example 2: Legal Risk Assessment

```
User: "@smith @dan Is JobSearchTool legal?"

## Smith's Analysis:
- Technical: 9/10 (mature)
- Market: 8/10 (blue ocean)
- Revenue: Good potential
- BUT: High legal risk

## Dan's Review:
- Scraping ToS: 🔴 VIOLATION
- Platform ban risk: 🔴 HIGH
- Legal exposure: 🔴 LAWSUIT POSSIBLE
- Recommendation: NO-GO 🚫

## Integrated:
Score: 4.5/10 → NO-GO
One-vote veto: Legal risk (2/10)

User: "Understood, let's shelve it"
```

### Example 3: Pricing Strategy

```
User: "@smith @dan What pricing for image-gen?"

## Smith's Analysis:
- Market: 71 competitors (red ocean)
- Differentiation: 8-level fallback
- Pricing data: $0.01-0.50/image
- Recommendation: $0.02-0.05 (premium pricing)

## Dan's Review:
- Cost tracking: Usage-based required
- Documentation: API pricing page
- Legal: No issues (vendor APIs)
- Process: Implement metering

## Integrated:
Pricing: $0.02-0.05/image
- Competitive positioning: "Most Stable"
- Tiered pricing available
- Usage-based billing required

User: "Sounds good, proceed"
```

---

## Technical Implementation

### Agent Activation

```python
def activate_agents(user_message):
    agents = []

    # Check Smith triggers
    if has_smith_trigger(user_message):
        agents.append('smith')

    # Check Dan triggers
    if has_dan_trigger(user_message):
        agents.append('dan')

    # Check for explicit multi-agent call
    if '@smith' in user_message and '@dan' in user_message:
        agents = ['smith', 'dan']

    return agents

def has_smith_trigger(message):
    triggers = [
        'smith', 'cto', 'technical', 'architecture',
        'market', 'business', 'feasibility', 'pricing'
    ]
    return any(t in message.lower() for t in triggers)

def has_dan_trigger(message):
    triggers = [
        'dan', 'coo', 'documentation', 'version',
        'release', 'legal', 'compliance', 'risk'
    ]
    return any(t in message.lower() for t in triggers)
```

### Response Integration

```python
def integrate_responses(smith_response, dan_response):
    # Extract scores
    smith_scores = smith_response['scores']
    dan_scores = dan_response['scores']

    # Combine scores
    combined = {
        'technical': smith_scores['technical'],
        'market': smith_scores['market'],
        'legal': dan_scores['legal'],
        'docs': dan_scores['documentation']
    }

    # Calculate final score
    final_score = calculate_weighted_score(combined)

    # Generate recommendation
    if final_score >= 7.5:
        recommendation = 'GO'
    elif final_score >= 6.5:
        recommendation = 'CONDITIONAL GO'
    else:
        recommendation = 'NO-GO'

    return {
        'final_score': final_score,
        'recommendation': recommendation,
        'smith_analysis': smith_response,
        'dan_review': dan_response,
        'action_items': generate_action_items(smith_response, dan_response)
    }
```

---

## Output Format

### Standard Three-Party Discussion Output

```markdown
# Three-Party Discussion: [Topic]

**Participants**: User, Agent Smith (CTO), Dan (COO)
**Date**: 2026-03-06

---

## Agent Smith's Analysis (CTO)

### Technical Feasibility
**Score**: 8/10

[Technical analysis...]

### Market Opportunity
**Score**: 9/10

[Market analysis...]

### Recommendation
**GO** ✅ (confidence: 80%)

---

## Dan's Review (COO)

### Legal & Compliance
**Score**: 6/10

[Legal analysis...]

### Documentation & Process
**Score**: 7/10

[Process analysis...]

### Recommendation
**CONDITIONAL GO** ⚠️

---

## Integrated Decision

### Final Score: 7.8/10

### Recommendation: ✅ GO (First Priority)

### Rationale:
- Strong technical case (Smith: 8/10)
- Excellent market (Smith: 9/10)
- Acceptable legal risk (Dan: 6/10)
- Manageable process (Dan: 7/10)

### Conditions:
1. [Condition 1]
2. [Condition 2]

### Action Items:
| Owner | Task | Deadline |
|-------|------|----------|
| Smith | [Task] | [Date] |
| Dan | [Task] | [Date] |

---

## User Decision: [APPROVED / REJECTED / REVISE]
```

---

## Benefits

1. **全面性**: 技术 + 商业 + 法律 + 流程，360 度评估
2. **客观性**: 数据驱动，减少偏见
3. **效率**: 并行分析，快速决策
4. **可追溯**: 完整记录决策过程
5. **可扩展**: 轻松添加新的 Agent

---

**最后更新**: 2026-03-06
**维护者**: MyAIProduct Team
