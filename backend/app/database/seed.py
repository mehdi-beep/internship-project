"""Synthetic data generator for BIMS (Ch.51, Ch.135 of project_specifications.md).

Produces realistic demo data simulating a company that has been using the
application for several months: users, clients, sites, contracts, projects,
travaux, interventions (across every lifecycle status), planning, notifications
and approval history — all with real, referentially-consistent relationships
(Ch.51 "Relationships must be realistic").

Run with:  python -m app.database.seed
Re-running against a non-empty database is a no-op (idempotent guard on `roles`).
"""

import random
from datetime import date, datetime, time, timedelta

from faker import Faker
from sqlalchemy.orm import Session

from app.authentication.password import hash_password
from app.database import SessionLocal
from app.models import (
    ApprovalHistory,
    Attachment,
    AuditLog,
    Client,
    ClientSite,
    Contract,
    Intervention,
    InterventionTask,
    Notification,
    Planning,
    Project,
    Role,
    Travail,
    User,
)
from app.models.enums import (
    ApprovalDecision,
    ApprovalLevel,
    AuditAction,
    ContractStatus,
    InterventionStatus,
    InterventionType,
    LocationType,
    PlanningStatus,
    Priority,
    ProjectStatus,
)
from app.utils.bi_number import format_bi_number

fake = Faker()
Faker.seed(42)
random.seed(42)

MOROCCAN_CITIES = [
    "Agadir", "Casablanca", "Rabat", "Marrakech", "Fes", "Tangier", "Meknes",
    "Oujda", "Kenitra", "Tetouan", "Safi", "Mohammedia", "El Jadida", "Beni Mellal",
    "Nador", "Taza", "Settat", "Khemisset", "Larache", "Guelmim",
]

TRAVAUX_CATALOG = [
    ("Firewall Installation", "Network"),
    ("Fiber Repair", "Network"),
    ("Server Maintenance", "Infrastructure"),
    ("Camera Configuration", "Security"),
    ("Router Replacement", "Network"),
    ("Switch Configuration", "Network"),
    ("UPS Battery Replacement", "Infrastructure"),
    ("Access Point Installation", "Network"),
    ("VPN Setup", "Network"),
    ("Antivirus Deployment", "Security"),
    ("Backup Configuration", "Infrastructure"),
    ("Printer Installation", "Hardware"),
    ("Workstation Setup", "Hardware"),
    ("Cabling — Cat6", "Network"),
    ("PABX Maintenance", "Telephony"),
    ("Alarm System Check", "Security"),
    ("CCTV Recorder Replacement", "Security"),
    ("Load Balancer Configuration", "Network"),
    ("Data Migration", "Infrastructure"),
    ("Software Update Rollout", "Infrastructure"),
    ("Network Diagnostics", "Network"),
    ("Cable Termination", "Network"),
    ("Rack Installation", "Infrastructure"),
    ("Wireless Site Survey", "Network"),
    ("Badge Reader Installation", "Security"),
]

# Statuses assigned to bulk-generated interventions, weighted toward the end
# of the pipeline (Fully Approved) since the company has "been using the
# application for several months" (Ch.51) — most historical work is finished.
INTERVENTION_STATUS_WEIGHTS: list[tuple[InterventionStatus, int]] = [
    (InterventionStatus.DRAFT, 5),
    (InterventionStatus.SUBMITTED, 5),
    (InterventionStatus.PENDING_TECHNICAL_APPROVAL, 5),
    (InterventionStatus.TECHNICAL_APPROVED, 3),
    (InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL, 5),
    (InterventionStatus.REJECTED, 7),
    (InterventionStatus.FULLY_APPROVED, 70),
]

LUNCH_BREAK_OPTIONS = [0, 30, 60, 90, 120]


def _weighted_status() -> InterventionStatus:
    statuses, weights = zip(*INTERVENTION_STATUS_WEIGHTS)
    return random.choices(statuses, weights=weights, k=1)[0]


def _points_for_submission(submission_dt: datetime) -> int:
    """Ch.28 point system — mirrors `business_logic_service.calculate_points()`
    (Phase 7) so seeded historical data is internally consistent with the real
    rules. Seed timestamps are already generated as Morocco wall-clock times
    (this script never converts timezones), so no conversion is needed here —
    unlike the real service, which converts from UTC before checking the hour."""
    hour = submission_dt.hour
    if 17 <= hour < 19:
        return 5
    if 19 <= hour < 22:
        return 2
    if 22 <= hour < 24:
        return 1
    if hour < 6:
        return -2
    return 0


def seed_roles(db: Session) -> dict[str, Role]:
    from app.models.role import RoleName

    roles = {}
    for role_name in RoleName:
        role = Role(name=role_name)
        db.add(role)
        roles[role_name.value] = role
    db.flush()
    return roles


def seed_users(db: Session, roles: dict[str, Role]) -> dict[str, list[User]]:
    """Ch.51: 10 Technicians, 2 Chef des Techniciens, 2 Administration Supervisors."""

    def make_user(first: str, last: str, username: str, role: Role) -> User:
        user = User(
            first_name=first,
            last_name=last,
            username=username,
            password_hash=hash_password("Password123!"),
            email=f"{username}@bims.local",
            phone=fake.phone_number()[:30],
            role=role,
            active=True,
        )
        db.add(user)
        return user

    technicians = []
    for i in range(1, 11):
        first, last = fake.first_name(), fake.last_name()
        technicians.append(make_user(first, last, f"tech{i:02d}", roles["technician"]))

    chefs = []
    for i in range(1, 3):
        first, last = fake.first_name(), fake.last_name()
        chefs.append(make_user(first, last, f"chef{i:02d}", roles["chef_technicien"]))

    admins = []
    for i in range(1, 3):
        first, last = fake.first_name(), fake.last_name()
        admins.append(make_user(first, last, f"admin{i:02d}", roles["admin_supervisor"]))

    db.flush()
    return {"technicians": technicians, "chefs": chefs, "admins": admins}


def seed_clients_and_sites(db: Session) -> tuple[list[Client], list[ClientSite]]:
    """Ch.51: 20+ clients, 50+ sites. Every site belongs to exactly one client (Rule 1/2)."""
    company_suffixes = ["Maroc", "Group", "Solutions", "Telecom", "Bank", "Industries", "Holding", "Services"]
    clients = []
    for _ in range(22):
        name = f"{fake.company()} {random.choice(company_suffixes)}"
        client = Client(client_name=name, phone=fake.phone_number()[:30], email=fake.company_email(), active=True)
        db.add(client)
        clients.append(client)
    db.flush()

    sites = []
    for client in clients:
        for _ in range(random.randint(2, 4)):
            city = random.choice(MOROCCAN_CITIES)
            site = ClientSite(
                client=client,
                site_name=f"{client.client_name.split()[0]} {city} Site",
                city=city,
                address=fake.address().replace("\n", ", "),
                active=True,
            )
            db.add(site)
            sites.append(site)
    db.flush()
    return clients, sites


def seed_contracts_and_projects(db: Session, clients: list[Client]) -> tuple[list[Contract], list[Project]]:
    """Ch.51: 25+ contracts, 15+ projects, each tied to exactly one client."""
    contracts = []
    for _ in range(28):
        client = random.choice(clients)
        start = fake.date_between(start_date="-2y", end_date="-6M")
        contract = Contract(
            client=client,
            contract_name=f"Maintenance Contract {start.year} — {client.client_name.split()[0]}",
            start_date=start,
            end_date=start + timedelta(days=365),
            status=random.choices([ContractStatus.ACTIVE, ContractStatus.ARCHIVED], weights=[80, 20])[0],
        )
        db.add(contract)
        contracts.append(contract)

    projects = []
    project_names = [
        "Fiber Expansion Project", "Datacenter Migration", "Network Modernization",
        "Security Upgrade Program", "Wireless Rollout", "Cabling Overhaul",
        "Surveillance Deployment", "Cloud Backup Rollout", "PABX Replacement Program",
        "Access Control Rollout", "Branch Connectivity Project", "Disaster Recovery Setup",
        "VoIP Migration", "Perimeter Security Project", "Smart Building Rollout",
        "Retail Network Rollout", "ATM Network Upgrade", "Core Switching Refresh",
    ]
    for name in project_names:
        client = random.choice(clients)
        start = fake.date_between(start_date="-18M", end_date="-3M")
        project = Project(
            client=client,
            project_name=f"{name} — {client.client_name.split()[0]}",
            start_date=start,
            end_date=start + timedelta(days=random.randint(180, 540)),
            status=random.choices([ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED], weights=[70, 30])[0],
        )
        db.add(project)
        projects.append(project)

    db.flush()
    return contracts, projects


def seed_travaux(db: Session) -> list[Travail]:
    """Ch.51: 100+ catalog entries. The 25 named ones above are repeated with
    distinct codes/categorized variants to realistically pad the catalog, since
    a real technical-operations catalog has many near-duplicate line items
    (different equipment models, capacities, etc.) rather than 100 unique concepts."""
    travaux = []
    code = 100
    variants = ["", " — Type A", " — Type B", " — Standard", " — Advanced"]
    for name, category in TRAVAUX_CATALOG:
        for variant in variants:
            code += 1
            travaux.append(
                Travail(
                    travail_code=str(code),
                    travail_name=f"{name}{variant}",
                    category=category,
                    active=True,
                )
            )
    db.add_all(travaux)
    db.flush()
    return travaux


def seed_interventions(
    db: Session,
    technicians: list[User],
    clients: list[Client],
    sites_by_client: dict[int, list[ClientSite]],
    contracts_by_client: dict[int, list[Contract]],
    projects_by_client: dict[int, list[Project]],
    travaux: list[Travail],
    chefs: list[User],
    admins: list[User],
) -> list[Intervention]:
    """Ch.51: 500-1000 interventions spanning several months, all statuses,
    with warranty interventions referencing real prior BI numbers (Ch.5)."""

    interventions: list[Intervention] = []
    bi_seq = 1
    today = date.today()

    target_count = 650

    for _ in range(target_count):
        client = random.choice(clients)
        client_sites = sites_by_client.get(client.id) or []
        if not client_sites:
            continue
        site = random.choice(client_sites)
        technician = random.choice(technicians)

        intervention_type = random.choices(
            [InterventionType.STANDARD, InterventionType.CONTRACT, InterventionType.PROJECT, InterventionType.WARRANTY],
            weights=[55, 20, 15, 10],
        )[0]

        contract_id = None
        project_id = None
        warranty_reference_id = None

        if intervention_type == InterventionType.CONTRACT:
            client_contracts = contracts_by_client.get(client.id) or []
            if client_contracts:
                contract_id = random.choice(client_contracts).id
            else:
                intervention_type = InterventionType.STANDARD
        elif intervention_type == InterventionType.PROJECT:
            client_projects = projects_by_client.get(client.id) or []
            if client_projects:
                project_id = random.choice(client_projects).id
            else:
                intervention_type = InterventionType.STANDARD
        elif intervention_type == InterventionType.WARRANTY:
            if interventions:
                warranty_reference_id = random.choice(interventions).id
            else:
                intervention_type = InterventionType.STANDARD

        intervention_date = fake.date_between(start_date="-8M", end_date="today")
        start_hour = random.randint(7, 16)
        start_minute = random.choice([0, 15, 30, 45])
        start_time = time(start_hour, start_minute)
        duration_hours = random.randint(1, 8)
        end_hour = min(start_hour + duration_hours, 23)
        end_time = time(end_hour, random.choice([0, 15, 30, 45]))

        lunch_break = random.choice(LUNCH_BREAK_OPTIONS) if start_hour < 13 < end_hour else 0

        gross_minutes = (end_hour * 60 + end_time.minute) - (start_hour * 60 + start_time.minute)
        net_duration = max(gross_minutes - lunch_break, 15)

        status = _weighted_status()
        location_type = random.choice([LocationType.SUR_SITE, LocationType.ATELIER])

        bi_number = format_bi_number(bi_seq)
        bi_seq += 1

        intervention = Intervention(
            bi_number=bi_number,
            technician_id=technician.id,
            client_id=client.id,
            site_id=site.id,
            contract_id=contract_id,
            project_id=project_id,
            warranty_reference_id=warranty_reference_id,
            intervention_type=intervention_type,
            location_type=location_type,
            intervention_date=intervention_date,
            start_time=start_time,
            end_time=end_time,
            lunch_break_minutes=lunch_break,
            net_duration_minutes=net_duration,
            number_of_technicians=random.choice([1, 1, 1, 2, 2, 3]),
            technical_report=fake.paragraph(nb_sentences=4),
            contact_person=fake.name() if random.random() > 0.3 else None,
            status=InterventionStatus.DRAFT,  # set for real below via status machine
            points_earned=0,
        )
        db.add(intervention)
        db.flush()

        # --- tasks (Ch.43) ---
        for travail in random.sample(travaux, k=random.randint(1, 3)):
            db.add(InterventionTask(intervention_id=intervention.id, travail_id=travail.id))

        # --- attachments (Rule 7 — required once past draft) ---
        submission_dt = None
        if status != InterventionStatus.DRAFT:
            submission_dt = datetime.combine(intervention_date, start_time) + timedelta(
                hours=random.randint(0, 30), minutes=random.randint(0, 59)
            )
            db.add(
                Attachment(
                    intervention_id=intervention.id,
                    file_name=f"{bi_number}_signed.jpg",
                    file_path=f"{intervention_date.year}/{intervention_date.month:02d}/{bi_number}/signed.jpg",
                    content_type="image/jpeg",
                    uploaded_by=technician.id,
                )
            )

        db.add(AuditLog(intervention_id=intervention.id, user_id=technician.id, action=AuditAction.CREATED))

        chef = random.choice(chefs)
        admin = random.choice(admins)

        if status == InterventionStatus.DRAFT:
            db.add(AuditLog(intervention_id=intervention.id, user_id=technician.id, action=AuditAction.DRAFT_SAVED))

        elif status in (
            InterventionStatus.SUBMITTED,
            InterventionStatus.PENDING_TECHNICAL_APPROVAL,
            InterventionStatus.TECHNICAL_APPROVED,
            InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL,
            InterventionStatus.FULLY_APPROVED,
            InterventionStatus.REJECTED,
        ):
            intervention.submission_date = submission_dt
            intervention.points_earned = _points_for_submission(submission_dt)
            db.add(AuditLog(intervention_id=intervention.id, user_id=technician.id, action=AuditAction.SUBMITTED))

            if status in (
                InterventionStatus.TECHNICAL_APPROVED,
                InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL,
                InterventionStatus.FULLY_APPROVED,
            ):
                tech_approval_dt = submission_dt + timedelta(hours=random.randint(1, 48))
                intervention.technical_approval_date = tech_approval_dt
                db.add(
                    ApprovalHistory(
                        intervention_id=intervention.id,
                        approval_level=ApprovalLevel.TECHNICAL,
                        approved_by=chef.id,
                        decision=ApprovalDecision.APPROVED,
                        comment="Technical review OK." if random.random() > 0.7 else None,
                        approval_date=tech_approval_dt,
                    )
                )
                db.add(AuditLog(intervention_id=intervention.id, user_id=chef.id, action=AuditAction.TECHNICAL_APPROVED))

                if status == InterventionStatus.FULLY_APPROVED:
                    admin_approval_dt = tech_approval_dt + timedelta(hours=random.randint(1, 72))
                    intervention.administrative_approval_date = admin_approval_dt
                    db.add(
                        ApprovalHistory(
                            intervention_id=intervention.id,
                            approval_level=ApprovalLevel.ADMINISTRATIVE,
                            approved_by=admin.id,
                            decision=ApprovalDecision.APPROVED,
                            comment=None,
                            approval_date=admin_approval_dt,
                        )
                    )
                    db.add(
                        AuditLog(
                            intervention_id=intervention.id,
                            user_id=admin.id,
                            action=AuditAction.ADMINISTRATIVE_APPROVED,
                        )
                    )

            elif status == InterventionStatus.REJECTED:
                rejector, level = random.choice([(chef, ApprovalLevel.TECHNICAL), (admin, ApprovalLevel.ADMINISTRATIVE)])
                rejection_dt = submission_dt + timedelta(hours=random.randint(1, 48))
                db.add(
                    ApprovalHistory(
                        intervention_id=intervention.id,
                        approval_level=level,
                        approved_by=rejector.id,
                        decision=ApprovalDecision.REJECTED,
                        comment=random.choice(
                            [
                                "Missing details in technical report.",
                                "Dates do not match the attached document.",
                                "Incorrect intervention type selected.",
                                "Attachment illegible, please re-upload.",
                            ]
                        ),
                        approval_date=rejection_dt,
                    )
                )
                db.add(AuditLog(intervention_id=intervention.id, user_id=rejector.id, action=AuditAction.REJECTED))

        intervention.status = status
        interventions.append(intervention)

    db.flush()
    return interventions


def seed_planning(
    db: Session,
    technicians: list[User],
    clients: list[Client],
    sites_by_client: dict[int, list[ClientSite]],
    chefs: list[User],
) -> None:
    """Ch.51: 200+ planning records referencing existing technicians/clients/sites."""
    today = date.today()
    for _ in range(220):
        client = random.choice(clients)
        client_sites = sites_by_client.get(client.id) or []
        if not client_sites:
            continue
        site = random.choice(client_sites)
        technician = random.choice(technicians)
        planned_date = today + timedelta(days=random.randint(-10, 60))
        status = (
            PlanningStatus.COMPLETED
            if planned_date < today
            else random.choices(
                [PlanningStatus.PLANNED, PlanningStatus.CANCELLED], weights=[90, 10]
            )[0]
        )
        db.add(
            Planning(
                technician_id=technician.id,
                client_id=client.id,
                site_id=site.id,
                planned_date=planned_date,
                planned_start_time=time(random.randint(7, 16), random.choice([0, 15, 30, 45])),
                estimated_duration_minutes=random.choice([60, 90, 120, 180, 240, 480]),
                priority=random.choices(
                    [Priority.NORMAL, Priority.HIGH, Priority.URGENT], weights=[65, 25, 10]
                )[0],
                status=status,
                notes=fake.sentence() if random.random() > 0.5 else None,
                created_by=random.choice(chefs).id,
            )
        )
    db.flush()


def seed_notifications(
    db: Session,
    technicians: list[User],
    chefs: list[User],
    admins: list[User],
    interventions: list[Intervention],
) -> None:
    """Ch.51: 300+ notifications referencing real users/interventions."""
    templates = [
        ("New Intervention Assigned", "You have been assigned a new intervention: {bi}."),
        ("Urgent Intervention", "An urgent intervention requires your attention: {bi}."),
        ("Intervention Approved", "Intervention {bi} has been fully approved."),
        ("Intervention Rejected", "Intervention {bi} was rejected — please review and resubmit."),
        ("Technical Approval Needed", "Intervention {bi} is pending technical approval."),
        ("Administrative Approval Needed", "Intervention {bi} is pending administrative approval."),
        ("Planning Modified", "Your planning for {bi} has been updated."),
    ]
    all_users = technicians + chefs + admins
    for _ in range(320):
        title, message_template = random.choice(templates)
        intervention = random.choice(interventions)
        recipient = random.choice(all_users)
        db.add(
            Notification(
                user_id=recipient.id,
                title=title,
                message=message_template.format(bi=intervention.bi_number),
                related_intervention_id=intervention.id,
                read=random.random() > 0.4,
            )
        )
    db.flush()


def run() -> None:
    db = SessionLocal()
    try:
        if db.query(Role).count() > 0:
            print("Database already seeded (roles table is non-empty) — skipping.")
            return

        print("Seeding roles...")
        roles = seed_roles(db)

        print("Seeding users...")
        users = seed_users(db, roles)

        print("Seeding clients and sites...")
        clients, sites = seed_clients_and_sites(db)
        sites_by_client: dict[int, list[ClientSite]] = {}
        for site in sites:
            sites_by_client.setdefault(site.client_id, []).append(site)

        print("Seeding contracts and projects...")
        contracts, projects = seed_contracts_and_projects(db, clients)
        contracts_by_client: dict[int, list[Contract]] = {}
        for contract in contracts:
            contracts_by_client.setdefault(contract.client_id, []).append(contract)
        projects_by_client: dict[int, list[Project]] = {}
        for project in projects:
            projects_by_client.setdefault(project.client_id, []).append(project)

        print("Seeding travaux catalog...")
        travaux = seed_travaux(db)

        print("Seeding interventions (this may take a moment)...")
        interventions = seed_interventions(
            db,
            technicians=users["technicians"],
            clients=clients,
            sites_by_client=sites_by_client,
            contracts_by_client=contracts_by_client,
            projects_by_client=projects_by_client,
            travaux=travaux,
            chefs=users["chefs"],
            admins=users["admins"],
        )

        print("Seeding planning...")
        seed_planning(db, users["technicians"], clients, sites_by_client, users["chefs"])

        print("Seeding notifications...")
        seed_notifications(db, users["technicians"], users["chefs"], users["admins"], interventions)

        db.commit()
        print(
            f"Seed complete: {len(users['technicians'])} technicians, {len(users['chefs'])} chefs, "
            f"{len(users['admins'])} admins, {len(clients)} clients, {len(sites)} sites, "
            f"{len(contracts)} contracts, {len(projects)} projects, {len(travaux)} travaux, "
            f"{len(interventions)} interventions."
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
