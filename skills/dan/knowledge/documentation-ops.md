# Dan - Documentation & Operations Knowledge Base

## Documentation Management

### MkDocs Documentation Site

**Location**: `C:\D\CAIE_tool\MyAIProduct\docs-site\`

**Structure**:
```
docs-site/
├── mkdocs.yml              # Configuration
├── docs/
│   ├── index.md           # Homepage
│   ├── projects/          # Project documentation
│   ├── skills/            # Skill system docs
│   ├── company/           # Company knowledge base
│   └── reference/         # Reference materials
└── site/                  # Generated static site
```

**Commands**:
```bash
# Start development server
mkdocs serve

# Build production site
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy
```

**Features**:
- Chinese language support
- Full-text search (zh + en)
- Dark/light mode toggle
- Responsive design
- Git integration (revision dates)

### API Documentation Sync

**Workflow**:
1. Code changes → Smith updates code
2. Dan scans code for API changes
3. Auto-generates API documentation
4. Updates MkDocs site
5. Commits to Git

**Tools**:
- `sphinx` - Python API docs
- `mkdocs-material` - Site theme
- `mkdocs-git-revision-date-plugin` - Revision tracking

## Version Control

### Git Workflow

**Branching Strategy**:
- `main` - Production releases
- `develop` - Integration branch
- `feature/*` - Feature branches
- `hotfix/*` - Emergency fixes

**Tagging Convention**:
```
v<MAJOR>.<MINOR>.<PATCH>

Examples:
- v1.0.0 - Initial release
- v2.1.5 - Bugfix release
- v3.0.0 - Major version
```

### Release Process

**Pre-Release**:
1. Update version in code
2. Update CHANGELOG.md
3. Create Git tag
4. Run full test suite

**Release**:
1. Create GitHub Release
2. Upload EXE/artifacts
3. Update MkDocs docs
4. Deploy to production

**Post-Release**:
1. Monitor for bugs
2. Collect user feedback
3. Plan next iteration

### CHANGELOG Format

```markdown
## [Unreleased]

### Added
- New feature 1
- New feature 2

### Changed
- Updated feature 1

### Fixed
- Bug fix 1

## [1.2.3] - 2026-03-06

### Added
- ...
```

## Legal & Risk Management

### Risk Assessment Framework

**Scraping Legality**:
- ✅ Check platform ToS
- ✅ Verify robots.txt
- ✅ Respect rate limits
- ✅ Add user-agent identification
- ⚠️ Consider legal precedents

**IP Protection**:
- ✅ Patent search (USPTO, Google Patents)
- ✅ Trademark check (USPTO TESS)
- ✅ Copyright clearance
- ✅ License compatibility review

**Privacy Compliance**:
- ✅ GDPR compliance (EU users)
- ✅ CCPA compliance (California users)
- ✅ Data minimization
- ✅ User consent management
- ✅ Right to deletion

**Open Source Licenses**:
- ✅ MIT - Permissive, compatible
- ✅ Apache 2.0 - Patent protection
- ⚠️ GPL - Copyleft, viral
- ❌ Proprietary - Avoid dependencies

### Project Risk Ratings

**JobSearchTool**: 🔴 High Risk
- Scraping violates platform ToS
- Potential legal action
- Recommendation: Refactor to official API

**jobMatchTool**: 🟡 Medium Risk
- LinkedIn scraping ToS risk
- Mitigation: Use official API
- Current status: Acceptable (China-only)

**image-gen**: 🟢 Low Risk
- AI-generated content (no copyright)
- API licensing (vendor responsibility)
- Safe to deploy

**gethtml**: 🔴 High Risk
- Copyrighted content downloading
- Potential ToS violations
- Recommendation: Open source with disclaimers

## Process Management

### Development Workflow

**1. Planning Phase**:
- Requirements gathering (User + Smith)
- Technical feasibility (Smith)
- Legal review (Dan)
- Resource estimation (Both)

**2. Development Phase**:
- Architecture design (Smith)
- Implementation (Smith)
- Documentation draft (Dan)
- Code review (Both)

**3. Testing Phase**:
- Unit tests (Smith)
- Integration tests (Smith)
- Legal compliance check (Dan)
- Documentation review (Dan)

**4. Release Phase**:
- Version tagging (Dan)
- CHANGELOG update (Dan)
- GitHub Release (Dan)
- Documentation sync (Dan)

### Document Maintenance

**Company Knowledge Base** (`docs-site/docs/company/`):

- **history.md**: Development milestones
- **processes.md**: Standard workflows
- **policies.md**: Company policies
- **decisions.md**: Decision records
- **startup-best-practices.md**: Management lessons

**Update Frequency**:
- history.md: After major milestones
- processes.md: Quarterly review
- policies.md: As needed
- decisions.md: After every major decision

### Quality Checklists

**Pre-Release Checklist**:
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Legal review completed
- [ ] Security scan passed
- [ ] Version tagged
- [ ] GitHub Release created
- [ ] MkDocs site built

**Legal Compliance Checklist**:
- [ ] ToS reviewed
- [ ] Licenses compatible
- [ ] IP clearance done
- [ ] Privacy compliance checked
- [ ] Disclaimers added
- [ ] User agreements updated

## Task Coordination

### Progress Tracking

**Tools**:
- TaskCreate/TaskUpdate/TaskList (Claude Code)
- Project boards (GitHub Projects)
- Milestone tracking

**Status Definitions**:
- `pending`: Not started
- `in_progress`: Actively working
- `completed`: Finished
- `blocked`: Waiting on dependencies
- `deleted`: Cancelled

### Meeting Workflow

**Three-Party Discussion** (User + Smith + Dan):

1. **User Presents Problem**
   - Clear problem statement
   - Desired outcome
   - Constraints

2. **Smith Analysis** (CTO)
   - Technical feasibility
   - Market research
   - Business analysis
   - Recommendations

3. **Dan Review** (COO)
   - Documentation impact
   - Version control implications
   - Legal compliance
   - Process requirements

4. **Integrated Decision**
   - Synthesize both perspectives
   - Weigh trade-offs
   - Make go/no-go decision
   - Assign action items

5. **Follow-Up**
   - Track progress
   - Review outcomes
   - Update documentation

---

**最后更新**: 2026-03-06
**维护者**: Dan (COO)
