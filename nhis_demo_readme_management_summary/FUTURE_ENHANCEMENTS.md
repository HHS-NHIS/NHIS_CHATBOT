# Future Enhancements for Production Consideration

## Near-term hardening

- Lock the approved adult/child SHS source files and keyword mapping version used for the demo.
- Add a formal QC checklist for every source/mapping update.
- Review all fallback, suppression, and special-code display language.
- Review the production UI for Section 508/accessibility, mobile responsiveness, and CDC web style alignment.

## Source and data improvements

- Add controlled live Socrata refresh with row-count, column, year, and special-code validation.
- Build a richer NHIS documentation retrieval index from approved CDC/NCHS pages and PDFs.
- Add metadata cards showing source file, year range, updated date, and source URL.
- Add Teen SHS integration only after separate teen routing/crosswalks are reviewed.

## GPT/OpenAI governance and safety

- Keep deterministic estimate retrieval as the authority.
- Use GPT only for intent interpretation, follow-up handling, and answer wording from retrieved/tool output.
- Review logging, privacy, and API-key handling.
- Add explicit no-source/no-answer guardrails.
- Conduct a red-team style review for hallucination, bad fallback, and unsupported claims.

## Operations and review workflow

- Store feedback logs in a durable database/table instead of local CSV.
- Add an internal reviewer dashboard for wrong matches, missing sources, and bad wording.
- Add automated batch regression testing for keyword mappings and common user questions.
- Add deployment documentation for the selected CDC dev/production environment.

