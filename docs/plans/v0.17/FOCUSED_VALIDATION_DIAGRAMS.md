# v0.17 Focused Validation Diagrams

This companion report visualizes the sanitized app architectures and the chained-audit outcomes for `app-05`, `app-10`, and `app-14`. It uses only aggregate benchmark outcomes and source-navigation summaries from the focused run. Raw event logs, generated reports, proxy snapshots, endpoint values, usernames, API key names/values, temp roots, and original corpus paths are intentionally omitted.

## Legend

Architecture diagrams show the source-level components the agent explored. Chain overlay diagrams show whether GPT-5.4-mini fully connected the chain during the benchmark.

```mermaid
flowchart LR
    full[Detected full chain]
    partial[Partially detected / not fully detected]
    missed[Missed bridge or component]
    surface[Entry surface]
    sink[Sink or outcome]

    full --> surface --> sink
    partial -.-> surface
    missed -.-> sink

    classDef full fill:#e8f6ec,stroke:#1f7a3f,color:#0b2c18;
    classDef partial fill:#fff4d6,stroke:#a66a00,color:#3b2500;
    classDef missed fill:#fde8e8,stroke:#b42318,color:#3a0a06;
    classDef component fill:#eef2ff,stroke:#475569,color:#111827;
    classDef sink fill:#f4f4f5,stroke:#52525b,color:#18181b;
    class full full;
    class partial partial;
    class missed missed;
    class surface component;
    class sink sink;
```

## app-05 Architecture

```mermaid
flowchart LR
    client[Browser and learner/instructor users]
    auth[Auth and session routes]
    course[Course and dashboard routes]
    enroll[Enrollment and role flows]
    submit[Submission and quiz flows]
    grade[Grading and override flows]
    import[Import routes and worker]
    debug[Debug/config surface]
    services[Course, enrollment, submission, grading services]
    repos[Repositories and persistence]
    fetch[Internal fetch/import sink]
    data[(Application data)]

    client --> auth
    client --> course
    client --> enroll
    client --> submit
    client --> grade
    client --> import
    client --> debug
    auth --> services
    course --> services
    enroll --> services
    submit --> services
    grade --> services
    services --> repos --> data
    import --> fetch
    debug --> import

    classDef surface fill:#eef2ff,stroke:#475569,color:#111827;
    classDef service fill:#ecfeff,stroke:#0e7490,color:#083344;
    classDef store fill:#f4f4f5,stroke:#52525b,color:#18181b;
    class client,auth,course,enroll,submit,grade,import,debug surface;
    class services,fetch service;
    class repos,data store;
```

## app-05 Chain Overlay

Outcome: `1/3` complete chains and `5/7` required components were found. The debug-to-import chain was fully detected; the two user/session and role/state-change chains were not fully connected.

```mermaid
flowchart LR
    c1[Detected: debug config leak to internal fetch pivot]
    debug[Debug/config surface]
    import[Import worker]
    ssrf[Internal fetch sink]

    c2[Not fully detected: config/session/submission exfiltration]
    cfg[Config exposure]
    session[Session forgery bridge]
    submission[Submission lookup]
    exfil[Quiz submission data]

    c3[Not fully detected: enrollment to grade tampering]
    enroll[Enrollment role path]
    audit[Missing audit bridge]
    grade[Grade override sink]

    c1 --> debug --> import --> ssrf
    c2 -.-> cfg -.-> session -.-> submission -.-> exfil
    c3 -.-> enroll -.-> audit -.-> grade

    classDef full fill:#e8f6ec,stroke:#1f7a3f,color:#0b2c18;
    classDef partial fill:#fff4d6,stroke:#a66a00,color:#3b2500;
    classDef missed fill:#fde8e8,stroke:#b42318,color:#3a0a06;
    classDef component fill:#eef2ff,stroke:#475569,color:#111827;
    classDef sink fill:#f4f4f5,stroke:#52525b,color:#18181b;
    class c1 full;
    class c2,c3 partial;
    class session,enroll,audit missed;
    class debug,import,cfg,submission component;
    class ssrf,exfil,grade sink;
```

## app-10 Architecture

```mermaid
flowchart LR
    client[Operators, customers, and billing clients]
    security[Security configuration]
    auth[Auth controller]
    admin[Admin controller]
    billing[Billing controller]
    usage[Usage controller]
    customer[Customer controller]
    health[Health controller]
    services[Billing, usage, payment, cache, and search services]
    audit[Audit producer and consumer]
    repos[Repositories and models]
    db[(Billing database)]
    search[Search/index boundary]
    cache[Cache boundary]

    client --> security --> auth
    client --> admin
    client --> billing
    client --> usage
    client --> customer
    client --> health
    admin --> services
    billing --> services
    usage --> services
    customer --> services
    services --> repos --> db
    services --> audit
    services --> search
    services --> cache

    classDef surface fill:#eef2ff,stroke:#475569,color:#111827;
    classDef service fill:#ecfeff,stroke:#0e7490,color:#083344;
    classDef store fill:#f4f4f5,stroke:#52525b,color:#18181b;
    class client,security,auth,admin,billing,usage,customer,health surface;
    class services,audit,search,cache service;
    class repos,db store;
```

## app-10 Chain Overlay

Outcome: `1/2` complete chains and `4/6` required components were found. The usage-query chain was fully detected; the billing-admin chain remained partial.

```mermaid
flowchart LR
    c1[Detected: usage SQL injection to invoice exfiltration]
    usage[Usage controller]
    native[Native usage query construction]
    invoice[Invoice lookup]
    auditBypass[Audit bypass]
    db[Data exfiltration]

    c2[Not fully detected: weak billing-admin custom-rate modification]
    admin[Weak billing admin auth]
    rate[Custom rate mutation]
    missingAudit[Missing audit bridge]
    tamper[Data modification]

    c1 --> usage --> native --> invoice --> auditBypass --> db
    c2 -.-> admin -.-> rate -.-> missingAudit -.-> tamper

    classDef full fill:#e8f6ec,stroke:#1f7a3f,color:#0b2c18;
    classDef partial fill:#fff4d6,stroke:#a66a00,color:#3b2500;
    classDef missed fill:#fde8e8,stroke:#b42318,color:#3a0a06;
    classDef component fill:#eef2ff,stroke:#475569,color:#111827;
    classDef sink fill:#f4f4f5,stroke:#52525b,color:#18181b;
    class c1 full;
    class c2 partial;
    class admin,missingAudit missed;
    class usage,native,invoice,auditBypass,rate component;
    class db,tamper sink;
```

## app-14 Architecture

```mermaid
flowchart LR
    client[Patients, clinicians, and schedulers]
    routes[Route layer]
    auth[Auth controller and token service]
    appointment[Appointment controller and service]
    notes[Clinical note controller and service]
    search[Patient search controller and client]
    debug[Debug topology controller]
    schedule[Schedule validator]
    audit[Audit producer]
    rx[Prescription consumer]
    repos[Appointment and clinical repositories]
    db[(Clinical data store)]
    outbound[Internal search/outbound boundary]
    queue[Message bus]

    client --> routes
    routes --> auth
    routes --> appointment
    routes --> notes
    routes --> search
    routes --> debug
    appointment --> schedule
    appointment --> repos --> db
    notes --> repos
    search --> outbound
    debug --> outbound
    appointment --> audit --> queue
    queue --> rx --> db

    classDef surface fill:#eef2ff,stroke:#475569,color:#111827;
    classDef service fill:#ecfeff,stroke:#0e7490,color:#083344;
    classDef store fill:#f4f4f5,stroke:#52525b,color:#18181b;
    class client,routes,auth,appointment,notes,search,debug surface;
    class schedule,audit,rx,outbound service;
    class repos,db,queue store;
```

## app-14 Chain Overlay

Outcome: `3/3` complete chains and `6/6` required components were found after one corrective pass. No required chain remained missed in the final selected attempt.

```mermaid
flowchart LR
    c1[Detected: weak JWT to patient-notes exfiltration]
    jwt[Weak JWT validation]
    notes[Patient notes IDOR]
    db[Database exfiltration]

    c2[Detected: schedule override to prescription tampering]
    schedule[Schedule override]
    audit[Missing audit]
    rx[Prescription tampering]

    c3[Detected: debug topology to internal search pivot]
    debug[Debug topology leak]
    search[Internal search client]
    pivot[Internal pivot]

    c1 --> jwt --> notes --> db
    c2 --> schedule --> audit --> rx
    c3 --> debug --> search --> pivot

    classDef full fill:#e8f6ec,stroke:#1f7a3f,color:#0b2c18;
    classDef component fill:#eef2ff,stroke:#475569,color:#111827;
    classDef sink fill:#f4f4f5,stroke:#52525b,color:#18181b;
    class c1,c2,c3 full;
    class jwt,notes,schedule,audit,debug,search component;
    class db,rx,pivot sink;
```

## Cross-App Readout

```mermaid
flowchart LR
    app05[app-05: 1/3 complete]
    app10[app-10: 1/2 complete]
    app14[app-14: 3/3 complete]
    detected[Detected chains: 5]
    notFull[Not fully detected chains: 3]
    components[Components found: 15/19]

    app05 --> detected
    app10 --> detected
    app14 --> detected
    app05 --> notFull
    app10 --> notFull
    detected --> components
    notFull --> components

    classDef full fill:#e8f6ec,stroke:#1f7a3f,color:#0b2c18;
    classDef partial fill:#fff4d6,stroke:#a66a00,color:#3b2500;
    classDef metric fill:#eef2ff,stroke:#475569,color:#111827;
    class app14,detected full;
    class app05,app10,notFull partial;
    class components metric;
```

The diagrams should be read as evaluator-aligned summaries, not as complete design documentation for each application. They show the surfaces, bridges, and sinks that mattered for the focused chained-audit validation and mark whether GPT-5.4-mini fully connected each expected chain in the final selected attempt.
