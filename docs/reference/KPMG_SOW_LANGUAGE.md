# docs/reference/KPMG_SOW_LANGUAGE.md — house scope-of-work language

Transcribed verbatim from `Product and Tech Due Diligence scope_ITeS company v1.1.pdf`
(© 2024 KPMG India Services LLP). This is the **house voice and structure** the scope
generator must produce. `docs/reference/DD_master.md` supplies the domain depth; this file supplies
the shape, tone and register a KPMG deliverable actually uses.

## What this document establishes

1. **Two scope archetypes**, matching the Enterprise/Product axis in `CLAUDE.md` §2:
   - *Product Due Diligence* — numbered rows, `Objective` → `Scope of Work`.
   - *Enterprise IT Due Diligence* — grouped by `Focus Area` → `Key considerations` bullets.
2. **Register.** Third person, imperative-declarative, verb-led: "Review…", "Assess…",
   "Identify…", "Understand…", "Gain overview of…", "Evaluate…". No first person, no
   hedging, no marketing adjectives. Sentences state what the team will *do*.
3. **Granularity.** Each objective is one line; each scope-of-work entry is one or two
   sentences that name concrete artefacts (roadmap, architecture diagram, SAR audit
   report, EOL asset list, contract register) rather than abstractions.
4. **Structure is a table, not prose.** Output must map cleanly onto rows/bullets.

---

## Product Due Diligence — in-scope areas

Verbatim, `Objective` → `Scope of Work`:

| SN | Objective | Scope of Work |
|---|---|---|
| 1 | Review product tech stack and architecture for scalability constraints | Review technology stack to identify limiting factors for growth, including core architecture, use of legacy languages/ frameworks, interfaces etc. Identify any legacy systems, degree of tech standardization etc. |
| 2 | Technology readiness to support future business growth projections | Review technology platform roadmap and operating model to identify whether adequate planning and resources are available to meet business objectives. |
| 3 | Review product infrastructure to understand scalability constraints | Review scalability of infrastructure to meet deal thesis, including use of cloud services, infrastructure management, performance/ scalability testing performed, and backup/ DR cadence |
| 4 | Review risks related to cyber security posture, and internal IT governance to manage security and privacy | Review IT governance and security framework and testing results (strategy/ policy, governance structure, solutions implemented and managed, testing performed etc.) and initiatives implemented for cybersecurity and data privacy |
| 5 | IT Regulatory aspects | Gain overview of SAR audit report, as well as identify any additional tech related regulatory requirements |
| 6 | Technology team | Understand current capacity and capabilities for the Product tech team, and identify limiting factors from a growth perspective (ex. key personnel, spread of knowledge) |
| 7 | Current IT stack is adequately integrated across internal components and third-party solutions in an automated manner | Review key functionalities in the system and readiness for IT enabled integration across technology platform landscape |
| 8 | Software development lifecyle (SDLC) | Review development and testing methodology, quality metrics, release cadence, Devops capabilities and other associated areas |
| 9 | Technology vendors | Identify major vendors and their role in Tech stack, as well as Tech stack focused on specific clients. Identify accountability and obligations due to tech failure, as well as tenure of contracts and monetary spends obligations due to Tech. |
| 10 | Tech outages and disclosures | Identify any outages, vulnerabilities and other relevant aspects etc. basis disclosures made |

---

## Enterprise IT Due Diligence — in-scope areas

Verbatim, `Focus Area` → `Key considerations`:

### Applications
- Assess key enterprise IT applications, such as ERP, CRM, timesheet system, HRMS, finance and accounting systems (AR, AP, FA, GR etc.) etc. and level of automation enabled for supporting business processes
- Assess IT infrastructure for enterprise IT applications (on cloud and on premise), reviewing end of life assets as well as ability to support planned growth
- Assess list of all the dashboards (Finance, Processes, infrastructure and others) along with the functionalities and KPI including employee productivity

### IT Strategy and Roadmap
- Review enterprise IT roadmap prepared by management, fitment to meet business objectives, and current level of preparedness for the roadmap initiatives

### IT Org and Governance
- Review IT organization including key personnel, responsibilities, skills and areas of specialist knowledge, including any keyperson risk

### IT Infrastructure
- Overview of the infrastructure (on-premise/ cloud) and services including Infra architecture diagram showing the linkage between various infra components, example servers, devices, storage, backup, analytics, availability zones and instances etc.
- Assess details of data centers
- Review implementation of backup, disaster recovery and restoration policy
- Review infrastructure performance metrics are monitored (CPU, disk space, RAM) to allow monitoring of the application performance KPIs, and the processes/mechanisms in place to ensure the infrastructure is scalable and can meet planned business growth
- Assess the status EOL infrastructure

### IT Financials
- Evaluate IT financials and details of how the technology budget is defined and agreed.

### IT Projects
- Review in-flight enterprise projects' status and management's plan for completion of such projects
- Assess all ongoing enterprise IT projects, corresponding budget, resource mapping, current status and estimated date of completion of each project

### Software Development Lifecycle for internal apps
- Review key SDLC (Software Development Life Cycle) applications being leveraged, such as bug management, project management system, knowledge management platform, collaboration and communication platform etc. for custom developed internal applications
- Review SDLC for product development cycle and digital technology
- Review software development processes from requirements definition, through to development, integration, testing and deployment

### Emerging Tech
- Overview of Emerging Technologies such as Analytics, RPA, AI, ML related solutions that have been implemented for enabling key business processes.

### Contracts and Licenses
- Review and Assess of key IT contracts & licenses

---

## House-voice rules for the generator

Derived from the two tables above. The LLM prompt enforces these.

- **Verb-led.** Every scope line opens with Review / Assess / Identify / Understand /
  Evaluate / Gain overview of. Never "We will…", never "The team should consider…".
- **Concrete artefacts.** Name the document or system to be examined, not the concept.
- **Objective vs Scope split.** The objective is the question; the scope of work is the
  activity that answers it. Keep them distinct — do not restate one as the other.
- **Tailoring is factual, not decorative.** Reference the target's actual line of
  business, systems and thesis; do not add adjectives or sales language.
- **British/Indian-English spellings** as in the source ("licences" appears as
  "Licenses" in the headings; follow the source where it is explicit).
- **No invented certainty.** The scope says what will be examined, never what will be
  found.
