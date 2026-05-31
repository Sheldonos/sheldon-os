# Sheldon OS Known Issues

This document reflects the **current post-debugging state** of the repository.

It separates:
1. **Resolved issues** fixed during the debugging pass
2. **Open non-critical issues** that still require follow-up
3. **Strategic/runtime gaps** that are not code defects but still block an unqualified broad production claim

---

## 1. Resolved During Debugging

### 1.1 Pydantic v2 deprecation warnings
**Status:** Resolved

**What was fixed**
- `src/core/config.py` was migrated from deprecated Pydantic v1 patterns to Pydantic v2 patterns.
- Replaced deprecated `@validator(...)` usage with `@field_validator(...)`
- Replaced inner `Config` class usage with `SettingsConfigDict`

**Impact**
- Removes deprecation noise from configuration loading
- Reduces future breakage risk on newer Pydantic releases

---

### 1.2 Pytest collection warning in agent tests
**Status:** Resolved

**What was fixed**
- Helper class in `tests/test_agents.py` was renamed from `TestAgent` to `MockAgent`
- Remaining stale references were updated

**Impact**
- Prevents pytest from attempting to collect helper classes as test classes
- Produces cleaner test output and more predictable collection behavior

---

### 1.3 Deprecated pandas monthly frequency alias warnings
**Status:** Resolved

**What was fixed**
- Forecasting tests were updated from deprecated `freq="M"` to `freq="ME"` in:
  - `tests/test_intelligence.py`
  - `tests/integration/test_intelligence_integration.py`

**Impact**
- Removes pandas deprecation warnings from forecasting-related test paths
- Improves forward compatibility with newer pandas versions

---

## 2. Open Non-Critical Issues

### 2.1 Repository-wide coverage target not yet met
**Severity:** Medium  
**Status:** Open

**Current state**
- Bounded validation suites pass
- Repository-wide automated coverage remains below the stated >80% target

**Why it matters**
- The codebase contains modules that are statically clean but not yet runtime-validated through sufficient automated tests
- This is the main reason the repository should not yet be described as fully validated for broad production rollout

**Recommended next steps**
- Add runtime tests for:
  - `src/api/*`
  - `src/integrations/connectors/*`
  - `src/integrations/mcp/*`
  - `src/products/ai_traceability/*`
  - `src/products/creator_monetization/*`
  - remaining `src/products/rightai/*` paths

---

### 2.2 Editable install should be revalidated in a clean environment
**Severity:** Low  
**Status:** Open

**Current state**
- Packaging metadata and local environment behavior were improved during debugging
- A clean-room validation of `pip install -e .` should still be performed in a fresh virtual environment before external distribution

**Why it matters**
- Local success in an already-prepared environment does not fully guarantee first-time install success for external users or CI runners

**Recommended next steps**
- Create a fresh virtual environment
- Run:
  - `pip install --upgrade pip`
  - `pip install -r requirements.txt`
  - `pip install -e .`
- Validate importability from a clean shell

---

### 2.3 LibreSSL/OpenSSL environment warning may still appear on some macOS Python builds
**Severity:** Low  
**Status:** Environment-specific

**Current state**
- This is not a Sheldon OS code defect
- Some local Python/urllib3 combinations on macOS may emit SSL backend warnings depending on interpreter build provenance

**Why it matters**
- Can create noise in local validation logs
- May confuse operators if not documented

**Recommended next steps**
- Use a Python build linked against supported OpenSSL
- Prefer managed runtimes used in CI/containers for release validation

---

### 2.4 Performance suite remains bounded rather than production-scale
**Severity:** Medium  
**Status:** Open

**Current state**
- Performance-related validation exists
- Full production-like load validation has not yet been executed against deployed infrastructure

**Why it matters**
- Current evidence supports controlled pilots, not unqualified scale claims
- 100+ concurrent agent claims should be revalidated in the target environment with observability enabled

**Recommended next steps**
- Run sustained load tests in staging
- Capture:
  - API latency
  - task throughput
  - memory growth
  - CPU saturation
  - Redis/database latency
- Store benchmark outputs in release artifacts

---

## 3. Strategic / Runtime Gaps Still Blocking Broad Production Claims

These are not necessarily bugs, but they remain important release constraints.

### 3.1 API runtime validation gap
**Severity:** High  
**Status:** Open

**Current state**
- API modules are statically validated
- End-to-end runtime tests for auth, rate limiting, and gateway behavior are still limited

**Why it matters**
- Enterprise deployment requires runtime proof, not only static cleanliness

**Required follow-up**
- Add API tests for:
  - JWT issuance and expiration
  - protected route access
  - invalid token handling
  - rate limiting behavior
  - CORS behavior
  - OpenAPI/docs route availability

---

### 3.2 Integration connector runtime validation gap
**Severity:** High  
**Status:** Open

**Current state**
- Connector code is present and statically validated
- Runtime behavior for Slack, Email, CRM, and MCP flows is not yet comprehensively exercised in automated tests

**Why it matters**
- External integrations are common failure points in production systems

**Required follow-up**
- Add mocked and failure-path tests for:
  - auth failures
  - retries
  - timeouts
  - malformed responses
  - partial outages
  - rate-limit responses

---

### 3.3 Product runtime validation gap
**Severity:** High  
**Status:** Open

**Current state**
- Product modules exist and lint/type checks pass
- Runtime smoke coverage for AI Traceability, Creator Monetization, and RightAI remains incomplete

**Why it matters**
- Product-layer code is where enterprise buyers will evaluate real value and reliability

**Required follow-up**
- Add smoke/integration tests for:
  - AI Traceability event capture and policy evaluation
  - Creator Monetization payment and aggregation flows
  - RightAI usage/billing/subscription flows
  - cross-product orchestration paths where applicable

---

### 3.4 README and external positioning must remain evidence-based
**Severity:** Medium  
**Status:** Open governance requirement

**Current state**
- README was updated to avoid overstating readiness
- Future edits must preserve this discipline

**Why it matters**
- Overstated readiness creates diligence risk during enterprise review, fundraising, or acquisition discussions

**Required follow-up**
- Keep all public claims aligned with:
  - actual coverage
  - actual runtime validation
  - actual deployment evidence

---

## 4. Deferred Improvements / Technical Debt

### 4.1 Expand observability coverage
- Add richer structured logging across product and integration layers
- Standardize correlation IDs across orchestrator, agents, and API requests

### 4.2 Add deployment-environment smoke scripts
- Provide one-command smoke validation for:
  - API gateway
  - orchestrator startup
  - Redis connectivity
  - PostgreSQL connectivity
  - MCP registry health

### 4.3 Add staged release evidence artifacts
- Persist benchmark outputs
- Persist security scan outputs
- Persist deployment verification outputs
- Link them from `DEBUG_REPORT.md`

---

## 5. Current Bottom Line

### Suitable now for
- Controlled pilots
- Internal demos
- Technical diligence
- Architecture review
- Staged enterprise evaluation

### Not yet suitable to claim
- Fully unqualified broad production readiness
- Repository-wide >80% validated runtime coverage
- Production-scale performance proof across all subsystems