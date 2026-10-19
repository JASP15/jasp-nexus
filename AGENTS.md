# Rules for AI contributors to JASP Nexus

Operate on feature branches and submit PRs. Do not bypass Claude/Codex permission controls, enable yolo, exfiltrate secrets, deploy, merge or alter production databases without explicit authorization.

Until adapters are implemented, Nexus only suggests routing. Never claim to have executed an agent, test, migration, browser action or Git operation that was not observed.

The --actor CLI argument is self-declared, not authenticated. It does not enforce true reviewer identity. Add real authorization and evidence verification before autonomous use.

Keep Nexus-owned task state separate from upstream CAO sessions. Follow docs/ARCHITECTURE.md and docs/SECURITY.md.

Tests: python -m unittest discover -s tests -v
