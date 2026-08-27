# PART 1 — PROJECT FOUNDATION

---

# Chapter 1 — Project Overview

## 1.1 Project Name

Bon d'Intervention Management System (BIMS)

---

## 1.2 Project Description

The Bon d'Intervention Management System (BIMS) is a web-based application designed to replace the company's current paper-based intervention workflow.

Currently, technicians complete a physical Bon d'Intervention after every intervention performed at a client's premises or inside the company's workshop. The document contains technical information, administrative information, work performed, signatures and various references.

The current workflow is entirely manual.

After completion, the paper document is physically transported to the company where different supervisors validate it before archiving it.

This process introduces several problems including:

- Slow approval
- Risk of losing documents
- Difficult searching
- Difficult reporting
- Manual calculations
- No centralized history
- No planning system
- No dashboard
- No performance indicators

The objective of this project is to digitize the entire workflow while preserving the existing business process used by the company.

The digital application must become the primary platform used by technicians and supervisors while still keeping the scanned (photographed) paper form as the legal signed document.

The application is currently developed as a web application using a synthetic database. The architecture must allow easy migration to the company's real database in the future.

---

# Chapter 2 — Objectives

## 2.1 Main Objective

Create a centralized web platform capable of managing the complete lifecycle of technical interventions from planning to final approval while maintaining complete traceability.

---

## 2.2 Specific Objectives

The application shall:

- Replace paper-only management with digital management.
- Reduce administrative work.
- Improve intervention traceability.
- Preserve the signed paper document by attaching its image.
- Allow technicians to submit interventions digitally.
- Support two-level approval.
- Calculate technician points automatically.
- Calculate working duration automatically.
- Manage intervention planning.
- Dispatch urgent interventions.
- Produce dashboards and KPIs.
- Generate reports.
- Maintain complete intervention history.
- Prevent data loss.
- Eliminate manual calculations.
- Improve productivity.

---

## 2.3 Long-Term Objectives

The architecture should allow future integration of:

- Mobile application
- OCR
- Artificial Intelligence
- Predictive analytics
- Automatic planning optimization
- Cloud deployment
- Multi-company support

These features are outside the scope of the first version.

---

# Chapter 3 — Project Scope

## 3.1 Included Features

Version 1 includes:

### Authentication

- Secure login
- User roles
- Session management

---

### Intervention Management

- Create intervention
- Edit rejected intervention
- Submit intervention
- Attach photographed paper form
- Track intervention status
- View intervention history

---

### Planning

- Create planned interventions
- Assign technicians
- Weekly planning
- Daily planning
- Urgent interventions

---

### Approval

Two-level approval:

1. Chef des Techniciens
2. Administration Supervisor

---

### Dashboard

- Technician dashboard
- Technical supervisor dashboard
- Administration dashboard

---

### Statistics

- KPIs
- Charts
- Reports
- Technician performance
- Client statistics
- City statistics

---

### Notifications

- New intervention
- New assignment
- Urgent intervention
- Approval
- Rejection

---

### Database

- PostgreSQL
- Synthetic demo data

---

# 3.2 Excluded Features

The first version does NOT include:

- OCR
- AI
- Automatic text recognition
- Mobile application
- Client portal
- Email automation
- SMS notifications
- GPS tracking
- Offline synchronization
- Multi-language support

These features may be implemented later.

---

# Chapter 4 — Stakeholders

The application involves several stakeholders.

---

## Technician

Responsible for:

- Performing interventions
- Completing the digital form
- Photographing the signed paper form
- Uploading attachments
- Correcting rejected interventions

---

## Chef des Techniciens

Responsible for:

- Technical validation
- Planning interventions
- Dispatching urgent interventions
- Managing technician workload
- Monitoring technicians

---

## Administration Supervisor

Responsible for:

- Administrative validation
- Checking dates
- Checking formal information
- Final approval
- Report consultation

---

## Company Management

Responsible for:

- Monitoring activity
- Viewing KPIs
- Consulting dashboards
- Evaluating technician productivity

---

## Development Team

Responsible for:

- Designing
- Developing
- Testing
- Maintaining
- Deploying the application

---

# Chapter 5 — Terminology

## Bon d'Intervention (BI)

Official intervention document completed after every intervention.

---

## Intervention

A maintenance, repair, installation or technical operation performed by one or more technicians.

---

## Technician

Employee responsible for executing interventions.

---

## Chef des Techniciens

Supervisor responsible for validating the technical aspect of interventions and organizing technician planning.

---

## Administration Supervisor

Supervisor responsible for validating the administrative aspect of interventions.

---

## Client

Company receiving technical services.

A client may own one or multiple sites located in different cities.

Example:

Client:

Orange Maroc

Sites:

- Agadir
- Casablanca
- Rabat

The intervention is associated with the specific client site where it was performed.

---

## City

Represents the intervention location.

Cities are stored in the database.

They are not entered manually.

---

## Contract

A maintenance agreement signed between the company and the client.

Contracts are selected from the database.

---

## Project

A long-term activity involving multiple interventions.

Projects are selected from the database.

---

## Travaux

A predefined catalog of technical operations.

Each task contains:

- Task Number
- Task Name

Example:

101 - Firewall Installation

205 - Fiber Repair

412 - Server Maintenance

Technicians select one or more predefined tasks instead of writing them manually.

---

## Warranty Intervention

A new intervention created because a previous intervention did not completely resolve the problem.

The warranty intervention has:

- its own BI number
- a reference to the previous intervention

Example:

BI000015

↓

Problem persists

↓

BI000042 (Warranty)

Reference:

BI000015

---

## Planned Intervention

An intervention scheduled in advance by the Chef des Techniciens.

---

## Urgent Intervention

An intervention requiring immediate execution.

Urgent interventions have higher priority than planned interventions.

---

## Attachment

Photograph or uploaded image of the signed paper Bon d'Intervention.

Every submitted intervention must include at least one attachment.

OCR is not used.

The image is stored only as documentary evidence.

---

## Approval

Validation performed by supervisors.

There are two approvals:

Technical Approval

Administrative Approval

An intervention is considered finalized only after both approvals have been completed.
# PART 2 — BUSINESS ANALYSIS

---

# Chapter 6 — Current Paper Workflow

## 6.1 Current Process

The company currently manages all interventions using physical paper forms called **Bon d'Intervention (BI)**.

Each intervention follows the workflow below.

---

### Step 1 — Intervention Assignment

The company receives an intervention request from a client.

The request may be:

- Planned in advance.
- Part of a maintenance contract.
- Related to a project.
- An urgent intervention.

The Chef des Techniciens assigns one or more technicians.

---

### Step 2 — Technician Performs the Work

The technician travels to:

- The client's premises (Sur Site)

or

- Repairs equipment inside the company workshop (Atelier)

The technician performs the requested work.

---

### Step 3 — Paper Bon d'Intervention

After completing the work, the technician manually fills a paper BI.

Typical information includes:

- Client
- City
- Date
- Technician
- Work performed
- Intervention type
- Duration
- Comments
- Client signature

---

### Step 4 — Client Signature

The client verifies the intervention.

If satisfied:

- Signs the paper BI.

The signed document becomes the legal proof that the intervention was completed.

---

### Step 5 — Return to Company

The technician physically returns the paper BI to the company.

This may happen:

- Later the same day
- The following day
- Several days later

---

### Step 6 — Technical Validation

The Chef des Techniciens reviews the intervention.

Checks include:

- Technical quality
- Work performed
- Correct intervention type
- Technical comments

If accepted:

The BI continues to the next approval.

Otherwise:

Corrections are requested.

---

### Step 7 — Administrative Validation

The Administration Supervisor verifies:

- Dates
- Administrative information
- Completeness
- Formal correctness

If approved:

The BI becomes officially validated.

---

### Step 8 — Archiving

The paper BI is archived.

Finding it later requires manual searching.

---

# Chapter 7 — Problems With The Current Workflow

The current paper system creates several operational problems.

---

## 7.1 Document Loss

Paper documents may be:

- Lost
- Damaged
- Misfiled

---

## 7.2 Slow Validation

Approvals cannot begin until the paper reaches the company.

This delays the workflow.

---

## 7.3 Manual Calculations

The company manually calculates:

- Working duration
- Technician points

This increases errors.

---

## 7.4 Difficult Searching

Searching requires manually browsing physical archives.

Finding an intervention may take several minutes or even hours.

---

## 7.5 No Planning Module

The company has no centralized planning system.

Assignments are communicated manually.

---

## 7.6 No Notification System

Technicians receive intervention assignments through phone calls or verbal communication.

There is no centralized notification platform.

---

## 7.7 No Statistics

Management cannot easily answer questions such as:

- How many interventions were completed this month?
- Which technician completed the most interventions?
- Which clients generate the highest workload?
- Average intervention duration?
- Number of urgent interventions?

---

## 7.8 Duplicate Information

Information exists only on paper.

Any digital processing requires manually rewriting the same data.

---

## 7.9 Limited Traceability

It is difficult to determine:

- Who modified information.
- Who approved it.
- When it was approved.
- Why it was rejected.

---

# Chapter 8 — Proposed Digital Workflow

## 8.1 General Principle

The digital application reproduces the existing business workflow while eliminating manual administration.

The paper BI remains important because it contains the client's handwritten signature.

However, instead of transporting only the paper, the technician also submits a digital version immediately.

---

## 8.2 New Workflow

Client requests intervention

↓

Chef des Techniciens schedules intervention

↓

Technician receives assignment

↓

Technician performs intervention

↓

Technician completes digital BI

↓

Technician photographs or uploads the signed paper BI

↓

Technician submits both together

↓

Technical approval

↓

Administrative approval

↓

Intervention becomes fully approved

↓

Stored permanently

↓

Available for dashboards and reports

---

# Chapter 9 — Digital Intervention Lifecycle

Each intervention passes through predefined states.

---

## State 1 — Planned

Created by:

Chef des Techniciens

Characteristics:

- Assigned technician
- Planned date
- Planned time
- Client
- Priority

The intervention has not yet started.

---

## State 2 — In Progress

The technician has started the intervention.

Only the assigned technician may edit it.

---

## State 3 — Draft

The technician has saved the intervention but has not submitted it.

Editable.

---

## State 4 — Submitted

The technician submits:

- Digital form
- Attached photograph of the signed paper BI

The intervention becomes read-only for the technician until a decision is made.

---

## State 5 — Pending Technical Approval

Waiting for:

Chef des Techniciens

Possible actions:

Approve

Reject

---

## State 6 — Technical Approved

Technical validation completed.

The intervention automatically moves to:

Pending Administrative Approval.

---

## State 7 — Pending Administrative Approval

Waiting for:

Administration Supervisor.

Possible actions:

Approve

Reject

---

## State 8 — Fully Approved

Both supervisors approved.

Characteristics:

- Locked permanently.
- No editing.
- No deletion.
- Included in reports.
- Included in KPIs.

---

## State 9 — Rejected

Returned to the technician.

Technician may:

- Correct data.
- Upload another attachment if necessary.
- Submit again.

The rejection history remains stored.

---

# Chapter 10 — High-Level Business Rules

## Rule 1

Every intervention must belong to exactly one client.

---

## Rule 2

Every intervention must reference one client site (city).

Example:

Client:

Orange Maroc

Sites:

- Agadir

- Casablanca

- Rabat

The technician chooses the correct site, not only the client.

---

## Rule 3

Clients cannot be typed manually.

They are selected from the database.

---

## Rule 4

Cities cannot be typed manually.

They are automatically filtered based on the selected client.

Example:

Client:

Orange Maroc

↓

Available cities:

- Agadir
- Casablanca
- Rabat

Client:

Bank X

↓

Available cities:

- Marrakech
- Agadir

This prevents selecting invalid client-city combinations.

---

## Rule 5

Technician names are never entered manually.

They are automatically filled from the logged-in session.

---

## Rule 6

Every intervention receives a unique BI number generated automatically.

Example:

BI000001

BI000002

BI000003

Technicians cannot modify it.

---

## Rule 7

Every submitted intervention must contain at least one attached image of the signed paper BI.

Without an attachment, submission is not allowed.

---

## Rule 8

The application does not perform OCR.

Uploaded images are stored only as documentary evidence.

All intervention information is entered manually into the digital form.

---

## Rule 9

Interventions can never be deleted.

Only their status changes.

This guarantees complete traceability.

---

## Rule 10

Every important action is timestamped.

Examples:

- Creation
- Submission
- Technical approval
- Administrative approval
- Rejection
- Modification

The application maintains a complete audit trail.
# PART 3 — USERS, ROLES & PERMISSIONS

---

# Chapter 11 — User Roles

The application contains only three user roles.

There is **no separate administrator**.

Administrative responsibilities are performed by the Administration Supervisor.

---

## 1. Technician

The technician is responsible for performing interventions and recording them in the system.

The technician cannot validate interventions.

The technician only manages interventions assigned to him.

---

## 2. Chef des Techniciens

The Chef des Techniciens is responsible for:

- Managing technicians
- Planning interventions
- Dispatching urgent interventions
- Technical validation
- Monitoring workloads

The Chef does not perform the final administrative validation.

---

## 3. Administration Supervisor

The Administration Supervisor is responsible for:

- Administrative validation
- User management
- Client management
- Contracts
- Projects
- Travaux catalog
- Dashboard consultation
- Reports
- Application administration

This role replaces the traditional system administrator.

---

# Chapter 12 — Permissions

---

## Technician Permissions

### Allowed

✔ Login

✔ Logout

✔ View own profile

✔ View assigned interventions

✔ View planned interventions

✔ View urgent interventions

✔ Create intervention

✔ Save intervention as Draft

✔ Submit intervention

✔ Upload photograph of signed paper BI

✔ Modify Draft intervention

✔ Modify Rejected intervention

✔ View intervention history

✔ Receive notifications

✔ View personal calendar

---

### Not Allowed

✖ Delete intervention

✖ Approve interventions

✖ Reject interventions

✖ Modify approved interventions

✖ Modify interventions belonging to another technician

✖ Assign interventions

✖ Manage users

✖ Manage clients

✖ Manage contracts

✖ View company statistics

---

## Chef des Techniciens Permissions

### Allowed

Everything available to technicians plus:

✔ View all technicians

✔ View all interventions

✔ Create planned interventions

✔ Modify planning

✔ Assign technicians

✔ Reassign technicians

✔ Create urgent interventions

✔ Change priorities

✔ Technical approval

✔ Technical rejection

✔ View technician workload

✔ View planning calendar

✔ Search interventions

✔ Filter interventions

✔ Dashboard consultation

---

### Not Allowed

✖ Final administrative approval

✖ Delete interventions

✖ Delete users

✖ Delete clients

---

## Administration Supervisor Permissions

### Allowed

Everything except technical approval.

Additionally:

✔ Administrative approval

✔ Administrative rejection

✔ Manage users

✔ Manage clients

✔ Manage cities

✔ Manage contracts

✔ Manage projects

✔ Manage Travaux catalog

✔ Dashboard access

✔ Reports

✔ KPI consultation

✔ Export reports

✔ User activation

✔ User deactivation

✔ Reset passwords

---

### Not Allowed

✖ Delete intervention history

✖ Delete approval history

---

# Chapter 13 — Authentication

---

## Login

Every user receives:

- Username
- Password

After authentication, JWT authentication is used.

---

## Automatic Session

Once connected:

The application automatically knows:

- User ID
- Full Name
- Role
- Department

The technician therefore never types his own name.

The "Nom du Technicien" field is automatically filled.

---

## Session Expiration

Inactive sessions automatically expire.

The user must log in again.

---

# Chapter 14 — User Workflow

---

## Technician Workflow

Login

↓

Dashboard

↓

Today's interventions

↓

Open assigned intervention

or

Create new intervention

↓

Fill digital BI

↓

Attach paper BI image

↓

Submit

↓

Wait for approval

↓

If rejected:

Correct

↓

Resubmit

↓

If approved:

Read-only

---

## Chef des Techniciens Workflow

Login

↓

Dashboard

↓

Pending technical approvals

↓

Review intervention

↓

Compare with attachment

↓

Approve

or

Reject

↓

Planning

↓

Assign new interventions

↓

Dispatch urgent interventions

---

## Administration Supervisor Workflow

Login

↓

Dashboard

↓

Pending administrative approvals

↓

Review intervention

↓

Review dates

↓

Review client information

↓

Approve

or

Reject

↓

Generate reports

↓

Dashboard

---

# Chapter 15 — Intervention Ownership

Every intervention has exactly one owner.

Owner = Assigned Technician

Only the owner can:

- Edit Draft
- Edit Rejected intervention

Nobody else can modify intervention content.

Supervisors only validate.

---

# Chapter 16 — Intervention Visibility

---

## Technician

Can see:

- Own interventions

Cannot see:

- Other technicians' interventions

---

## Chef des Techniciens

Can see:

- Every intervention

Can filter by:

- Technician
- Client
- City
- Date
- Status
- Priority

---

## Administration Supervisor

Can see every intervention.

Additional filters:

- Approval state
- Technical approval
- Administrative approval
- Date range

---

# Chapter 17 — Intervention Locking

The application automatically locks interventions.

---

## Draft

Editable

---

## Submitted

Locked

Waiting for technical approval.

---

## Technical Approved

Still locked.

Waiting for administrative approval.

---

## Fully Approved

Permanently locked.

No edits allowed.

---

## Rejected

Unlocked.

Technician can modify.

After resubmission:

Locked again.

---

# Chapter 18 — Audit Trail

Every important action is recorded.

Examples:

Created

↓

Saved Draft

↓

Modified

↓

Submitted

↓

Technical Approval

↓

Administrative Approval

↓

Rejected

↓

Resubmitted

Each event stores:

- User
- Date
- Time
- Action
- Optional comment

Nothing is deleted.

---

# Chapter 19 — General Security Rules

Passwords are encrypted.

JWT tokens secure every request.

Every API verifies user permissions.

Users cannot access pages outside their role.

Example:

Technician attempting to access:

/admin/users

↓

Access denied.

---

# Chapter 20 — Data Integrity Rules

The system enforces the following rules:

- BI numbers are unique.
- Every intervention belongs to one technician.
- Every intervention belongs to one client.
- Every intervention belongs to one client site.
- Every intervention has one status.
- Every approval stores its approver.
- Every approval stores its timestamp.
- Every submitted intervention has at least one attached image.
- Approved interventions cannot be modified.
- Interventions are never physically deleted.
- All changes remain traceable through the audit history.
# PART 4 — CORE BUSINESS LOGIC

---

# Chapter 21 — Intervention Creation

The intervention is the core object of the application.

Every intervention represents one maintenance, installation, repair or technical operation carried out by one or more technicians.

Every intervention receives a unique BI number generated automatically by the system.

Example:

BI000001

BI000002

BI000003

Technicians never enter this number manually.

---

## Intervention Creation Workflow

Technician logs in

↓

Opens Dashboard

↓

Selects "New Intervention"

↓

Completes the digital form

↓

Attaches image(s) of signed paper BI

↓

Saves as Draft or Submits

---

# Chapter 22 — Intervention Form

The intervention form contains the following sections.

---

## Section A — General Information

### BI Number

- Generated automatically
- Read only
- Unique

---

### Technician

Automatically filled using the logged-in user.

Cannot be modified.

---

### Intervention Date

Date the intervention occurred.

Default:

Today's date.

Can be changed if necessary.

---

### Submission Date

Automatically generated.

Read only.

---

### Technical Approval Date

Automatically generated after technical approval.

Read only.

---

### Administrative Approval Date

Automatically generated after administrative approval.

Read only.

---

# Section B — Client Information

---

## Client

Dropdown list.

Loaded from database.

Cannot be typed manually.

Example:

Orange Maroc

Maroc Telecom

Bank Al-Maghrib

Attijariwafa Bank

---

## Client Site (City)

Depends on selected client.

Example

Client

Orange Maroc

↓

Cities available

Agadir

Casablanca

Rabat

If another client is selected, the list changes automatically.

This prevents invalid client-city combinations.

---

## Contact Person (Optional)

Text field.

Example

Mr. Ahmed

---

# Section C — Intervention Type

Only one intervention type may be selected.

Dropdown list.

Possible values:

- Standard
- Contract
- Project
- Warranty

---

## Standard Intervention

Regular intervention.

No additional information required.

---

## Contract Intervention

Additional field appears.

Contract

↓

Dropdown from database.

Example

Maintenance Contract 2025

---

## Project Intervention

Additional field appears.

Project

↓

Dropdown from database.

Example

Fiber Expansion Project

---

## Warranty Intervention

Additional field appears.

Previous BI Number

Text field or searchable lookup.

Example

Current BI

BI000081

Warranty Reference

BI000055

The referenced BI must already exist.

---

# Section D — Location

The technician chooses:

Sur Site

or

Atelier

Only one option.

---

## Sur Site

Work performed at the client's premises.

---

## Atelier

Equipment repaired inside company workshop.

---

# Section E — Time Information

---

## Start Time

Selected manually.

---

## End Time

Selected manually.

---

## Lunch Break

Checkbox

"No Lunch Break"

↓

Lunch Break = 0

If unchecked:

User selects:

30 min

1 hour

1.5 hours

2 hours

Custom duration

---

## Net Duration

Calculated automatically.

Formula

Net Duration

=

End Time

-

Start Time

-

Lunch Break

Displayed automatically.

Cannot be modified manually.

---

# Section F — Number of Technicians

Field:

Number of Technicians

Example

1

2

3

5

Optional list of accompanying technicians may be added later.

---

# Section G — Travaux Effectués

Dropdown list.

Loaded from database.

Each task contains

Task Number

Task Name

Example

101 - Firewall Installation

205 - Fiber Repair

330 - Server Maintenance

415 - Camera Configuration

One or more tasks may be selected.

Free typing is not allowed.

---

# Section H — Comments

Large text area.

Technician describes:

- Problem
- Solution
- Notes
- Recommendations

---

# Section I — Attachments

Mandatory.

Technician must attach the signed paper BI.

Methods

Take Photo

Upload Image

Multiple images allowed.

Accepted formats

JPG

JPEG

PNG

PDF (optional)

No OCR is performed.

The attachment is stored only as documentary evidence.

---

# Chapter 23 — Draft Logic

The technician may save the intervention without submitting it.

Status

Draft

Characteristics

Editable

Visible only to technician

No approvals

No notifications

Drafts may be modified unlimited times.

---

# Chapter 24 — Submission Logic

Submission requires:

Client selected

↓

Client Site selected

↓

Intervention Type selected

↓

Times completed

↓

Travaux selected

↓

Attachment uploaded

↓

Validation successful

↓

Submit

Status changes

Draft

↓

Submitted

Automatic actions

Record submission date

Generate notification

Send to Chef des Techniciens

Lock intervention

---

# Chapter 25 — Technical Approval

Chef des Techniciens receives notification.

Pending interventions appear in dashboard.

Supervisor reviews

Digital form

+

Attached paper BI

Possible actions

Approve

Reject

---

## If Approved

System stores

Technical approver

Approval date

Approval time

Comment (optional)

Status

Technical Approved

↓

Pending Administrative Approval

Administration Supervisor notified.

---

## If Rejected

Supervisor enters rejection reason.

Status

Rejected

Intervention unlocked.

Technician notified.

---

# Chapter 26 — Administrative Approval

Administration Supervisor reviews

Client

Dates

Duration

Administrative information

Attachment

Possible actions

Approve

Reject

---

## Administrative Approval

Stores

Approver

Date

Time

Comment

Status

Fully Approved

Intervention permanently locked.

---

## Administrative Rejection

Stores

Reason

Date

Time

Technician notified.

Status

Rejected

Editable again.

---

# Chapter 27 — Duration Logic

Input

08:00

↓

17:30

Lunch

1 hour

Calculation

17:30

-

08:00

=

9h30

9h30

-

1h

=

8h30

Display

Gross Duration

9h30

Lunch Break

1h

Net Duration

8h30

---

# Chapter 28 — Point System

Points depend on submission time.

Submission Time

17:00–19:00

↓

+5 Points

19:00–22:00

↓

+2 Points

22:00–24:00

↓

+1 Point

After 00:00

↓

Negative points (exact value configurable)

The application calculates points automatically.

Technicians cannot modify them.

Monthly totals appear on dashboards.

---

# Chapter 29 — Planning Logic

Chef des Techniciens creates planned interventions.

Required fields

Client

Client Site

Technician

Date

Start Time

Priority

Intervention Type

Notes

Status

Planned

Technician immediately sees the intervention in their calendar.

---

# Chapter 30 — Urgent Intervention Logic

Urgent interventions bypass normal planning.

Priority

Urgent

Automatic actions

Notification sent

↓

Appears at top of technician dashboard

↓

Highlighted in calendar

↓

Technician performs urgent work first

↓

Returns to planned interventions afterwards

Urgent interventions remain identifiable throughout their lifecycle.

---

# Chapter 31 — Notification Logic

Technician receives notifications when:

- New intervention assigned
- Urgent intervention assigned
- Intervention rejected
- Intervention fully approved

Chef des Techniciens receives notifications when:

- Technician submits intervention

Administration Supervisor receives notifications when:

- Technical approval completed
- Administrative approval required

Notifications contain

Title

Message

Date

Related BI Number

Status

Read / Unread

---

# Chapter 32 — Business Rules Summary

The following rules are mandatory:

- BI numbers are automatically generated.
- Technician names come from the logged-in session.
- Clients are selected only from the database.
- Client sites depend on the selected client.
- Contracts come only from the database.
- Projects come only from the database.
- Travaux come only from the database.
- Every submitted intervention requires at least one attachment.
- OCR is not used.
- Drafts are editable.
- Submitted interventions are locked.
- Approved interventions are permanently locked.
- Rejected interventions become editable again.
- Interventions are never deleted.
- Every approval stores the approver, date and time.
- Every modification is recorded in the audit history.
- Every important action generates notifications when appropriate.
# PART 5 — DATABASE DESIGN & DATA MODEL

---

# Chapter 33 — Database Overview

The application uses a relational PostgreSQL database.

The database is normalized to reduce redundancy and preserve data integrity.

During development, the database contains only synthetic (demo) data.

The schema, however, must be production-ready so that replacing the demo data with the company's real data requires little to no structural changes.

---

# Chapter 34 — Main Entities

The system is composed of the following entities:

- Users
- Roles
- Clients
- Client Sites (Cities)
- Contracts
- Projects
- Travaux
- Interventions
- Intervention Tasks
- Attachments
- Planning
- Notifications
- Approval History

---

# Chapter 35 — Users

Stores every user of the application.

Fields

- UserID (PK)
- FirstName
- LastName
- Username
- PasswordHash
- Email
- Phone
- RoleID (FK)
- Active
- CreatedAt
- UpdatedAt

---

# Chapter 36 — Roles

Contains the three application roles.

Fields

- RoleID
- RoleName

Values

- Technician
- Chef des Techniciens
- Administration Supervisor

No Administrator role exists.

---

# Chapter 37 — Clients

Stores company customers.

Fields

- ClientID
- ClientName
- Phone
- Email
- Active

Examples

Orange Maroc

Maroc Telecom

Bank Al-Maghrib

Attijariwafa Bank

---

# Chapter 38 — Client Sites

A client may own multiple intervention sites.

Instead of storing only the city, every client site is stored separately.

Fields

- SiteID
- ClientID (FK)
- SiteName
- City
- Address

Example

Client

Orange Maroc

↓

Sites

Agadir Headquarters

Casablanca Datacenter

Rabat Agency

The intervention references the SiteID instead of only the city.

---

# Chapter 39 — Contracts

Stores maintenance contracts.

Fields

- ContractID
- ClientID
- ContractName
- StartDate
- EndDate
- Status

Only visible when Intervention Type = Contract.

---

# Chapter 40 — Projects

Stores company projects.

Fields

- ProjectID
- ClientID
- ProjectName
- StartDate
- EndDate
- Status

Only visible when Intervention Type = Project.

---

# Chapter 41 — Travaux Catalog

Contains predefined technical operations.

Fields

- TravailID
- TravailCode
- TravailName
- Category
- Active

Example

101

Firewall Installation

---

205

Fiber Repair

---

330

Server Maintenance

---

415

Camera Configuration

Technicians select tasks from this table.

Free typing is not allowed.

---

# Chapter 42 — Interventions

The most important table.

Fields

- InterventionID
- BINumber
- TechnicianID
- ClientID
- SiteID
- ContractID (nullable)
- ProjectID (nullable)
- WarrantyReferenceID (nullable)
- InterventionType
- LocationType
- StartTime
- EndTime
- LunchBreak
- NetDuration
- NumberOfTechnicians
- TechnicalReport
- Status
- SubmissionDate
- TechnicalApprovalDate
- AdministrativeApprovalDate
- PointsEarned
- CreatedAt
- UpdatedAt

---

# Chapter 43 — Intervention Tasks

One intervention may contain multiple tasks.

Relationship

One Intervention

↓

Many Tasks

Fields

- InterventionTaskID
- InterventionID
- TravailID

Example

BI000123

↓

101

↓

330

↓

415

---

# Chapter 44 — Attachments

Stores uploaded images.

Fields

- AttachmentID
- InterventionID
- FileName
- FilePath
- UploadDate
- UploadedBy

Supported formats

- JPG
- JPEG
- PNG
- PDF

OCR is not performed.

---

# Chapter 45 — Planning

Stores planned interventions.

Fields

- PlanningID
- TechnicianID
- ClientID
- SiteID
- PlannedDate
- PlannedStartTime
- EstimatedDuration
- Priority
- Status
- Notes

---

# Chapter 46 — Notifications

Stores system notifications.

Fields

- NotificationID
- UserID
- Title
- Message
- RelatedInterventionID
- Read
- CreatedAt

---

# Chapter 47 — Approval History

Every approval action is stored permanently.

Fields

- ApprovalID
- InterventionID
- ApprovalLevel
- ApprovedBy
- Decision
- Comment
- ApprovalDate

ApprovalLevel

Technical

Administrative

Decision

Approved

Rejected

Nothing is deleted.

---

# Chapter 48 — Entity Relationships

Role

↓

Users

↓

Interventions

↓

Attachments

↓

Approval History

↓

Notifications

Client

↓

Client Sites

↓

Interventions

Contract

↓

Interventions

Project

↓

Interventions

Travaux

↓

Intervention Tasks

↓

Interventions

Planning

↓

Users

↓

Interventions

---

# Chapter 49 — Database Constraints

The database must enforce:

- Every user has exactly one role.
- Every intervention belongs to one technician.
- Every intervention belongs to one client.
- Every intervention belongs to one client site.
- Every attachment belongs to one intervention.
- Every notification belongs to one user.
- Every approval belongs to one intervention.
- Every intervention has exactly one current status.
- Every BI number is unique.
- Foreign keys cannot be broken.

---

# Chapter 50 — Cascade Rules

Deleting records is generally forbidden.

Instead of deleting:

Users

↓

Set Active = False

Clients

↓

Set Active = False

Travaux

↓

Set Active = False

Projects

↓

Archived

Contracts

↓

Archived

Interventions

↓

Never deleted

This preserves historical integrity.

---

# Chapter 51 — Synthetic Database

Until the production database is available, create realistic demo data.

Example

Users

- 10 Technicians
- 2 Chef des Techniciens
- 2 Administration Supervisors

Clients

15–20 companies

Client Sites

40–60 sites

Contracts

20+

Projects

10+

Travaux

100+

Interventions

300–500 sample records

Planning

100 future interventions

Notifications

100 sample notifications

Approval History

Linked to every completed intervention

The synthetic data should resemble real operational activity.

---

# Chapter 52 — Indexing

Indexes should be created for:

- BINumber
- TechnicianID
- ClientID
- SiteID
- Status
- PlannedDate
- SubmissionDate
- ApprovalDate

This ensures good performance when thousands of interventions exist.

---

# Chapter 53 — Database Growth

The system should comfortably support:

- 60+ interventions/day
- Hundreds/week
- Thousands/month
- Tens of thousands historically

The schema should not require redesign as data volume increases.
# PART 6 — USER INTERFACE & APPLICATION MODULES

---

# Chapter 54 — Application Structure

The application is divided into the following major modules:

1. Authentication
2. Technician Module
3. Chef des Techniciens Module
4. Administration Supervisor Module
5. Planning Module
6. Intervention Management
7. Dashboard & KPIs
8. Reports
9. Notifications
10. Settings

Every module is accessible according to the user's role.

---

# Chapter 55 — Login Module

## Login Page

Fields

- Username
- Password

Buttons

- Login

Features

- JWT Authentication
- Session creation
- Automatic role detection

After login, the user is redirected to the appropriate dashboard.

Technician

↓

Technician Dashboard

Chef des Techniciens

↓

Supervisor Dashboard

Administration Supervisor

↓

Administration Dashboard

---

# Chapter 56 — Technician Dashboard

The technician dashboard is the home page after login.

It contains:

## KPI Cards

- Planned Interventions Today
- Completed Today
- Pending Approval
- Rejected
- Monthly Points

---

## Quick Actions

- New Intervention
- My Calendar
- My Interventions

---

## Notifications

Recent notifications

Example

- Intervention Approved
- Intervention Rejected
- New Assignment
- Urgent Intervention

---

## Today's Planning

Shows today's planned interventions.

Information displayed:

- BI Number
- Client
- Site
- Time
- Priority
- Status

---

# Chapter 57 — New Intervention Page

The technician creates a new intervention here.

The page is divided into logical sections.

## General Information

- BI Number
- Technician
- Date

---

## Client Information

- Client
- Client Site

---

## Intervention Information

- Intervention Type
- Contract (if applicable)
- Project (if applicable)
- Warranty Reference (if applicable)

---

## Time

- Start Time
- End Time
- Lunch Break
- Net Duration

---

## Location

- Sur Site
- Atelier

---

## Technical Work

- Travaux (Dropdown)
- Technical Report

---

## Attachments

- Camera
- Upload Image

---

## Bottom Buttons

Save Draft

Submit

Cancel

---

# Chapter 58 — My Interventions

Technicians can view all their interventions.

Tabs

- Draft
- Planned
- Submitted
- Rejected
- Approved

Each row shows

- BI Number
- Client
- Date
- Status
- Priority

Search is available.

Filters

- Date
- Status
- Client

---

# Chapter 59 — Technician Calendar

Calendar views

- Daily
- Weekly
- Monthly

Each intervention is represented by a colored card.

Colors

Blue

Planned

Green

Completed

Orange

Pending Approval

Red

Urgent

Gray

Rejected

Clicking an intervention opens its details.

---

# Chapter 60 — Intervention Details

Displays every field.

General Information

↓

Client Information

↓

Intervention Information

↓

Technical Report

↓

Attachments

↓

Approval History

↓

Timeline

If editable

↓

Edit button

Otherwise

↓

Read-only

---

# Chapter 61 — Chef des Techniciens Dashboard

The supervisor dashboard focuses on operational management.

Cards

- Pending Technical Approvals
- Today's Planned Interventions
- Urgent Interventions
- Active Technicians
- Weekly Activity

Recent submissions appear immediately.

---

# Chapter 62 — Technical Approval Page

Table containing interventions awaiting validation.

Columns

- BI Number
- Technician
- Client
- Site
- Submission Date
- Priority

Buttons

View

Approve

Reject

Clicking View opens the intervention.

Supervisor can compare

Digital Form

+

Uploaded Paper BI

---

# Chapter 63 — Planning Module

Planning is managed through a calendar.

Views

Daily

Weekly

Monthly

Each intervention can be

Created

Edited

Moved

Reassigned

Priority changed

---

Planning window

Contains

Client

↓

Site

↓

Technician

↓

Date

↓

Time

↓

Estimated Duration

↓

Priority

↓

Notes

↓

Save

---

# Chapter 64 — Urgent Intervention

Chef des Techniciens creates an urgent intervention.

Priority options

Normal

High

Urgent

Urgent interventions

Generate notification

Appear first

Use a red indicator

Remain highlighted until completed

---

# Chapter 65 — Administration Dashboard

Displays

Pending Administrative Approvals

Monthly Activity

Approval Statistics

Recent Reports

Technician Performance

Charts

---

# Chapter 66 — Administrative Approval Page

Very similar to Technical Approval.

Additional verification

Dates

Client

Duration

Administrative consistency

Buttons

Approve

Reject

View Attachment

Approval permanently finalizes the intervention.

---

# Chapter 67 — Dashboard Module

Every role has a different dashboard.

---

## Technician Dashboard

Personal KPIs

Personal interventions

Personal notifications

---

## Chef Dashboard

Team KPIs

Planning

Pending technical approvals

Technician workload

---

## Administration Dashboard

Global KPIs

Reports

Statistics

Approval rates

---

# Chapter 68 — Search System

The application includes a global search.

Search by

- BI Number
- Client
- Site
- Technician
- Project
- Contract

Search updates results instantly.

---

# Chapter 69 — Filters

Available filters

Date

Client

Technician

Status

Priority

Project

Contract

Site

Intervention Type

Multiple filters can be combined.

---

# Chapter 70 — Notifications

Notification Center

Displays

Title

Message

Time

Read Status

Clicking a notification opens the related intervention.

Unread notifications are highlighted.

---

# Chapter 71 — Reports

Available reports

Daily

Weekly

Monthly

Yearly

Technician Report

Client Report

Project Report

Contract Report

Approval Report

Planning Report

Reports can be exported as

PDF

Excel

---

# Chapter 72 — Responsive Design

The application is Web-only.

Supported devices

Desktop

Laptop

Tablet

Mobile Browser

The layout must automatically adapt to screen size.

---

# Chapter 73 — Navigation

Main sidebar

Dashboard

↓

Planning

↓

Interventions

↓

Calendar

↓

Approvals

↓

Reports

↓

Notifications

↓

Settings

The menu changes depending on the logged-in role.

Example

Technicians do not see

- User Management
- Reports
- Planning Management

Administration Supervisors see all available modules.

---

# Chapter 74 — UI Principles

The interface should follow these principles:

- Minimal clicks to complete common tasks.
- Consistent page layouts.
- Responsive design.
- Fast navigation.
- Search available on all large lists.
- Pagination for large datasets.
- Color-coded statuses and priorities.
- Read-only fields clearly distinguished from editable fields.
- Confirmation dialogs for important actions (submit, approve, reject).
- Form validation before submission.
- Clear success and error messages.
- Accessibility-friendly components where possible.
# PART 7 — BACKEND ARCHITECTURE & API DESIGN

---

# Chapter 75 — Backend Overview

The backend is responsible for all business processing and communication between the frontend and the PostgreSQL database.

The backend exposes a REST API consumed by the React frontend.

Technology Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- JWT Authentication

---

# Chapter 76 — Backend Architecture

Use a layered architecture to keep the project maintainable.

```
Frontend (React)
        │
        ▼
 REST API (FastAPI)
        │
        ▼
 Business Logic (Services)
        │
        ▼
 Database Layer (Repositories)
        │
        ▼
 PostgreSQL
```

Each layer has one responsibility.

---

# Chapter 77 — Project Structure

```
backend/

├── app/
│
├── api/
│
├── models/
│
├── schemas/
│
├── services/
│
├── repositories/
│
├── authentication/
│
├── middleware/
│
├── database/
│
├── utils/
│
├── uploads/
│
├── static/
│
├── main.py
│
└── config.py
```

---

# Chapter 78 — Responsibilities

## Models

Database tables.

Example

- User
- Client
- Intervention
- Planning

---

## Schemas

Request/Response validation.

Example

Create Intervention

↓

Validate

↓

Save

---

## Services

Contains all business logic.

Examples

- Point calculation
- Duration calculation
- Approval workflow
- Notification creation
- Planning logic

Business rules should **only** exist here.

Never duplicate business logic inside React.

---

## Repositories

Responsible for database queries.

Example

findUser()

saveIntervention()

updatePlanning()

---

## API

Receives HTTP requests.

Calls Services.

Returns JSON.

Contains no business logic.

---

# Chapter 79 — Authentication

Authentication uses JWT.

Workflow

Login

↓

Username + Password

↓

Password Verification

↓

JWT Generated

↓

Returned to Frontend

↓

Stored securely

↓

Used for every request

---

Protected endpoints verify:

- Token validity
- User existence
- User role
- Permissions

---

# Chapter 80 — Authorization

Role permissions are enforced by the backend.

Example

Technician

↓

POST

/interventions

Allowed

---

Technician

↓

POST

/technical-approval

Forbidden

---

Administration Supervisor

↓

POST

/admin/users

Allowed

---

The frontend should hide inaccessible pages, but the backend must always enforce permissions.

---

# Chapter 81 — File Upload

Each submitted intervention requires at least one attachment.

Supported formats

- JPG
- JPEG
- PNG
- PDF

Maximum size should be configurable (e.g. 10 MB).

Workflow

Upload

↓

Validate format

↓

Store file

↓

Save database record

↓

Link to Intervention

OCR is not performed.

Files are stored only as documentary evidence.

---

# Chapter 82 — Error Handling

Every API returns standardized responses.

Success

```json
{
  "success": true,
  "message": "Intervention created.",
  "data": { ... }
}
```

Error

```json
{
  "success": false,
  "message": "Client not found."
}
```

Validation errors

```json
{
  "success": false,
  "errors": [
    "Client is required",
    "Start Time is required"
  ]
}
```

---

# Chapter 83 — Main API Modules

Authentication

```
POST /login

POST /logout

GET /me
```

---

Users

```
GET /users

POST /users

PUT /users/{id}

PATCH /users/{id}/activate

PATCH /users/{id}/deactivate
```

---

Clients

```
GET /clients

POST /clients

PUT /clients/{id}
```

---

Client Sites

```
GET /sites

GET /clients/{id}/sites

POST /sites
```

---

Projects

```
GET /projects

POST /projects
```

---

Contracts

```
GET /contracts

POST /contracts
```

---

Travaux

```
GET /travaux

POST /travaux

PUT /travaux/{id}
```

---

Interventions

```
GET /interventions

GET /interventions/{id}

POST /interventions

PUT /interventions/{id}
```

---

Planning

```
GET /planning

POST /planning

PUT /planning/{id}

DELETE /planning/{id}
```

---

Approvals

```
POST /technical-approval

POST /administrative-approval
```

---

Dashboard

```
GET /dashboard

GET /dashboard/technician

GET /dashboard/supervisor

GET /dashboard/admin
```

---

Reports

```
GET /reports

GET /reports/monthly

GET /reports/yearly
```

---

Notifications

```
GET /notifications

PATCH /notifications/{id}/read
```

---

Attachments

```
POST /attachments

GET /attachments/{id}
```

---

# Chapter 84 — Transactions

Critical operations should use database transactions.

Examples

- Create Intervention
- Submit Intervention
- Technical Approval
- Administrative Approval

If one step fails, the entire operation is rolled back.

This prevents inconsistent data.

---

# Chapter 85 — Logging

Log important events.

Examples

- Login
- Failed Login
- Submission
- Approval
- Rejection
- Planning
- User Creation

Logs should contain

- Timestamp
- User
- Action
- Result

---

# Chapter 86 — Configuration

Environment variables

```
DATABASE_URL

SECRET_KEY

JWT_EXPIRE_MINUTES

UPLOAD_FOLDER

MAX_UPLOAD_SIZE

APP_NAME

DEBUG
```

No sensitive information should be hardcoded.

---

# Chapter 87 — Backend Business Principles

The backend is the single source of truth.

Therefore:

- All calculations happen in the backend.
- All permissions are checked in the backend.
- All validations are performed in the backend.
- React should only display data and send user requests.
- The frontend must never calculate points, durations, approval status, or permissions independently.

This ensures consistent behavior regardless of the client consuming the API.
# PART 8 — FRONTEND ARCHITECTURE (REACT)

---

# Chapter 88 — Frontend Overview

The frontend is a responsive web application developed using React and TypeScript.

Its responsibilities are:

- Display information.
- Collect user input.
- Communicate with the backend API.
- Validate basic form inputs.
- Display notifications.
- Manage navigation.

The frontend **must never contain business logic**.

Calculations such as:

- Points
- Duration
- Permissions
- Approval workflow

must always come from the backend.

---

# Chapter 89 — Technology Stack

Framework

- React

Language

- TypeScript

Build Tool

- Vite

UI Library

- Material UI (MUI)

Routing

- React Router

HTTP Client

- Axios

Server State

- TanStack Query

Forms

- React Hook Form

Date Management

- Day.js

Calendar

- FullCalendar

Icons

- Material Icons

---

# Chapter 90 — Frontend Folder Structure

```

frontend/

├── src/
│
├── assets/
│
├── components/
│
├── pages/
│
├── layouts/
│
├── hooks/
│
├── services/
│
├── api/
│
├── context/
│
├── routes/
│
├── utils/
│
├── types/
│
├── styles/
│
└── App.tsx

```

---

# Chapter 91 — Pages

## Public Pages

- Login

---

## Technician

- Dashboard
- My Calendar
- My Interventions
- Intervention Details
- Complete Intervention
- Notifications
- Profile

---

## Chef des Techniciens

- Dashboard
- Planning
- Calendar
- Technical Approvals
- Assign Intervention
- Urgent Interventions
- Notifications

---

## Administration Supervisor

- Dashboard
- Administrative Approvals
- Reports
- User Management
- Client Management
- Site Management
- Contract Management
- Project Management
- Travaux Catalog
- Notifications

---

# Chapter 92 — Layout

Every authenticated page shares the same layout.

```

+----------------------------------------+

| Header |

+----------+-----------------------------+

| Sidebar | Main Content |

| | |

| | |

| | |

+----------+-----------------------------+

```

---

## Header

Contains

- Application name
- User name
- User role
- Notifications
- Profile menu
- Logout

---

## Sidebar

Displays only modules available for the connected user.

Example

Technician

Dashboard

↓

Calendar

↓

Interventions

↓

Notifications

↓

Profile

---

Chef des Techniciens

Dashboard

↓

Planning

↓

Approvals

↓

Calendar

↓

Notifications

---

Administration Supervisor

Dashboard

↓

Approvals

↓

Users

↓

Clients

↓

Contracts

↓

Projects

↓

Travaux

↓

Reports

↓

Notifications

---

# Chapter 93 — Components

Reusable components

- DataTable
- SearchBar
- FilterPanel
- Calendar
- KPI Card
- Status Badge
- Priority Badge
- Notification Card
- Upload Component
- Date Picker
- Time Picker
- Modal
- Confirmation Dialog
- Pagination
- Loading Spinner

All pages should reuse these components.

---

# Chapter 94 — Navigation

Navigation should never require more than three clicks for common operations.

Example

Dashboard

↓

My Interventions

↓

Complete Intervention

Maximum

3 clicks

---

# Chapter 95 — Intervention Form Logic

The form is dynamic.

Fields appear according to the selected intervention type.

---

Standard

Only standard fields.

---

Contract

Contract dropdown appears.

---

Project

Project dropdown appears.

---

Warranty

Warranty Reference field appears.

---

The frontend should dynamically display these fields without reloading the page.

---

# Chapter 96 — Validation

Before submission

Required

- Client
- Site
- Start Time
- End Time
- Intervention Type
- Travaux
- Attachment

If missing

Display validation message.

Submission is blocked.

---

# Chapter 97 — Status Colors

Draft

Gray

---

Planned

Blue

---

In Progress

Light Blue

---

Submitted

Orange

---

Pending Technical Approval

Yellow

---

Pending Administrative Approval

Purple

---

Rejected

Red

---

Fully Approved

Green

---

Urgent

Dark Red

These colors should be consistent throughout the application.

---

# Chapter 98 — Priority Colors

Normal

Blue

---

High

Orange

---

Urgent

Red

---

# Chapter 99 — Loading States

Every API request should display

- Loading Spinner
- Skeleton Loader

The interface should never freeze.

---

# Chapter 100 — Empty States

Examples

"No interventions found."

"No notifications."

"No planning available."

Avoid blank pages.

---

# Chapter 101 — Error Handling

Examples

"Connection lost."

"Server unavailable."

"Permission denied."

Provide clear messages.

---

# Chapter 102 — Search

Large lists should support instant search.

Examples

Search by

- BI Number
- Client
- Technician
- Project
- Contract
- Site

Search should not require pressing Enter.

---

# Chapter 103 — Pagination

Large tables should never load every record.

Example

20 rows per page

Next

Previous

Go to page

---

# Chapter 104 — Responsive Design

Desktop

Full sidebar

---

Tablet

Collapsed sidebar

---

Mobile Browser

Drawer menu

The application remains Web-only.

---

# Chapter 105 — Accessibility

Buttons should always contain text or tooltips.

Forms should support keyboard navigation.

Colors should not be the only way to communicate status.

Icons should always include labels.

---

# Chapter 106 — Frontend Principles

The frontend should remain:

- Simple
- Consistent
- Fast
- Responsive
- Modular
- Reusable
- Easy to maintain

Each page should reuse existing components instead of creating duplicate implementations.
# PART 9 — DASHBOARDS, KPIs & REPORTING

---

# Chapter 107 — Dashboard Philosophy

Dashboards should provide actionable operational information instead of only displaying raw numbers.

Each role sees information relevant to their responsibilities.

---

# Chapter 108 — Technician Dashboard

Display:

## KPI Cards

- Planned Today
- Completed Today
- Pending Approval
- Rejected
- Monthly Points
- Average Daily Duration

---

## Lists

- Today's Planning
- Recent Notifications
- Recently Completed Interventions

---

## Charts

Weekly completed interventions

Monthly points earned

---

# Chapter 109 — Chef des Techniciens Dashboard

KPIs

- Planned Today
- Completed Today
- Pending Technical Approvals
- Urgent Interventions
- Active Technicians
- Average Completion Time

Charts

- Interventions by Technician
- Interventions by Client
- Daily Activity
- Weekly Activity

Operational Panels

- Today's Planning
- Technician Workload
- Urgent Queue

---

# Chapter 110 — Administration Dashboard

KPIs

- Pending Administrative Approvals
- Approved This Month
- Rejected This Month
- Average Approval Time

Charts

- Monthly Interventions
- Approval Rate
- Rejection Rate
- Points Distribution
- Client Activity
- City Activity

---

# Chapter 111 — KPI Definitions

Examples

Average Duration

=

Total Duration

/

Completed Interventions

---

Approval Rate

=

Approved

/

Submitted

×

100

---

Rejection Rate

=

Rejected

/

Submitted

×

100

---

Completion Rate

=

Completed

/

Planned

×

100

---

Technician Productivity

=

Completed Interventions

per Month

---

# Chapter 112 — Reports

Generate

- Daily Report
- Weekly Report
- Monthly Report
- Yearly Report
- Technician Report
- Client Report
- Contract Report
- Project Report
- Planning Report
- Approval Report

---

# Chapter 113 — Export Formats

Reports may be exported as

- PDF
- Excel

Generated directly from current filters.

---

# Chapter 114 — Historical Analysis

Users should be able to compare activity across periods.

Examples

Current Month vs Previous Month

Current Year vs Previous Year

Technician A vs Technician B

Client A vs Client B

---

# Chapter 115 — Dashboard Performance

Dashboards should aggregate data efficiently.

Avoid loading thousands of intervention records into the browser.

Whenever possible, the backend should return summarized statistics rather than raw data.
# PART 10 — PROJECT ARCHITECTURE, DEVELOPMENT STANDARDS & GIT WORKFLOW

---

# Chapter 116 — Overall System Architecture

The application follows a classic three-tier architecture.

```
                User
                  │
                  ▼
      React Frontend (Web)
                  │
            HTTPS / REST API
                  │
                  ▼
          FastAPI Backend
                  │
        SQLAlchemy ORM Layer
                  │
                  ▼
        PostgreSQL Database
```

Every request follows this path.

The frontend never communicates directly with the database.

---

# Chapter 117 — High-Level Application Flow

```
User Login
      │
      ▼
JWT Authentication
      │
      ▼
Dashboard
      │
      ▼
Planning
      │
      ▼
Assigned Intervention
      │
      ▼
Technician Completes Form
      │
      ▼
Attach Paper BI Image
      │
      ▼
Submit
      │
      ▼
Technical Approval
      │
      ▼
Administrative Approval
      │
      ▼
Reports
      │
      ▼
Dashboard Statistics
```

---

# Chapter 118 — Development Standards

General principles

- Modular architecture
- Separation of concerns
- Reusable components
- Consistent naming
- Small, focused functions
- Clear documentation
- No duplicated code
- Strong typing where possible

---

# Chapter 119 — Naming Conventions

## Backend

Python

```
snake_case
```

Examples

```
calculate_points()

create_intervention()

approval_service.py
```

---

## Frontend

React

```
PascalCase
```

Components

```
Dashboard.tsx

InterventionForm.tsx

NotificationCard.tsx
```

Variables

```
camelCase
```

Example

```
selectedClient

plannedInterventions

currentUser
```

---

## Database

Tables

```
snake_case
```

Example

```
client_sites

approval_history

intervention_tasks
```

Columns

```
snake_case
```

Example

```
start_time

approval_date

created_at
```

---

# Chapter 120 — Git Strategy

Main branch

```
main
```

Protected

Never commit directly.

---

Development branch

```
develop
```

Used for integration.

---

Feature branches

Examples

```
feature/authentication

feature/database

feature/intervention-form

feature/dashboard

feature/planning
```

Every member develops only in their own branch.

---

# Chapter 121 — Pull Request Workflow

Workflow

```
Create Feature Branch

↓

Develop

↓

Commit

↓

Push

↓

Pull Request

↓

Code Review

↓

Merge into develop

↓

Testing

↓

Merge into main
```

No direct merge into `main`.

---

# Chapter 122 — Commit Convention

Examples

```
feat: add login API

feat: intervention planning

fix: duration calculation

fix: approval workflow

docs: update README

style: improve dashboard layout

refactor: notification service
```

---

# Chapter 123 — Code Review Rules

Before merging

Verify

- No duplicated code
- Naming conventions respected
- No hardcoded values
- No unused files
- No debugging statements
- No commented-out production code
- API documented
- Tests pass

---

# Chapter 124 — Environment Configuration

Backend

```
.env
```

Contains

```
DATABASE_URL

SECRET_KEY

JWT_SECRET

UPLOAD_FOLDER

DEBUG

MAX_UPLOAD_SIZE
```

Never commit `.env`.

---

Frontend

```
VITE_API_URL
```

Example

```
http://localhost:8000/api
```

---

# Chapter 125 — API Documentation

The backend automatically generates Swagger documentation.

```
/docs
```

Contains

- Endpoints
- Parameters
- Authentication
- Responses
- Error codes

---

# Chapter 126 — File Storage

Uploaded files are stored outside the database.

Example

```
uploads/

2026/

07/

BI000145/

image1.jpg

image2.jpg
```

Database stores only

- File path
- File name
- Upload date
- Linked intervention

---

# Chapter 127 — Security

Passwords

- Hashed
- Never stored in plain text

JWT

- Expiration time
- Validation on every request

Uploads

- File type validation
- Size validation

Database

- Prepared statements via SQLAlchemy
- No raw SQL unless necessary

---

# Chapter 128 — Error Logging

Application logs

- Login failures
- Server errors
- Database errors
- Upload failures
- Approval failures

Unexpected exceptions should be logged without exposing internal details to the user.

---

# Chapter 129 — Performance Guidelines

The application should

- Use pagination
- Lazy-load large datasets
- Use indexes on frequently searched columns
- Avoid unnecessary API calls
- Cache static reference data (clients, sites, travaux)

---

# Chapter 130 — Backup Strategy

Although the project uses synthetic data initially, the production version should support:

- Daily database backups
- File attachment backups
- Backup restoration procedures

This is outside the scope of Version 1 but must be considered in the architecture.
# PART 11 — TESTING, DEVELOPMENT ROADMAP & TEAM ORGANIZATION

---

# Chapter 131 — Testing Strategy

Testing should occur continuously throughout development.

Three levels of testing

- Unit Testing
- Integration Testing
- User Acceptance Testing

---

# Chapter 132 — Unit Testing

Each module should be tested independently.

Examples

Authentication

- Login
- Invalid password
- Expired token

Business Logic

- Duration calculation
- Lunch break calculation
- Point calculation
- Warranty reference validation

Planning

- Assignment
- Priority handling

---

# Chapter 133 — Integration Testing

Verify interactions between modules.

Examples

React

↓

API

↓

Database

Examples

Create intervention

↓

Save

↓

Submit

↓

Approve

↓

Dashboard updated

---

# Chapter 134 — User Acceptance Testing

Typical scenarios

Scenario 1

Technician completes planned intervention.

Scenario 2

Technician submits intervention.

Scenario 3

Chef approves.

Scenario 4

Administration approves.

Scenario 5

Dashboard updates correctly.

Scenario 6

Rejected intervention corrected and resubmitted.

---

# Chapter 135 — Synthetic Test Data

Generate realistic records.

Users

15+

Clients

20+

Sites

50+

Projects

10+

Contracts

20+

Travaux

100+

Interventions

500+

Planning

200+

Notifications

200+

---

# Chapter 136 — Seven-Day Development Plan

## Day 1

- Validate requirements
- Validate database model
- Validate API design
- Create Git repository
- Assign tasks

---

## Day 2

Backend

- Authentication
- Database schema

Frontend

- Login page
- Dashboard layout

---

## Day 3

Intervention form

Planning module

Synthetic database

---

## Day 4

Approval workflow

Notifications

Business logic

---

## Day 5

Dashboards

KPIs

Reports

---

## Day 6

Testing

Bug fixing

Integration

---

## Day 7

Prepare demonstration

Populate synthetic database

Final testing

Presentation to supervisor

---

# Chapter 137 — Team Organization (5 Members)

## Member 1 — Backend & Authentication

Responsibilities

- FastAPI setup
- JWT
- REST API
- File uploads
- API documentation
- Backend utilities

---

## Member 2 — Database

Responsibilities

- PostgreSQL
- ERD
- SQLAlchemy models
- Alembic
- Synthetic data
- Relationships

---

## Member 3 — Frontend

Responsibilities

- React
- Layout
- Intervention form
- Calendar
- API integration
- Responsive design

---

## Member 4 — Business Logic

Responsibilities

- Approval workflow
- Point calculation
- Duration calculation
- Lunch break
- Warranty logic
- Permissions
- Notifications
- Scheduling rules

---

## Member 5 — Dashboards & Planning

Responsibilities

- Planning calendar
- KPIs
- Charts
- Reports
- Dashboard pages
- Statistics
- Export (PDF/Excel)

---

# Chapter 138 — Milestones

Milestone 1

Authentication complete

---

Milestone 2

Database operational

---

Milestone 3

Intervention workflow complete

---

Milestone 4

Approval workflow complete

---

Milestone 5

Planning operational

---

Milestone 6

Dashboards complete

---

Milestone 7

Final integrated prototype

---

# Chapter 139 — Definition of Done

A feature is considered complete only if:

- Functionality works correctly.
- UI is complete.
- API is connected.
- Data is stored correctly.
- Validation is implemented.
- Error handling exists.
- Code reviewed.
- Tested.
- Merged into the `develop` branch.
# PART 12 — FUTURE IMPROVEMENTS (OUT OF SCOPE FOR VERSION 1)

The following features are intentionally excluded from Version 1 but should be considered in future releases.

## Mobile Application

Native Android/iOS application for technicians.

---

## OCR

Automatic extraction of data from the photographed paper BI.

---

## Artificial Intelligence

- Automatic anomaly detection.
- Workload prediction.
- Intervention duration prediction.
- Smart technician assignment.
- Predictive maintenance.

---

## Push Notifications

Real-time notifications via mobile devices.

---

## Email Integration

Automatic emails when interventions are assigned or approved.

---

## Client Portal

Clients can:

- View intervention history.
- Download reports.
- Track intervention status.

---

## GPS Integration

Record intervention location.

Track technician arrival and departure times.

---

## Digital Signature

Replace handwritten signatures with electronic signatures.

---

## Inventory Management

Manage:

- Spare parts.
- Equipment.
- Consumables.
- Warehouse stock.

---

## Multi-Company Support

Support multiple organizations within the same platform while isolating their data.

---

## Cloud Deployment

Deploy on cloud infrastructure with scalable storage, backups, monitoring, and automatic updates.

---

## Final Project Vision

The Bon d'Intervention Management System should evolve into a complete maintenance management platform that centralizes:

- Intervention planning.
- Technician management.
- Digital intervention forms.
- Approval workflows.
- Document management.
- Notifications.
- Performance dashboards.
- KPI monitoring.
- Reporting.
- Historical traceability.

Version 1 focuses on establishing a robust, maintainable web application with a production-ready architecture and a synthetic database, providing a solid foundation for future enhancements without requiring major redesign.
# PART 13 — FUNCTIONAL SPECIFICATION OF EVERY MODULE

---

# Chapter 140 — Authentication Module

## Purpose

Authenticate users and determine their role.

---

## Login Page

### Fields

- Username
- Password

### Buttons

- Login

### Business Rules

- Username must exist.
- Password must match.
- Passwords are hashed.
- Invalid credentials display an error.
- After login:
  - JWT token is created.
  - Session begins.
  - User role is loaded.
  - User is redirected to the correct dashboard.

---

# Logout

Destroys session.

Deletes JWT.

Redirects to Login.

---

# Chapter 141 — Dashboard Module

Purpose:

Provide a quick overview of work.

Each dashboard changes according to the user's role.

---

## Technician Dashboard

Cards

- Planned Today
- Completed Today
- Pending Approval
- Rejected
- Monthly Points

Tables

Today's Planning

Recent Interventions

Notifications

Buttons

- New Intervention
- Open Calendar
- View History

---

## Chef Dashboard

Cards

- Pending Technical Approvals
- Planned Today
- Urgent Interventions
- Active Technicians

Tables

Planning

Pending Approvals

Urgent Queue

Buttons

- Create Planning
- Assign Technician
- Approve
- Reject

---

## Administration Dashboard

Cards

- Pending Administrative Approvals
- Approval Rate
- Monthly Activity
- Reports Generated

Tables

Administrative Queue

Recent Reports

Buttons

- Approve
- Reject
- Export PDF
- Export Excel

---

# Chapter 142 — Planning Module

Purpose

Plan interventions before technicians execute them.

Only Chef des Techniciens may access it.

---

## Create Planning

Fields

Client

↓

Site

↓

Technician

↓

Date

↓

Estimated Start Time

↓

Estimated Duration

↓

Priority

↓

Notes

Button

Assign

---

Business Rules

Assigned technician immediately receives notification.

Planning appears in technician calendar.

Status becomes

Planned.

---

# Edit Planning

Allowed before technician starts work.

Editable

- Technician
- Date
- Time
- Priority
- Notes

---

# Cancel Planning

Planning is cancelled.

History remains stored.

Technician receives notification.

---

# Chapter 143 — Calendar Module

Purpose

Display interventions chronologically.

Views

Daily

Weekly

Monthly

---

Each event displays

- Client
- Site
- Time
- Status
- Priority

Clicking opens details.

---

Color Rules

Blue

Planned

Green

Completed

Red

Urgent

Gray

Draft

Orange

Pending Approval

Purple

Administrative Approval

---

# Chapter 144 — Intervention Module

This is the application's central module.

---

## General Section

Fields

BI Number

(Read Only)

Technician

(Read Only)

Date

Submission Date

(Read Only)

---

## Client Section

Client

Dropdown

↓

Site

Dropdown

Filtered by client.

---

## Intervention Type

Dropdown

Values

Standard

Contract

Project

Warranty

Dynamic fields appear automatically.

---

## Location

Dropdown

Sur Site

Atelier

---

## Time

Start Time

↓

End Time

↓

Lunch Break

↓

Duration

Calculated automatically.

---

## Technical Tasks

Travaux

Dropdown

Multiple Selection

Loaded from database.

---

## Technical Report

Large text area.

Technician describes work.

---

## Attachments

Buttons

Take Photo

Upload Image

Preview Image

Delete Image

At least one attachment required.

---

Buttons

Save Draft

Submit

Cancel

---

# Chapter 145 — Approval Module

Two approval stages.

---

## Technical Approval

Visible only to Chef des Techniciens.

Actions

Approve

Reject

View Attachment

View Intervention

Comment

After approval

Status

Pending Administrative Approval

---

## Administrative Approval

Visible only to Administration Supervisor.

Actions

Approve

Reject

Comment

View Attachment

After approval

Status

Fully Approved

Locked permanently.

---

# Chapter 146 — Notification Module

Notifications generated automatically.

Examples

New Planning

Urgent Planning

Technical Approval

Administrative Approval

Rejected Intervention

Planning Modified

Planning Cancelled

---

Each notification contains

Title

Description

Time

Related BI

Read Status

---

# Chapter 147 — Search Module

Global search.

Searches

BI Number

↓

Client

↓

Site

↓

Technician

↓

Project

↓

Contract

↓

Status

Results update instantly.

---

# Chapter 148 — Filtering

Every large table supports filtering.

Filters

Date Range

Status

Priority

Technician

Client

Site

Project

Contract

Intervention Type

Filters may be combined.

---

# Chapter 149 — Reports Module

Generate reports from filters.

Output

PDF

Excel

Reports

Daily

Weekly

Monthly

Yearly

Technician

Client

Planning

Projects

Contracts

Approvals

---

# Chapter 150 — Settings Module

Visible only to Administration Supervisor.

Manage

Users

Clients

Sites

Projects

Contracts

Travaux

Application Configuration

Point Rules

Status Definitions

Priority Definitions

Future Configuration Options

---

# Chapter 151 — Audit Module

Every action generates history.

Examples

Created

↓

Modified

↓

Submitted

↓

Rejected

↓

Approved

↓

Administrative Approval

History contains

User

Date

Time

Action

Comment

History cannot be deleted.

---

# Chapter 152 — File Management Module

Stores intervention attachments.

Functions

Upload

Preview

Download

Replace (before approval)

Supported Formats

JPG

JPEG

PNG

PDF

OCR not implemented.

---

# Chapter 153 — Error Messages

Examples

Client required.

Site required.

Attachment required.

Invalid time.

Unauthorized access.

Planning conflict.

Duplicate BI.

Server unavailable.

Validation failed.

Messages should be clear and user-friendly.

---

# Chapter 154 — Success Messages

Examples

Planning created.

Intervention saved.

Draft updated.

Intervention submitted.

Technical approval completed.

Administrative approval completed.

Report exported.

Notification sent.