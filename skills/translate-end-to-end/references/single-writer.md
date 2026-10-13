# Single-writer publication

1. Only the parent writes official manuscripts, decisions, glossaries, manifests
   or state. Serialize controller commands and publications across chapters.
   Workers receive read-only inputs and unique NEW candidate/report paths.
2. Before dispatch, record SHA-256 of source, target (null if absent) and context.
   Preserve a baseline copy. Assign `candidate.md` and `translation.md`. For a
   correction, record approved zero-based nonempty block indices; every other
   block must remain unchanged. Preserve semantic paragraph separators.
   A parent-produced mechanical candidate follows the same contract. First record
   approved issue IDs, exact before/after text, block indices and expected match
   counts; reject stale input, missing/ambiguous matches or cascading replacements.
   Save a NEW candidate and handoff, never apply replacements directly to the
   official manuscript. Semantic choices still require the selected translator.
3. Validate the persisted candidate, hash it, and save a unique publication spec
   beside its Markdown handoff. Baseline hashes must come from BEFORE dispatch:

   ```json
   {
     "source": {"path": "/absolute/source.md", "sha256": "source hash"},
     "target": {"path": "/absolute/manuscript.md", "sha256": "baseline hash"},
     "candidate": {"path": "/absolute/candidate.md", "sha256": "candidate hash"},
     "context": [{"path": "/absolute/glossary.md", "sha256": "dispatch hash"}],
     "allowed_blocks": [12, 13, 14]
   }
   ```

   Use JSON null for an absent target. Omit `allowed_blocks` only for an approved
   whole-chapter draft/revision. Never overwrite a previous spec or candidate.
4. Parent runs `python3 "$SCRIPTS/publish_candidate.py" --spec <spec.json>`, saves
   the receipt, and immediately runs controller `next`. Publication is not quality
   approval. A mismatch blocks publication: never refresh hashes just to accept
   a stale candidate. Reconcile newer changes into another candidate instead.
5. The publisher uses an advisory per-target lock and atomic replacement. This
   coordinates cooperating publishers, not arbitrary editors. Do not force-save
   dirty buffers. Resolve any editor/disk disagreement before publication. Hash
   checking is not protection against every uncooperative concurrent write.
6. Track confirmed issue IDs and resolutions in the chapter report. After a
   controller restoration, verify that known defects did not return. Preserve
   attempts and decisions; never reset history to obtain a clean result. Equal
   rank with a non-lower score retains the latest judged attempt, but a worse
   result still restores the best-ranked attempt and requires reconciliation.