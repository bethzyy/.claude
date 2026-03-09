# Three-Party Discussion System - Quick Start Guide

## What is This?

A collaborative decision-making system where:
- **You (CEO/User)**: Make final decisions
- **Agent Smith (CTO)**: Technical and business analysis
- **Dan (COO)**: Documentation, legal, and process review

---

## How to Use

### Method 1: Explicit Multi-Agent Call

```
User: "@smith @dan Should we expand Job Search Suite to international markets?"
```

**Result**:
- Smith analyzes technical feasibility and market opportunity
- Dan reviews legal compliance and documentation impact
- System integrates both perspectives
- You make the final decision

### Method 2: Topic-Based Activation

**Technical/Business Questions** → Smith activates automatically:
```
User: "What's the market size for AI image generators?"
→ Smith: Provides market research data
```

**Documentation/Legal Questions** → Dan activates automatically:
```
User: "Update the documentation for jobMatchTool v2.5"
→ Dan: Updates docs, creates Git tag, updates CHANGELOG
```

**Complex Decisions** → Both activate:
```
User: "Should we build X? Consider technical, market, and legal aspects."
→ Smith + Dan: Full analysis
```

### Method 3: Sequential Discussion

```
User: "@smith What's the technical feasibility of X?"
Smith: [Technical analysis]

User: "@dan What's the legal risk?"
Dan: [Legal review]

User: "Integrate both and give me a recommendation"
System: [Integrated decision matrix]
```

---

## Example Conversations

### Example 1: Project Evaluation

```
User: "@smith @dan Should we build Job Search Suite v2.0 for international markets?"

=== Agent Smith's Analysis (CTO) ===

Technical Feasibility: 8/10
- LinkedIn/Indeed APIs available
- 2-3 month timeline realistic
- GLM-4.6 integration proven

Market Opportunity: 9/10
- Blue ocean (0 competitors in MuleRun)
- Global market (5x China market)
- Strong demand from job seekers

Recommendation: GO ✅ (confidence: 85%)

=== Dan's Review (COO) ===

Legal & Compliance: 6/10
- LinkedIn API requires approval (1-2 weeks)
- Scraping violates ToS → use official API
- License compatibility: ✅

Documentation & Process: 7/10
- API docs update: 2 weeks
- User guides: 1 week
- Release process: Standard

Recommendation: CONDITIONAL GO ⚠️

Conditions:
1. LinkedIn API approval obtained
2. Official API approach only (no scraping)
3. Documentation budget allocated

=== Integrated Decision ===

Final Score: 7.8/10
Recommendation: ✅ GO (First Priority)

Action Items:
- Smith: Submit LinkedIn API application (Week 1)
- Dan: Prepare legal review checklist (Week 1)
- Smith: Technical architecture design (Week 2-4)
- Dan: Documentation plan (Week 4)
- Both: Implementation (Week 5-10)

=== User Decision ===
User: "Approved, proceed with Phase 1"
```

### Example 2: Legal Risk Assessment

```
User: "@smith @dan Is JobSearchTool (scraping) legal to deploy?"

=== Agent Smith's Analysis (CTO) ===

Technical: 9/10 (mature, v1.5.5)
Market: 8/10 (blue ocean)
Business: Good revenue potential

BUT: High legal risk acknowledged

Recommendation: TECHNICALLY FEASIBLE but legally risky

=== Dan's Review (COO) ===

Legal Risk: 2/10 🔴 CRITICAL

Issues:
- Scraping violates招聘平台 ToS
- Potential platform ban (IP blocked)
- Possible legal action (C&D, lawsuit)
- Jurisdiction risks (China + international)

Recommendation: NO-GO 🚫

One-vote veto triggered: Legal risk below threshold

=== Integrated Decision ===

Final Score: 4.5/10
Recommendation: 🚫 NO-GO (High Legal Risk)

Options:
1. Shelve project
2. Refactor to official APIs (costly)
3. Open source with disclaimers (limited liability)

=== User Decision ===
User: "Understood, let's shelve JobSearchTool"
```

### Example 3: Pricing Strategy

```
User: "@smith @dan What pricing strategy for image-gen?"

=== Agent Smith's Analysis (CTO) ===

Market Analysis:
- 71 competitors (50% of all MuleRun agents)
- Price range: $0.01-0.50/image
- Red ocean competition

Differentiation:
- 8-level fallback (98-99% reliability)
- "The Most Stable AI Image Generator"

Pricing Recommendation:
- Premium pricing: $0.02-0.05/image
- Subscription tier: $9.99-29.99/month
- Free tier: 10 images/month (lead generation)

Recommendation: Premium pricing due to technical advantage

=== Dan's Review (COO) ===

Cost Tracking:
- Usage-based billing required
- Implement metering system
- Cost per image: $0.008-0.015

Documentation:
- API pricing page required
- Usage dashboard needed
- Billing FAQ required

Legal:
- No issues (vendor APIs)
- Terms of service for pricing

Process:
- Standard release process
- Monitoring cost per user

Recommendation: APPROVED

=== Integrated Decision ===

Pricing Strategy:
- Pay-per-use: $0.02-0.05/image
- Monthly subscription: $9.99 (500 images) to $29.99 (2000 images)
- Free tier: 10 images/month

Positioning: Premium reliability at competitive prices

=== User Decision ===
User: "Approved, implement this pricing"
```

---

## Agent Capabilities

### Agent Smith (CTO)

**Responsibilities**:
- ✅ Technical architecture and design
- ✅ Market research and competitive analysis
- ✅ Business modeling and pricing strategy
- ✅ Information gathering and intelligence
- ✅ Project evaluation and prioritization

**Trigger Words**:
- "Smith", "CTO", "technical", "architecture"
- "market", "business", "feasibility"
- "pricing", "competition", "research"

### Dan (COO)

**Responsibilities**:
- ✅ Documentation management (MkDocs, API docs)
- ✅ Version control (Git tags, CHANGELOG)
- ✅ Process management (workflows, policies)
- ✅ Legal compliance (licenses, IP, privacy)
- ✅ Risk assessment (ToS, scraping, GDPR)

**Trigger Words**:
- "Dan", "COO", "documentation", "version"
- "release", "legal", "compliance", "risk"
- "license", "process", "policy"

---

## Decision Framework

### Scoring System

**Total Score** = Weighted sum of 5 dimensions:

| Dimension | Weight | Assessed By |
|-----------|--------|-------------|
| Platform Compatibility | 30% | Smith |
| Technical Feasibility | 30% | Smith |
| Market Competition | 20% | Smith |
| Cost & Difficulty | 10% | Dan |
| Legal & Compliance Risk | 10% | Dan |

**Priority Levels**:
- 🔥 **First Priority** (7.5+): Execute immediately
- 🌟 **Second Priority** (6.5-7.4): Plan for next phase
- 💡 **Observation** (5.5-6.4): Monitor market
- 🚫 **Not Recommended** (<5.5): Don't pursue

### One-Vote Veto

**Legal Risk** acts as one-vote veto:
- If legal risk < 5/10 → Automatic NO-GO
- Regardless of other scores

**Examples**:
- JobSearchTool: Legal 2/10 → NO-GO (final score: 4.5/10)
- jobMatchTool: Legal 6/10 → GO (final score: 7.6/10)

---

## Best Practices

### 1. Be Clear About Your Question

❌ Bad: "What do you think about X?"
✅ Good: "@smith @dan Should we build X? Consider technical feasibility, market opportunity, and legal risks."

### 2. Provide Context

❌ Bad: "Pricing for image-gen?"
✅ Good: "@smith @dan What pricing strategy for image-gen? Consider: 71 competitors (red ocean), our 8-level fallback advantage, cost per image is $0.008-0.015"

### 3. Specify Constraints

❌ Bad: "Can we build X?"
✅ Good: "@smith @dan Can we build X in 2 months with budget $5k? Consider technical and legal aspects."

### 4. Ask for Integrated Decision

❌ Bad: "@smith @dan [complex question]"
✅ Good: "@smith @dan [question]. Please provide analysis and then give me an integrated recommendation with action items."

---

## Common Workflows

### Workflow 1: New Project Evaluation

```
1. User: "@smith @dan Should we build [project]?"
2. Smith: Technical + Market analysis
3. Dan: Legal + Process review
4. System: Integrated score + recommendation
5. User: Go/No-Go decision
6. If Go: Assign action items to Smith and Dan
```

### Workflow 2: Risk Assessment

```
1. User: "@smith @dan What are the risks of [project]?"
2. Smith: Technical risks
3. Dan: Legal + Process risks
4. System: Integrated risk matrix
5. User: Accept/Mitigate/Reject
```

### Workflow 3: Pricing Strategy

```
1. User: "@smith @dan Pricing for [product]?"
2. Smith: Market + Competitor analysis
3. Dan: Cost structure + billing implementation
4. System: Recommended pricing tiers
5. User: Approve/Adjust
```

### Workflow 4: Legal Compliance Check

```
1. User: "@smith @dan Is [project] legal?"
2. Smith: Technical feasibility
3. Dan: Legal review (ToS, licenses, IP)
4. System: Compliance report
5. User: Proceed/Modify/Shelve
```

---

## Troubleshooting

### Issue: Only One Agent Responds

**Cause**: Question only triggers one agent

**Solution**: Use explicit multi-agent call:
```
User: "@smith @dan [question]"
```

### Issue: No Agent Responds

**Cause**: Question doesn't match any trigger patterns

**Solution**: Be more specific:
```
User: "@smith [technical question]" or "@dan [documentation question]"
```

### Issue: Conflicting Recommendations

**Cause**: Smith says GO, Dan says NO-GO

**Solution**: System provides integrated score with conditions:
```
User: "@smith @dan [complex question]"
System: "CONDITIONAL GO - Address Dan's legal concerns first"
```

---

## Advanced Usage

### Custom Agent Behavior

You can customize agent behavior by updating their knowledge bases:

- **Smith**: `.claude/skills/agent-smith/knowledge/projects.md`
- **Dan**: `.claude/skills/dan/knowledge/documentation-ops.md`

### Adding New Agents

The system is extensible. To add a new agent (e.g., CFO):

1. Create new skill directory: `.claude/skills/agent-cfo/`
2. Define capabilities in `.skill/SKILL.md`
3. Add knowledge base files
4. Update integration logic to include new agent

### Exporting Discussions

All discussions are automatically logged and can be exported for documentation:

```
User: "@dan Export the last discussion to MkDocs"
Dan: Creates discussion log in docs-site/docs/company/decisions.md
```

---

**Version**: 1.0.0
**Last Updated**: 2026-03-06
**Maintainer**: MyAIProduct Team
