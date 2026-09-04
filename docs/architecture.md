# AI-Powered Border Checkpoint & Travel Document Verification Platform
## Complete System Architecture Documentation — Smart India Hackathon

---

## 1. Project Overview

### What the system does
The platform assists immigration/security officers at border checkpoints by automatically extracting, validating, and cross-checking information from travel documents (passports, visas, IDs), analyzing them for tampering, and comparing the document photo against the traveler's face. It produces a transparent, evidence-backed **risk assessment** rather than a verdict, and an officer makes the final decision.

### Problem it solves
Manual verification is slow, inconsistent, and heavily dependent on officer experience. High passenger volumes create pressure to rush checks, increasing the chance that forged, altered, or expired documents pass through, or that genuine travelers are needlessly delayed.

### Target users
- **Immigration/Security Officers** (primary users, frontline decision-makers)
- **Supervisors** (oversight, escalations, analytics)
- **System Administrators** (checkpoint/user/rule configuration)

### Primary use cases
1. Routine passport/visa check at a checkpoint counter.
2. Secondary manual verification for flagged travelers.
3. Supervisor review of high-risk or overridden cases.
4. Post-incident audit and investigation.

### System philosophy
```
Capture → Extract → Validate → Compare → Analyze → Explain → Review → Audit
```
Every stage produces evidence that is preserved and shown to the officer — nothing is a black box.

### Major capabilities
OCR + MRZ extraction, document validation, tamper detection, face verification, database cross-checks, identity-consistency checks, explainable risk scoring, officer review workflow, full audit trail.

### Why AI is necessary
Humans cannot reliably detect sub-pixel image manipulation, checksum mismatches, or cross-reference thousands of watchlist records in seconds. AI narrows a large search space to the few things that need human judgment.

### Why human-in-the-loop is necessary
Legal, ethical, and due-process reasons: decisions about a person's entry/travel status carry serious consequences. AI errors (false positives/negatives) are inevitable; a trained officer with authority and accountability must make the final call. This also builds public trust and provides a legally defensible decision trail.

### Automation vs. AI-assisted decision support
| Automation | AI-Assisted Decision Support (this system) |
|---|---|
| System acts and decides | System analyzes and recommends |
| No human judgment in the loop | Officer reviews evidence before deciding |
| Errors become final actions | Errors surface as "needs review" |
| Appropriate for low-stakes, reversible tasks | Appropriate for high-stakes identity decisions |

### How this improves traditional verification
Reduces average verification time, standardizes checks across officers/checkpoints, catches subtle tampering humans miss, and creates a consistent audit record — while keeping legal accountability with the human officer.

---

## 2. System Architecture

### High-level style
A **modular monolith** for the SIH build: one deployable backend with clearly separated modules (auth, verification, AI orchestration, risk engine, audit) that can be extracted into services later if scale demands it. Avoids premature microservice complexity while keeping clean boundaries.

### Frontend (Next.js 15, App Router, TypeScript)
**Structure**
```
app/
  (auth)/login
  (dashboard)/checkpoint-select
  (dashboard)/officer/dashboard
  (dashboard)/verification/new
  (dashboard)/verification/[sessionId]
  (dashboard)/supervisor/analytics
  (dashboard)/admin/*
  (dashboard)/audit-logs
```
- **State management:** TanStack Query for server state (verification sessions, results) + lightweight React context for UI-only state (active checkpoint, theme). Avoid a heavy global store — most state is server-derived.
- **API communication:** Typed API client with Zod schema validation on responses; React Hook Form + Zod for all input forms (document metadata, manual overrides).
- **File upload pipeline:** Client compresses/validates image (type, size, dimensions) → requests a **signed upload URL** from backend → uploads directly to object storage → backend is notified via a completion callback → processing begins server-side. This avoids routing large binaries through the app server unnecessarily.
- **Dashboard architecture:** Officer dashboard shows active/recent sessions; verification detail page is a single evidence-centric view (document viewer, OCR panel, risk card, decision panel) rather than scattered tabs — officers should see everything needed on one screen.

### Backend (Python, FastAPI)
- **API layer:** Versioned REST API (`/api/v1/...`), grouped by domain (auth, travelers, documents, verification, risk, audit).
- **Authentication:** Supabase Auth (or enterprise SSO/OIDC for production) issuing short-lived JWTs; refresh handled server-side.
- **Authorization:** RBAC middleware checked per-route; Postgres Row-Level Security as a second enforcement layer (defense in depth).
- **Verification service:** Orchestrates the full pipeline for a session, calls AI services, aggregates evidence, calls risk engine.
- **AI services:** Isolated internal modules (OCR, MRZ, tamper detection, face verification) — callable synchronously for fast checks, asynchronously (background workers) for heavier inference.
- **Risk engine:** Pure, deterministic, explainable scoring function operating on structured evidence — see Section 5.
- **Database layer:** PostgreSQL via an ORM (SQLAlchemy) with migrations (Alembic).
- **File storage:** Object storage (S3-compatible / Supabase Storage) for document images, with signed URLs and short expiry, never public buckets.
- **Background processing:** Redis-backed task queue (e.g., Celery/RQ) for face embedding generation, tamper analysis, and any GPU-bound inference.

### AI pipeline
```
Document Image
   ↓ Preprocessing (deskew, crop, denoise)
   ↓ Document Classification (passport / visa / ID / unknown)
   ↓ OCR
   ↓ MRZ Detection & Parsing
   ↓ Field Extraction & Checksum Validation
   ↓ Database Lookup (demo or authorized source)
   ↓ Image Tamper Analysis
   ↓ Face Detection → Alignment → Embedding → Similarity
   ↓ Identity Consistency Check
   ↓ Risk Engine
   ↓ Explainable Result → Officer
```

### Synchronous vs. asynchronous processing
- **Synchronous (target <2–3s):** document classification, OCR, MRZ parsing, checksum validation, database lookup — officer needs these immediately to keep the counter moving.
- **Asynchronous (background, results streamed/polled):** face embedding + tamper analysis (more compute-heavy), especially under load or on CPU-only demo hardware. The UI shows a "analyzing…" state and updates live; the officer is never blocked, but also never shown a final risk score until these complete.

---

## 3. Database Design (Conceptual — No SQL)

### Core entities and relationships

**users** — id, email, password/auth ref, full_name, role_id (FK→roles), checkpoint_id (nullable FK), is_active, created_at, updated_at.

**roles** — id, name (officer/supervisor/admin), permissions (structured), created_at.

**checkpoints** — id, name, location, type (airport/land/sea), is_active, created_at.

**travelers** — id, full_name, date_of_birth, nationality, gender, created_at. (Minimal PII; no biometric data stored here.)

**documents** — id, traveler_id (FK, nullable until matched), document_type_id (FK), document_number (encrypted), issuing_country, issue_date, expiry_date, status (valid/expired/revoked/blacklisted — demo only), created_at.

**document_types** — id, name (passport/visa/national_id), template_reference, created_at.

**document_images** — id, document_id (FK), storage_path (never raw bytes in DB), image_type (front/photo_page/visa_page), checksum_hash, uploaded_at, retention_expires_at.

**ocr_results** — id, document_image_id (FK), extracted_fields (structured JSON), confidence_score, engine_used, created_at.

**mrz_results** — id, document_image_id (FK), raw_mrz_lines, parsed_fields, checksum_valid (bool), created_at.

**verification_sessions** — id, officer_id (FK), checkpoint_id (FK), traveler_id (nullable FK), status (in_progress/completed/escalated), started_at, completed_at.

**verification_checks** — id, session_id (FK), check_type (ocr/mrz/db_lookup/face/tamper), status, confidence, details (JSON), created_at. (One row per pipeline stage — this *is* the audit chain.)

**face_verification_results** — id, session_id (FK), similarity_score, threshold_used, match_result (bool), confidence, created_at. (Stores score/result only — see Section 4 on embedding storage policy.)

**tamper_analysis_results** — id, session_id (FK), regions_flagged (JSON), anomaly_score, indicators (JSON: font inconsistency, compression anomaly, copy-paste region, etc.), created_at.

**watchlist_records** *(demo/synthetic only)* — id, document_number_hash, reason_code, added_at.

**risk_assessments** — id, session_id (FK), total_score, risk_level (low/medium/high/critical), created_at.

**risk_factors** — id, risk_assessment_id (FK), factor_name, weight_applied, description, created_at. (Row per contributing factor — enables the itemized explanation UI.)

**verification_decisions** — id, session_id (FK), officer_id (FK), decision (approved/referred/rejected), override_reason (nullable), decided_at.

**audit_logs** — id, actor_id, action, entity_type, entity_id, metadata (JSON), ip_address, created_at. (Append-only, immutable.)

### Design notes
- Foreign keys enforce referential integrity between sessions → checks → risk factors → decisions.
- Unique constraints on (document_number, issuing_country) in demo data to prevent duplicate synthetic identities.
- Indexes on session status, checkpoint_id, created_at (for dashboard queries and audit search).
- `document_images.retention_expires_at` supports automated purging (Section 14).
- All PII-bearing columns (document_number, DOB, name) are candidates for column-level encryption; biometric data is never stored as raw images tied to identity long-term — see Section 4.

---

## 4. AI Architecture

### 4.1 OCR
- **Purpose:** Extract printed text fields (name, DOB, document number, dates) from the document.
- **Input:** Preprocessed document image (cropped, deskewed).
- **Output:** Structured field map + per-field confidence.
- **Model type:** PaddleOCR (recommended) — strong multilingual accuracy, good performance on structured documents, runs on CPU acceptably for demo scale. Tesseract as a lightweight fallback.
- **Training data:** Pretrained; fine-tuning optional using synthetic passport templates if time allows.
- **Inference:** Local (in-process or same-host worker) — avoids sending document images to third-party APIs, which is a privacy requirement here.
- **Confidence:** Per-field OCR confidence surfaced directly to officer; low-confidence fields are flagged, not silently accepted.
- **Failure cases:** Glare, blur, non-standard fonts, damaged documents → falls back to manual data entry by officer, session continues with a "manual entry" flag.

### 4.2 MRZ Detection & Validation
- **Purpose:** Locate and parse the Machine-Readable Zone, validate against ICAO 9303 checksum rules.
- **Input:** Document image (bottom region).
- **Output:** Parsed MRZ fields + boolean checksum validity per field (document number, DOB, expiry, composite).
- **Model/approach:** Rule-based MRZ line detection (OpenCV region heuristics) + a lightweight OCR pass tuned for OCR-B font, followed by deterministic checksum algorithms (no ML needed here — this is exact arithmetic).
- **Explainability:** Naturally explainable — checksum either matches or doesn't, and which field failed is directly reportable.
- **Failure cases:** Damaged/obscured MRZ → flagged as "MRZ unreadable," treated as a risk factor, not a hard failure.

### 4.3 Document Classification
- **Purpose:** Determine document type (passport/visa/ID) and, ideally, issuing-country template.
- **Model type:** A small CNN or fine-tuned Vision Transformer classifier (or even a simpler approach: template-matching against known layouts for the demo).
- **Output:** Class label + confidence.
- **Failure cases:** Unknown/unsupported document → routed to manual handling, not blocked.

### 4.4 Tampering Detection
- **Purpose:** Detect signs of digital manipulation: altered photo regions, inconsistent fonts, copy-paste artifacts, compression anomalies, metadata inconsistencies.
- **Approach:** Combination of:
  - Error Level Analysis (ELA) / compression-artifact analysis (classical CV, explainable, cheap).
  - A CNN-based tamper classifier trained on genuine vs. manipulated synthetic samples (produces a manipulation heatmap + score).
  - Metadata/EXIF consistency checks (rule-based).
- **Output:** Anomaly score (0–1) + flagged regions + which indicator(s) triggered it.
- **Explainability:** Each indicator (font inconsistency, compression anomaly, region flagged) is reported individually — never a single opaque "tampered" verdict.
- **Failure cases:** Low-quality source images cause false positives — the officer sees the visual heatmap and can judge for themselves.

### 4.5 Face Verification
```
Document Photograph → Face Detection → Alignment → Embedding → Similarity Comparison → Confidence
```
- **Purpose:** Confirm the person presenting the document matches the document photograph.
- **Model type:** MediaPipe/RetinaFace for detection+alignment; ArcFace/InsightFace for embeddings (industry standard, well-benchmarked, open-source).
- **Output:** Similarity score (cosine distance), pass/fail against a configured threshold, confidence.
- **Verification vs. Identification (critical distinction):**
  - **Face Verification** (used here): 1-to-1 comparison — "does this live photo match this specific document photo?" Lower privacy risk, purpose-limited.
  - **Face Identification**: 1-to-many search against a database of faces to determine *who* someone is. **This system does NOT perform identification** — it only ever compares two specific images the officer has explicitly presented for one session. This boundary must be enforced architecturally (no face search endpoint should exist) and stated in the demo.
- **Biometric data handling:** Store only the similarity **score/result**, not the raw embedding, beyond the life of the session, unless legally mandated and consented. If embeddings must persist temporarily (session correlation), store them encrypted, scoped to the session, and auto-delete on a short retention window (Section 14). Never build a persistent face-search index.
- **Failure cases:** Poor lighting, occlusion, angle → low confidence, reported as such, never silently treated as a match or non-match.

### 4.6 Identity Consistency Check
- **Purpose:** Compare extracted fields (name, DOB, passport number, nationality) across the OCR result, MRZ result, and any secondary document (e.g., visa) presented in the same session.
- **Approach:** Deterministic field-matching with fuzzy string comparison (e.g., Levenshtein) for OCR-noise tolerance, not ML.
- **Output:** List of matched/mismatched fields, each independently explainable.

### Summary table

| Component | Runs | Local/API | Compute |
|---|---|---|---|
| OCR | Sync | Local | CPU |
| MRZ | Sync | Local | CPU |
| Classification | Sync | Local | CPU/light GPU |
| Tamper Detection | Async | Local | CPU/GPU |
| Face Verification | Async | Local | CPU/GPU |
| Identity Consistency | Sync | Local | CPU |

---

## 5. Risk Scoring Engine

### Approach comparison

| Approach | Explainability | Data needs | Recommended? |
|---|---|---|---|
| Rule-based | Excellent | None | Good baseline |
| **Weighted scoring** | **Excellent** | **Minimal** | **✅ Recommended for SIH** |
| Random Forest | Moderate (feature importance) | Labeled data | Future upgrade |
| XGBoost | Moderate | Labeled data | Future upgrade |
| Neural network | Poor (needs SHAP/LIME) | Large labeled data | Not appropriate now |

**Recommendation:** A **transparent weighted-scoring engine** for the SIH build. It requires no training data (which the team doesn't have access to anyway — no real fraud dataset exists), and every point of the score is directly traceable to a named factor. This directly satisfies the "never just say suspicious" requirement. Random Forest/XGBoost are reasonable **future** upgrades once real labeled incident data exists, but even then should feed an explanation layer (e.g., SHAP values presented in the same "factor: contribution" format) rather than replace it.

### Example structure
```
Risk Score: 82/100

Factors:
MRZ checksum mismatch     +20
Document expired          +15
Face similarity below threshold  +30
Tampering indicators found +17
Total: 82  →  HIGH RISK
```

### Design elements
- **Risk factors & weights:** Configurable per-factor weights stored in a `risk_rules` config (not hardcoded), so supervisors/admins can tune sensitivity without redeploying.
- **Thresholds:** e.g., 0–30 Low, 31–60 Medium, 61–85 High, 86–100 Critical (configurable).
- **Confidence propagation:** Each contributing check carries its own confidence; low-confidence checks contribute reduced weight (a low-confidence tamper flag shouldn't swing the score as hard as a checksum failure, which is deterministic).
- **False positive/negative handling:** Thresholds are tuned conservatively toward **more manual review, not more auto-rejection** — the cost of a false "verified" is far higher than the cost of an extra manual check.
- **Manual override:** Officer can always override the recommended action; override reason is mandatory and logged.
- **Explainability:** The full factor list is always shown — the score is never presented without its breakdown.

---

## 6. Verification Workflow

```
Officer Login
  ↓
Select Checkpoint
  ↓
Create Verification Session
  ↓
Capture/Upload Document(s)
  ↓
Document Processing (classify → OCR → MRZ)
  ↓
Field Validation (checksums, expiry)
  ↓
Database Lookup (demo/synthetic or authorized source)
  ↓
AI Analysis (tamper + face, async)
  ↓
Risk Assessment (weighted engine)
  ↓
Evidence Generation (assemble all check results)
  ↓
Officer Review (views evidence panel)
  ↓
Decision: Approve / Refer for Secondary / Reject
  ↓
Audit Log Entry (immutable record of session + decision)
```
Each step writes a `verification_checks` row — if any step fails, the session is marked "incomplete" and **cannot silently resolve to a "verified" state**; it must be resolved by manual entry or referred.

---

## 7. Feature Breakdown by Phase

| Phase | Objective | Key Deliverables |
|---|---|---|
| 1 | Foundation | Auth, roles, checkpoint model, basic layout |
| 2 | Document capture | Upload pipeline, storage, document classification |
| 3 | OCR + MRZ | Field extraction, checksum validation |
| 4 | Demo database | Synthetic traveler/document/watchlist data + lookup service |
| 5 | Face verification | Embedding pipeline, similarity scoring |
| 6 | Tamper detection | ELA + CNN classifier, evidence heatmap |
| 7 | Risk engine | Weighted scoring, configurable rules |
| 8 | Officer dashboard | Evidence panels, decision workflow |
| 9 | Security hardening | RLS, encryption, rate limiting, audit completeness |
| 10 | Demo polish | Scenario data, performance tuning, UX polish |

Each phase ends with a fully runnable application — no phase leaves the system in a broken state.

---

## 8. UI/UX Design System

- **Typography:** A clean grotesque sans (e.g., Inter) for data density; monospace for document numbers/MRZ strings to aid visual scanning.
- **Color:** Neutral slate/gray base; **status colors reserved exclusively for risk/verification states** (green=low/verified, amber=medium/review, red=high, dark red/black=critical) — never used decoratively elsewhere, so officers develop fast visual pattern recognition.
- **Density:** High-information layouts (officers scan many fields quickly) — tables and evidence panels favor compact rows over generous whitespace, unlike a typical marketing-style admin dashboard.
- **Key components:** status badges, risk score gauge, side-by-side document/photo viewer with zoom, evidence timeline (vertical stepper mirroring the pipeline), factor breakdown table, sticky decision bar (approve/refer/reject always visible, never buried in a scroll).
- **States:** Explicit loading states per pipeline stage (not one spinner for everything), explicit "AI unavailable — manual review required" error states, empty states for new sessions.
- **Avoiding generic feel:** distinctive checkpoint-themed iconography, a real-time evidence timeline instead of static cards, and a security-appropriate dark/neutral theme rather than a bright generic SaaS palette.

---

## 9. Component Library (Responsibilities)

| Component | Responsibility |
|---|---|
| DocumentUpload | Capture/upload with client-side validation |
| DocumentPreview | Zoomable viewer with region-highlight overlay |
| OCRResultPanel | Field-by-field extracted data + confidence |
| MRZResultCard | Parsed MRZ + checksum pass/fail per field |
| RiskScoreCard | Score gauge + risk level |
| RiskFactorList | Itemized weighted factors |
| FaceMatchResult | Side-by-side photos + similarity score |
| TamperResult | Heatmap overlay + indicator list |
| IdentityMatchCard | Cross-document field comparison |
| EvidenceTimeline | Vertical pipeline-stage stepper |
| VerificationDecisionBar | Approve/Refer/Reject with mandatory reason on override |
| CheckpointSelector | Pre-session checkpoint assignment |
| AuditLogViewer | Searchable, filterable immutable log view |
| WatchlistAlert | Prominent banner for demo watchlist hits |

---

## 10. User Roles

| Role | Capabilities |
|---|---|
| **Officer** | Create sessions, upload documents, view AI evidence, make decisions |
| **Supervisor** | All officer capabilities + review flagged/overridden cases, analytics, authorized overrides |
| **Administrator** | User/checkpoint management, risk-rule configuration, audit log access, system settings |

No additional roles are needed for the SIH scope; a future "Auditor" (read-only, audit-log-only access) could be added for production compliance needs.

---

## 11. User Flow

```
Landing → Login → Auth → Checkpoint Selection → Officer Dashboard
  → New Verification → Document Capture → AI Processing
  → Verification Results → Evidence Review → Officer Decision → Audit Record
```

**Failure/edge scenarios:**
- **Low confidence anywhere in the pipeline:** surfaced explicitly, contributes to risk score, never hidden.
- **OCR/AI failure:** session flagged "AI unavailable," officer proceeds via manual data entry; risk assessment marked incomplete rather than defaulted to "low risk."
- **Database unavailable:** lookup step marked "unavailable" (not "clear") — this itself is a risk factor.
- **Network failure:** local draft of session data retained client-side; sync resumes on reconnect; no partial submission silently treated as complete.

---

## 12. API Architecture (Overview)

Grouped by domain, all under `/api/v1/`, all requiring authenticated JWT except `/auth/*`:

- **auth:** login, refresh, logout.
- **travelers:** create/lookup traveler records (minimal PII).
- **documents:** upload metadata, retrieve document, list by session.
- **ocr:** trigger/retrieve OCR result for a document image.
- **mrz:** trigger/retrieve MRZ parse + checksum result.
- **verification:** create session, get session state, list session checks.
- **face:** trigger/retrieve face similarity result (session-scoped only, no search endpoint).
- **tamper:** trigger/retrieve tamper analysis result.
- **risk:** get computed risk assessment for a session.
- **watchlist:** demo-only lookup endpoint.
- **audit:** query audit logs (admin/supervisor only, read-only).
- **analytics:** aggregate stats (supervisor/admin only).

Each endpoint: validates JWT + role, validates input schema (Zod on frontend, Pydantic on backend), returns structured errors with a code (not raw stack traces), and logs the access to `audit_logs`.

---

## 13. Project Structure

```
/frontend        - Next.js app (pages, components, hooks)
/backend
  /api           - route definitions per domain
  /services      - verification, risk, auth orchestration logic
  /ai            - ocr, mrz, tamper, face modules
  /db            - models, migrations
  /workers       - async task definitions
/infrastructure  - deployment config, environment templates
/docs            - this documentation, ADRs
/tests           - unit, integration, e2e, adversarial
```
Separation keeps AI logic swappable (e.g., replacing PaddleOCR later) without touching API or DB layers, and keeps infra config out of application code.

---

## 14. Security Architecture

- **AuthN/AuthZ:** Supabase Auth/OIDC, short-lived JWTs, RBAC middleware + PostgreSQL RLS as defense-in-depth.
- **File upload security:** strict MIME/type checks, size limits, re-encoding on ingest (strips embedded scripts/malformed metadata), virus scanning before persistence.
- **Encryption:** TLS in transit; column-level encryption for document numbers/PII at rest; encrypted object storage.
- **Secrets management:** environment-based secret injection (never committed), rotated regularly.
- **Rate limiting:** per-user and per-IP limits on upload/verification endpoints to prevent abuse/scraping.
- **Session security:** short JWT expiry, refresh rotation, checkpoint-bound sessions.
- **Data retention:** document images auto-deleted after a configurable short window (e.g., 24–72 hours) unless flagged for an active investigation; biometric embeddings never persisted beyond session lifetime.
- **Audit trails:** append-only, tamper-evident (hash-chained rows), covering every access and decision.
- **Attack vectors considered:** malicious uploads (mitigated by re-encoding/scanning), API abuse (rate limiting), prompt injection (no LLM free-text is used in the decision path — risk engine is deterministic, not LLM-driven), adversarial images against face/tamper models (liveness checks and confidence thresholds, flagged as a known limitation), database leakage (RLS + encryption), unauthorized officer access (RBAC + audit + checkpoint binding).

---

## 15. AI Dataset Strategy

- **Training data:** publicly available OCR/face-verification benchmark datasets (open, non-sensitive) for baseline models; no real passport data ever used.
- **Demo data:** entirely **synthetic** — programmatically generated fake passport/visa templates with fabricated names, numbers, and photos (either generated or consented stock/model-released images), fabricated watchlist entries, fabricated biometric embeddings. This avoids any real personal data in a student demonstration entirely.
- **Validation data:** held-out synthetic samples, never seen during tuning.
- **Production data:** exclusively authorized government/enterprise sources under legal agreement — out of scope for SIH build.
- **Labeling/augmentation:** synthetic tampering applied programmatically (splice, recompress, font-swap) to create labeled tamper/genuine pairs; standard image augmentation (rotation, noise, lighting) for robustness.
- **Class imbalance:** genuine documents will vastly outnumber tampered ones even in synthetic sets — oversample tampered synthetic examples or apply class-weighted loss during any classifier training.

---

## 16. AI Evaluation Metrics

| Component | Key Metrics | Why |
|---|---|---|
| OCR | Character/word accuracy | Direct measure of extraction reliability |
| MRZ | Checksum validation accuracy | Deterministic correctness measure |
| Tamper detection | Precision, Recall, F1 | Balance false alarms vs. missed forgeries |
| Face verification | FAR, FRR, ROC-AUC | Industry-standard biometric metrics |
| Risk engine | Precision, Recall, FPR, FNR | Measures real-world review-triggering behavior |

**In border security, Recall (catching real problems) is prioritized over raw Precision** for tamper/risk detection — a missed forgery is far costlier than an extra manual review — but Precision still matters to avoid overwhelming officers with false alarms and causing "alert fatigue."

---

## 17. System Reliability

The core rule: **AI/service failure never silently resolves to "verified."** Every failure mode maps to "incomplete/needs manual review," never to a default pass.

| Failure | Behavior |
|---|---|
| OCR fails | Manual data entry, flagged in session |
| Face verification fails | Marked "unavailable," contributes to risk as unresolved factor |
| Database unavailable | Lookup marked "unavailable" (risk factor, not cleared) |
| AI inference timeout | Session marked incomplete, officer notified, can proceed manually |
| Unreadable document | Flagged for manual physical inspection |
| Multiple failures | Session auto-escalates to "Manual Secondary Verification" |
| Officer loses connectivity | Local draft retained, sync resumes; no partial auto-submit |

---

## 18. Observability

- **Application logs:** request/response metadata (never raw document images or PII bodies).
- **AI inference logs:** model version, latency, confidence — no raw biometric data logged.
- **Verification logs:** stage-by-stage `verification_checks` entries (this is the audit trail itself).
- **Error tracking:** structured error codes + stack traces in a secured internal channel only.
- **Metrics/alerts:** latency per pipeline stage, queue depth, failure rates, risk-level distribution over time.
- **What NOT to log:** raw document images, raw biometric embeddings, full passport numbers/DOB in plaintext logs — log references (IDs), not the sensitive payloads themselves.

---

## 19. Testing Strategy

Unit tests (per AI module and service function), integration tests (pipeline stage chaining), API tests (contract + auth enforcement), database tests (constraints, RLS policies), AI model tests (accuracy on held-out synthetic sets), OCR/MRZ tests (checksum edge cases), face verification tests (FAR/FRR on synthetic pairs), security tests (auth bypass attempts, injection, rate-limit enforcement), performance tests (latency under simulated checkpoint load), end-to-end tests (full officer workflow), adversarial tests (deliberately tampered synthetic documents, adversarial face images), and explicit false-positive/false-negative test suites tied to the four demo scenarios below.

---

## 20. SIH Demo Strategy

**Flow (5–10 min):**
```
Traveler arrives → Officer scans passport → OCR extracts info → MRZ validated
→ Checked against synthetic demo database → Face verification → Tamper analysis
→ Risk score generated → System explains factors → Officer reviews evidence → Decision
```

| Scenario | Setup | Expected Result |
|---|---|---|
| 1. Genuine | Clean synthetic passport, matching face, valid record | LOW RISK / VERIFIED |
| 2. Tampered | Synthetic passport with edited photo region | HIGH RISK / MANUAL VERIFICATION REQUIRED |
| 3. Identity mismatch | Document photo vs. presented face deliberately mismatched | HIGH RISK / IDENTITY MISMATCH |
| 4. Expired/blacklisted | Synthetic record flagged expired/blacklisted in demo DB | CRITICAL ALERT / DOCUMENT INVALID |

All four scenarios use **entirely fabricated synthetic identities and generated/consented images** — never real people's passport data — generated ahead of time and seeded into the demo database, so the live demo is deterministic and repeatable.

---

## 21. Roadmap

Phases 1–10 as listed in Section 7, sequenced to keep the project demoable at every milestone. Deferred to future versions (not needed for SIH core demo): government API integration, advanced 1:many biometric identification, multi-country document template support, edge/offline checkpoint deployment, physical hardware scanner integration, mobile apps, large-scale distributed multi-checkpoint deployment.

---

## 22. Future Extensions

Government/immigration API integration, airline system integration, physical checkpoint hardware (scanners, e-gates), QR/NFC passport chip verification, digital identity wallet support, offline-capable checkpoint mode, multi-language OCR, broader multi-country document template support, real-time centralized watchlist sync, distributed multi-checkpoint deployment with a central command dashboard, and cross-checkpoint anomaly detection (e.g., the same identity attempting entry at two locations simultaneously). These are explicitly **out of scope** for the SIH build and should be presented as "roadmap," not promised capabilities.

---

## 23. Final Architecture Summary

```
                ┌──────────────────────┐
                │   Officer Web App    │
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │      API Gateway     │
                └──────────┬───────────┘
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       Verification      Identity      Audit
         Service         Service       Service
             │             │
             ▼             ▼
       ┌──────────┐   ┌────────────┐
       │ AI Layer │   │ PostgreSQL │
       └──────────┘   └────────────┘
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
      OCR   Face  Tamper
           Match  Detection
             │
             ▼
        Risk Engine
             │
             ▼
       Explainable Result
             │
             ▼
       Human Officer (Final Decision)
```

**Core architectural decisions:** modular monolith over microservices (avoids premature complexity); weighted transparent risk scoring over ML black-box scoring (satisfies explainability requirement with no training data dependency); local AI inference over third-party APIs (privacy of biometric/document data); synthetic-only data strategy (legal/ethical safety for a student project); human-in-the-loop enforced architecturally, not just procedurally (no auto-decision endpoint exists).

**Major risks:** synthetic data may not generalize to real forgery patterns; face verification models can be biased across demographics — must be disclosed as a known limitation; CPU-only demo hardware may bottleneck async AI tasks — mitigate via job queueing and clear "processing" UI states.

**Critical dependencies:** PaddleOCR/Tesseract, InsightFace/ArcFace, OpenCV, PostgreSQL, Redis, Supabase (auth/storage).

**MVP boundary:** Phases 1–7 (auth through risk engine) constitute a functioning MVP.

**SIH demo boundary:** Phases 1–10, using synthetic data and the four scripted scenarios in Section 20.

**Future scaling strategy:** extract AI modules into independent services behind the same internal interfaces once inference load justifies it; move from synchronous demo-scale lookups to a properly indexed, possibly sharded verification database; introduce real government API integration behind the existing "authorized data source" abstraction without touching the verification service's public contract.
