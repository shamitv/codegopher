# Chained Vulnerability Static Audit Report

**Project:** Nexus Health Vault — Patient Portal  
**Date:** 2026-05-24  
**Scope:** Static-only source review of `app-02-patient-portal` workspace  
**Reviewer:** CodeGopher (Chained Vulnerability Static Audit Skill)

---

## 1. Summary Dashboard

| Metric | Value |
|---|---|
| **Total Chains Detected** | 2 (High) |
| **Cross-Cutting Weaknesses** | 8 |
| **Maximum Chain Severity** | **High** |
| **Highest Confidence Chain** | Chain 1 — High |
| **Areas Reviewed** | Models, views, URLs, settings, HTML/JS/CSS frontend, migrations, tests, Dockerfile |
| **Areas Not Reviewed** | Runtime configuration, deployed environment variables, actual network topology, third-party service integrations |

### Chain Summary Table

| Chain ID | Title | Severity | Confidence | Impact | Easiest Break |
|----------|-------|----------|------------|--------|---------------|
| **Chain 1** | Credential Harvesting → MD5 Brute Force → Unauthorized Patient Data Exfiltration | **High** | High | Full PHI exposure across all patients | Enforce strong password hashing + ownership checks |
| **Chain 2** | Insecure Direct Object Reference (IDOR) → Bulk Patient Data Theft | **High** | High | Unrestricted access to any patient's medical records | Add per-record ownership authorization in `get_patient_records` |

---

## 2. Methodology & Safety Note

### Method

This audit follows a four-phase chained vulnerability methodology:

1. **Attack Surface Mapping** — Identified all public routes, API endpoints, webhook handlers, static files, database seeds, and request parameters.
2. **Weakness Inventory** — Cataloged every individually modest weakness found in source, configuration, and templates.
3. **Attack Graph Synthesis** — Connected entry points to intermediate weaknesses, weaknesses to sinks, and sinks to impacts using only static evidence from the codebase.
4. **Impact Assessment** — Rated each chain by impact, reachability, confidence, and the easiest remediation link.

### Static-Only Boundary

- **Only** source files, configurations, tests, schemas, routes, controllers, services, templates, middleware, dependency manifests, and existing documentation were reviewed.
- **No** live HTTP probes, dynamic scanners, SQL injection payloads, credential attacks, fuzzing, port scans, or external network tests were performed.
- **No** executable exploit payloads or step-by-step operational abuse instructions were generated.
- Evidence is drawn exclusively from cited file paths and line ranges in the source code.

---

## 3. Chain 1: Credential Harvesting → MD5 Brute Force → Unauthorized Patient Data Exfiltration

### 3.1 Mermaid Attack Graph

```mermaid
flowchart LR
    A[Attacker] -->|Visits index.html| B[Hardcoded Plaintext Seeds in HTML]
    A -->|POST /api/auth/login| C[login_view Different Error Messages]
    B -->|alice/alice123, bob/bob123| D[Valid Credential Pairs]
    C -->|Account Not Found vs Wrong Password| E[Username Enumeration]
    D --> F[Known Passwords (plaintext)]
    E --> G[Valid Username List]
    G --> H[Targeted Credential Testing]
    F --> I[Direct Login as Known User]
    H --> I
    I --> J[Session Cookie Set]
    J -->|No ownership check| K[GET /api/patients/{any_id}/records]
    K --> L[Full Patient PHI: prescriptions, diagnostics, blood type, DOB, full name]
    
    style L fill:#ff1744,color:#fff
    style K fill:#ff9100,color:#fff
    style I fill:#ffab00,color:#000
    style D fill:#448aff,color:#fff
```

### 3.2 Detailed Chain Breakdown

#### Link 1: Plaintext Password Seeds in Static HTML

- **Source File:** `portal/static/index.html`
- **Lines:** ~38–43 (in the "PATIENT PIN SEEDS" section)
- **Evidence:** The HTML comment block explicitly lists three valid username/password pairs:

```html
<span style="font-weight: 600; color: var(--secondary);">PATIENT PIN SEEDS:</span><br>
• Patient 1: <code>alice</code> / <code>alice123</code> (ID: 1)<br>
• Patient 2: <code>bob</code> / <code>bob123</code> (ID: 2)<br>
• Staff Doctor: <code>dr_cyber</code> / <code>staff123</code>
```

- **Assessment:** These are intended as "dev seeds" but are embedded in client-visible HTML. Any user loading the page can immediately obtain valid credentials without brute forcing.

#### Link 2: Different Error Messages Enable Username Enumeration

- **Source File:** `portal/views.py`
- **Function:** `login_view`
- **Lines:** ~91–107
- **Evidence:**

```python
except PatientProfile.DoesNotExist:
    return JsonResponse({'success': False, 'message': 'Account not found in patient registry'}, status=401)
# ...
return JsonResponse({'success': False, 'message': 'Incorrect password for this account'}, status=401)
```

- **Assessment:** An attacker can distinguish between non-existent and existing usernames, building a valid username list before launching targeted attacks.

#### Link 3: MD5 Password Hashing (Cryptographically Weak)

- **Source File:** `portal/models.py`
- **Methods:** `set_password_md5`, `check_password_md5`
- **Lines:** ~7–14 (approximate)
- **Evidence:**

```python
def set_password_md5(self, password):
    """Hashes password using obsolete MD5 algorithm."""
    self.password_hash = hashlib.md5(password.encode()).hexdigest()

def check_password_md5(self, password):
    """Verifies password matches MD5 hash in database."""
    return self.password_hash == hashlib.md5(password.encode()).hexdigest()
```

- **Assessment:** MD5 is a broken hash function. Rainbow tables for MD5 are trivially available. Combined with the short passwords seeded in `seed_database()` (e.g., `alice123`, `bob123`, `admin123`), offline brute force is trivially fast.

#### Link 4: Hardcoded Database Seeds with Weak Passwords

- **Source File:** `portal/views.py`
- **Function:** `seed_database()`
- **Lines:** ~39–84 (approximate)
- **Evidence:**

```python
p1 = PatientProfile(username='alice', ..., role='PATIENT')
p1.set_password_md5('alice123')
p2 = PatientProfile(username='bob', ..., role='PATIENT')
p2.set_password_md5('bob123')
p3 = PatientProfile(username='dr_cyber', ..., role='STAFF')
p3.set_password_md5('staff123')
p4 = PatientProfile(username='admin', ..., role='ADMIN')
p4.set_password_md5('admin123')
```

- **Assessment:** Four users with predictable, trivially guessable passwords. The `admin` account with role `ADMIN` is particularly dangerous.

#### Link 5: No Ownership Authorization in Patient Records Endpoint

- **Source File:** `portal/views.py`
- **Function:** `get_patient_records`
- **Lines:** ~128–156 (approximate)
- **Evidence:**

```python
def get_patient_records(request, patient_id):
    """Browse sensitive medical histories."""
    # Authenticated checks
    if 'patient_id' not in request.session:
        return JsonResponse({'message': 'Unauthenticated'}, status=401)
    try:
        # Performs no check comparing request.session['patient_id'] with the target parameter.
        target_patient = PatientProfile.objects.get(id=patient_id)
    except PatientProfile.DoesNotExist:
        return JsonResponse({'message': 'Patient records not found'}, status=404)
```

- **Assessment:** The only authorization check is whether the request has a valid session. There is no comparison of `request.session['patient_id']` (or the logged-in user's ID) against the requested `patient_id` parameter. Any authenticated user can retrieve any patient's records.

#### Link 6: Session Cookie Not Secure

- **Source File:** `patient_portal/settings.py`
- **Lines:** ~68–70
- **Evidence:**

```python
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Localhost dev support
SESSION_COOKIE_SAMESITE = 'Lax'
```

- **Assessment:** `SESSION_COOKIE_SECURE = False` means session cookies are transmitted over unencrypted HTTP connections, enabling network-level session hijacking via man-in-the-middle attacks.

### 3.3 Impact

- **Severity:** **High**
- **Confidence:** **High** — Every link is statically provable from cited source code.
- **Impact:** An attacker who loads the index.html page obtains valid credentials (alice/alice123, bob/bob123). These credentials provide authenticated session access. From any authenticated session, the attacker can call `GET /api/patients/{any_id}/records` to retrieve:
  - Full name and date of birth
  - Blood type
  - Complete prescription history (medication name, dosage, frequency, prescribing doctor)
  - Diagnostic notes containing clinical indicators, medical conditions (e.g., ADHD, Stage 1 Hypertension, Chronic Asthma)
- **Data Exposed:** Full PHI (Protected Health Information) for all patients in the system.
- **Reachability:** Trivial. The attack requires only an HTTP connection to the server and a web browser.

### 3.4 Remediation

| Link | Remediation | Priority |
|------|-------------|----------|
| HTML password seeds | Remove the "PATIENT PIN SEEDS" block from `portal/static/index.html` entirely. | Critical |
| MD5 password hashing | Replace `hashlib.md5()` with Django's built-in `django.contrib.auth.hashers.make_password()` / `check_password()` (PBKDF2 or Argon2). | Critical |
| Different error messages | Return identical error messages for both "account not found" and "wrong password" (e.g., "Invalid credentials"). | Medium |
| No ownership check | Add `patient_id = request.session.get('patient_id')` and verify it matches the requested `patient_id` parameter before returning data. | Critical |
| Session cookie insecure | Set `SESSION_COOKIE_SECURE = True` in production environments (use environment variable or conditional check). | High |

---

## 4. Chain 2: Insecure Direct Object Reference (IDOR) → Bulk Patient Data Theft

### 4.1 Mermaid Attack Graph

```mermaid
flowchart LR
    A[Authenticated User - e.g., alice] -->|Auth session via login| B[getSession]
    B -->|Session cookie| C[Authenticated state]
    C -->|GET /api/patients/{id}/records where id != own id| D[get_patient_records view]
    D -->|Session check passes (always)| E[Fetches target_patient.objects.get]
    E -->|No ownership verification| F[Returns prescriptions, diagnostics, DOB, blood type]
    
    G[Frontend UI] -->|User enters arbitrary ID in #idorPatientIdInput| H[triggerIdorRecordFetch called]
    H -->|loadRecords(id) via /api/patients/{id}/records| D
    
    style F fill:#ff1744,color:#fff
    style D fill:#ff9100,color:#fff
    style E fill:#ff9100,color:#fff
    style G fill:#7c4dff,color:#fff
```

### 4.2 Detailed Chain Breakdown

#### Link 1: Endpoint Accepts Arbitrary Patient ID

- **Source File:** `portal/urls.py`
- **Line:** ~10
- **Evidence:**

```python
path('api/patients/<int:patient_id>/records', views.get_patient_records, name='patient_records'),
```

- **Assessment:** The URL pattern accepts any integer `patient_id` directly from the URL path.

#### Link 2: No Role-Based or Ownership Authorization

- **Source File:** `portal/views.py`
- **Function:** `get_patient_records`
- **Lines:** ~128–156
- **Evidence:**

```python
def get_patient_records(request, patient_id):
    """Browse sensitive medical histories."""
    # Authenticated checks
    if 'patient_id' not in request.session:
        return JsonResponse({'message': 'Unauthenticated'}, status=401)
    try:
        # Performs no check comparing request.session['patient_id'] with the target parameter.
        target_patient = PatientProfile.objects.get(id=patient_id)
    except PatientProfile.DoesNotExist:
        return JsonResponse({'message': 'Patient records not found'}, status=404)
```

- **Assessment:** The comment in the source code explicitly confirms this is intentional ("Performs no check..."). The only gate is session presence. Role-based checks exist in `list_appointments` but not in `get_patient_records`.

#### Link 3: Frontend Explicitly Exposes the IDOR Vector

- **Source File:** `portal/static/index.html`
- **Lines:** ~123–127 (approximate)
- **Evidence:**

```html
<div style="border-top: 1px solid var(--border-color); padding-top: 16px; margin-top: 16px; display: flex; gap: 8px; align-items: center;">
    <input type="number" id="idorPatientIdInput" class="form-input" style="width: 70px; padding: 8px; text-align: center; font-family: var(--font-mono);" placeholder="ID" value="1">
    <button onclick="triggerIdorRecordFetch()" class="btn btn-secondary" style="flex-grow: 1; padding: 8px;">Switch Record Vault</button>
</div>
```

- **Assessment:** The frontend provides a dedicated UI element labeled "Switch Record Vault" with a numeric input for patient IDs, and a button explicitly labeled to change which patient's records are displayed. This is not a hidden or incidental feature—it is deliberately presented as a user-facing control.

#### Link 4: Frontend JavaScript Calls the Vulnerable Endpoint

- **Source File:** `portal/static/js/app.js`
- **Function:** `triggerIdorRecordFetch` / `loadRecords`
- **Lines:** ~84–90
- **Evidence:**

```javascript
function triggerIdorRecordFetch() {
    const id = parseInt(document.getElementById("idorPatientIdInput").value);
    if (!isNaN(id)) {
        loadRecords(id);
    }
}
function loadRecords(patientId) {
    fetch(`/api/patients/${patientId}/records`)
```

- **Assessment:** The frontend directly calls the API endpoint with the user-provided ID. Any integer value can be sent, including IDs belonging to other patients, staff members, or even the admin user.

#### Link 5: Full Sensitive Data Returned

- **Source File:** `portal/views.py`
- **Function:** `get_patient_records` (return block)
- **Evidence:**

```python
return JsonResponse({
    'patient_id': target_patient.id,
    'full_name': target_patient.full_name,
    'date_of_birth': target_patient.date_of_birth.strftime('%Y-%m-%d') if target_patient.date_of_birth else '-',
    'blood_type': target_patient.blood_type,
    'role': target_patient.role,
    'prescriptions': rx_list  # Contains medication_name, dosage, frequency, prescribing_doctor, diagnostic_notes
})
```

- **Assessment:** The response includes personally identifiable information (full name, DOB, blood type, role) and all clinical data including diagnostic notes revealing medical conditions.

### 4.3 Impact

- **Severity:** **High**
- **Confidence:** **High** — The IDOR is explicit in the source code; the endpoint accepts any `patient_id` with only a session check. The frontend even provides a UI for it.
- **Impact:** Any authenticated user can access any patient's complete medical records by supplying an arbitrary patient ID. This constitutes bulk PHI exfiltration.
- **Reachability:** Trivial. Requires authentication (trivially obtained via hardcoded seeds or brute force) and one HTTP request per target patient ID.

### 4.4 Remediation

| Link | Remediation | Priority |
|------|-------------|----------|
| Missing ownership check | Compare `request.session.get('patient_id')` against the URL `patient_id` parameter. Return 403 if they differ. | Critical |
| Frontend IDOR controls | Remove or restrict the "Switch Record Vault" input/button for non-admin users. Admin users should use an admin interface, not the patient-facing portal. | Critical |
| Missing role check | Consider adding role-based access: PATIENT users can only view their own records; STAFF/ADMIN may view all records. | High |

---

## 5. Cross-Cutting Weaknesses

These are security-relevant issues that individually or collectively degrade the security posture but do not fully form a standalone attack chain with a critical sink in this codebase.

### 5.1 Hardcoded Secret Key

- **File:** `patient_portal/settings.py`, line ~12
- **Evidence:** `SECRET_KEY = 'django-insecure-nexus-vault-clinical-key-glow-neon'`
- **Risk:** The Django secret key is hardcoded in source. Anyone with source access can forge sessions, CSRF tokens, and signed cookies.
- **Remediation:** Use environment variables or a secrets manager for `SECRET_KEY`.

### 5.2 Debug Mode Enabled

- **File:** `patient_portal/settings.py`, line ~14
- **Evidence:** `DEBUG = True`
- **Risk:** Enables detailed traceback pages, reveals stack traces, and may expose sensitive configuration data.
- **Remediation:** Set `DEBUG = False` in production; use environment variable to toggle.

### 5.3 Wildcard Allowed Hosts

- **File:** `patient_portal/settings.py`, line ~16
- **Evidence:** `ALLOWED_HOSTS = ['*']`
- **Risk:** Accepts requests for any `Host` header value, enabling HTTP host header attacks and cache poisoning.
- **Remediation:** Restrict to specific trusted hostnames.

### 5.4 No Password Validators

- **File:** `patient_portal/settings.py`, line ~53
- **Evidence:** `AUTH_PASSWORD_VALIDATORS = []`
- **Risk:** Users can set trivially guessable passwords (as seen in the seed data).
- **Remediation:** Configure Django's password validators (`UserAttributeSimilarityValidator`, `MinimumLengthValidator`, `CommonPasswordValidator`, `NumericPasswordValidator`).

### 5.5 CSRF Exempt on State-Changing Endpoints

- **File:** `portal/views.py`
- **Functions:** `login_view`, `logout_view`, `create_appointment`
- **Evidence:** All three functions are decorated with `@csrf_exempt`.
- **Risk:** Cross-site request forgery attacks can force authenticated users to log in, log out, or create appointments without their consent.
- **Remediation:** Remove `@csrf_exempt` from endpoints that need CSRF protection. For SPAs using session cookies, rely on Django's CSRF middleware with appropriate token handling. For APIs, implement CSRF protection via CSRF tokens in POST headers or use token-based auth.

### 5.6 No Rate Limiting / Brute Force Protection

- **File:** `portal/views.py`, function `login_view`
- **Evidence:** Comment on line ~95: `# No brute force lockouts or connection throttling rules.`
- **Risk:** Unlimited login attempts enable offline dictionary attacks against known usernames.
- **Remediation:** Implement rate limiting (e.g., Django Ratelimit, or middleware-based throttling) and account lockout after repeated failures.

### 5.7 SQLite in Production

- **File:** `patient_portal/settings.py`, lines ~56–59
- **Evidence:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```
- **Risk:** SQLite is not suitable for concurrent multi-user production access. It lacks row-level locking, can corrupt under concurrent writes, and has no network security model.
- **Remediation:** Use PostgreSQL or MySQL for production deployments.

### 5.8 Unvalidated/Unsanitized Input in Appointments

- **File:** `portal/views.py`, function `create_appointment`
- **Evidence:**
```python
clinic = data.get('clinic_department', '').strip()
reason = data.get('reason_for_visit', '').strip()
```
- **Risk:** No HTML escaping or output encoding is applied to user-provided `clinic_department` and `reason_for_visit` before storage. While the data is stored in the database, it could be reflected elsewhere (e.g., admin views) leading to stored XSS. The frontend also uses `innerHTML` to render data from the server, which compounds the risk.
- **Remediation:** Sanitize user input and ensure all template rendering uses Django's auto-escaping or manual `|safe` avoidance.

---

## 6. Not-Reviewed Areas & Recommendations for Further Testing

### 6.1 Areas Not Reviewed (Static-Only Limitation)

| Area | Reason |
|------|--------|
| Runtime configuration (environment variables, Docker secrets) | Not present in source code |
| Network security (TLS, firewall rules, proxy configuration) | No configuration files for reverse proxy or network topology |
| TLS/HTTPS enforcement | Dockerfile exposes port 8082 with no explicit HTTPS configuration |
| Database file access controls | File permissions and OS-level security not visible in source |
| CI/CD pipeline security | No pipeline configuration files found |
| Logging and monitoring | No logging configuration or audit trail implementation reviewed |
| Session expiration / timeout | `settings.py` does not configure `SESSION_EXPIRE_AT_BROWSER_CLOSE` or `SESSION_COOKIE_AGE` |
| Input sanitization in `search_patients` | SQL injection possibility via ORM (protected by Django ORM parameterization, but needs verification) |

### 6.2 Recommended Tests to Add

1. **IDOR Authorization Test:** Add a `TestCase` that authenticates as user A (patient_id=1), then calls `GET /api/patients/2/records` and verifies a 403 or 404 is returned.
2. **Password Strength Validation Test:** Test that weak passwords are rejected by `AUTH_PASSWORD_VALIDATORS`.
3. **CSRF Protection Test:** Verify that state-changing POST endpoints reject requests without valid CSRF tokens.
4. **Session Security Test:** Verify `SESSION_COOKIE_SECURE` is `True` in production-like settings.
5. **Error Message Consistency Test:** Verify that login returns the same error message for both invalid username and invalid password.
6. **Rate Limiting Test:** Verify that repeated login attempts are throttled or blocked.

---

## 7. Remediation Priority Matrix

| Priority | Action | Files Affected |
|----------|--------|----------------|
| **P0 — Immediate** | Remove hardcoded credentials from `index.html` | `portal/static/index.html` |
| **P0 — Immediate** | Replace MD5 hashing with Django `make_password` / `check_password` | `portal/models.py` |
| **P0 — Immediate** | Add ownership authorization to `get_patient_records` | `portal/views.py` |
| **P0 — Immediate** | Remove frontend "Switch Record Vault" IDOR control | `portal/static/index.html`, `portal/static/js/app.js` |
| **P1 — High** | Fix `SECRET_KEY` to use environment variable | `patient_portal/settings.py` |
| **P1 — High** | Disable `DEBUG = True` in production | `patient_portal/settings.py` |
| **P1 — High** | Set `SESSION_COOKIE_SECURE = True` in production | `patient_portal/settings.py` |
| **P1 — High** | Restrict `ALLOWED_HOSTS` to known hostnames | `patient_portal/settings.py` |
| **P2 — Medium** | Remove `@csrf_exempt` from non-API endpoints | `portal/views.py` |
| **P2 — Medium** | Implement rate limiting on login endpoint | `portal/views.py` |
| **P2 — Medium** | Unify login error messages | `portal/views.py` |
| **P2 — Medium** | Configure password validators | `patient_portal/settings.py` |
| **P3 — Low** | Migrate from SQLite to PostgreSQL/MySQL | `patient_portal/settings.py` |

---

## 8. Conclusion

This patient portal codebase contains **two High-severity chained vulnerabilities** that collectively allow an attacker to trivially gain access to any patient's protected health information (PHI) with minimal effort:

1. **Chain 1** leverages hardcoded plaintext credentials in the frontend combined with weak MD5 password hashing and a vulnerable login endpoint to establish authenticated access, then exploits the lack of ownership authorization to exfiltrate records.
2. **Chain 2** is a straightforward IDOR in the patient records endpoint, explicitly facilitated by a frontend UI element, allowing any authenticated user to access any patient's records.

The codebase also contains **8 cross-cutting weaknesses** including a hardcoded secret key, debug mode in production, wildcard allowed hosts, missing CSRF protection on state-changing endpoints, no rate limiting, SQLite usage, no password validators, and potential stored XSS via unvalidated input rendered with `innerHTML`.

**The entire codebase should be considered insecure for any production or even staged deployment.** All P0 items must be remediated before the application handles any real user data.
