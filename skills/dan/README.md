# Dan - Business Analysis Expert (COO)

**Version**: 1.0.0
**Role**: Chief Operating Officer
**Team**: MyAIProduct

## Quick Start

```bash
# Market analysis
python dan.py --market "job search tool"

# Pricing strategy
python dan.py --pricing "Job Match Tool" --cost 5

# Revenue projection
python dan.py --revenue "Job Match Tool" --price 39

# Full analysis
python dan.py --analyze "Job Match Tool" --price 39 --cost 5
```

## Capabilities

### 1. Market Research
- Search and analyze market landscape
- Identify competitors
- Assess market size

### 2. Pricing Strategy
- Analyze competitor pricing
- Recommend optimal pricing
- Design pricing tiers

### 3. Revenue Projection
- Forecast revenue scenarios
- Calculate platform fees
- Estimate net revenue

### 4. Business Analysis
- Product-market fit assessment
- Competitive positioning
- Revenue model design

## Team Structure

```
董事长 (您)
    ↓
CEO (主系统) ← 协调者
    ↓
    ├── Dan (COO) - 商业/市场 ← 我
    └── Smith (CTO) - 技术
```

## Usage Examples

### Example 1: Market Analysis
```bash
python dan.py --market "AI image generation tools"
```

Output:
- Market size
- Key competitors
- Market position

### Example 2: Pricing Strategy
```bash
python dan.py --pricing "Job Match Tool" --cost 5
```

Output:
- Minimum price
- Standard price
- Premium price
- Pricing models

### Example 3: Revenue Projection
```bash
python dan.py --revenue "Job Match Tool" --price 39
```

Output:
- Conservative scenario
- Realistic scenario
- Optimistic scenario

### Example 4: Full Analysis
```bash
python dan.py --analyze "Job Match Tool" --price 39 --cost 5
```

Output:
- Market analysis
- Pricing strategy
- Revenue projection

## Outputs

Dan generates formatted reports in:

### Markdown Format (default)
```markdown
# Pricing Strategy Report

## Product
Job Match Tool

## Recommended Pricing
- Minimum: $16.67
- Standard: $25.00
- Premium: $41.67
```

### JSON Format
```json
{
  "product": "Job Match Tool",
  "recommended_pricing": {
    "minimum": 16.67,
    "standard": 25.00,
    "premium": 41.67
  }
}
```

## Integration with Smith

Dan works alongside Smith (CTO):

**Example workflow:**
```
You: "Should we build Job Search Suite v2?"

Dan (COO):
  - Market analysis: ✓ Blue ocean
  - Pricing: $49 bundle
  - Revenue: $784-1960/month

Smith (CTO):
  - Technical feasibility: ✓ 2-3 months
  - Architecture: LinkedIn/Indeed API
  - Risk: Low (official APIs)

CEO (main system):
  - Integrates reports
  - Presents to Chairman (You)

You: "Approved, proceed"
```

## Files

- `dan.py` - Main implementation
- `.skill/SKILL.md` - Skill definition
- `prompts/` - Prompt templates
- `README.md` - This file

## Version History

- **v1.0.0** (2026-03-06): Initial release
  - Market research
  - Pricing strategy
  - Revenue projection

## Maintainer

MyAIProduct Team
