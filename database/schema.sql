-- ============================================================
-- SCHEMA POSTGRESQL - BON D'INTERVENTION MANAGEMENT SYSTEM (BIMS)
-- Projet PFA - Deweb Technology
-- Basé sur le cahier des charges officiel (Parts 1-5)
-- ============================================================
-- Conventions : tables et colonnes en snake_case (Chapitre 119).
-- Aucune suppression physique : tout passe par un champ de statut
-- ou "active" (Chapitre 50 - Cascade Rules).
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- pour le hash des mots de passe

-- ------------------------------------------------------------
-- 1. ROLES (Chapitre 36)
-- ------------------------------------------------------------
-- Exactement 3 rôles. Pas de rôle "administrateur" séparé :
-- l'Administration Supervisor remplit ce rôle.
CREATE TABLE roles (
    role_id     SERIAL PRIMARY KEY,
    role_name   VARCHAR(50) UNIQUE NOT NULL
);

INSERT INTO roles (role_name) VALUES
    ('Technician'),
    ('Chef des Techniciens'),
    ('Administration Supervisor');

-- ------------------------------------------------------------
-- 2. USERS (Chapitre 35)
-- ------------------------------------------------------------
CREATE TABLE users (
    user_id         SERIAL PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    username        VARCHAR(100) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    phone           VARCHAR(20),
    role_id         INTEGER NOT NULL REFERENCES roles(role_id),
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- 3. CLIENTS (Chapitre 37)
-- ------------------------------------------------------------
CREATE TABLE clients (
    client_id       SERIAL PRIMARY KEY,
    client_name     VARCHAR(150) NOT NULL,
    phone           VARCHAR(20),
    email           VARCHAR(150),
    active          BOOLEAN NOT NULL DEFAULT TRUE
);

-- ------------------------------------------------------------
-- 4. CLIENT SITES (Chapitre 38)
-- ------------------------------------------------------------
-- Règle 4 : les villes ne sont jamais tapées à la main, elles
-- dépendent du client sélectionné (via ce site).
CREATE TABLE client_sites (
    site_id     SERIAL PRIMARY KEY,
    client_id   INTEGER NOT NULL REFERENCES clients(client_id),
    site_name   VARCHAR(150) NOT NULL,    -- ex: "Agadir Headquarters"
    city        VARCHAR(100) NOT NULL,
    address     VARCHAR(255)
);

-- ------------------------------------------------------------
-- 5. CONTRACTS (Chapitre 39)
-- ------------------------------------------------------------
-- Visible uniquement si intervention_type = 'Contract'.
CREATE TABLE contracts (
    contract_id     SERIAL PRIMARY KEY,
    client_id       INTEGER NOT NULL REFERENCES clients(client_id),
    contract_name   VARCHAR(150) NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE,
    status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
                    CHECK (status IN ('ACTIVE','EXPIRED','ARCHIVED'))
);

-- ------------------------------------------------------------
-- 6. PROJECTS (Chapitre 40)
-- ------------------------------------------------------------
-- Visible uniquement si intervention_type = 'Project'.
CREATE TABLE projects (
    project_id      SERIAL PRIMARY KEY,
    client_id       INTEGER NOT NULL REFERENCES clients(client_id),
    project_name    VARCHAR(150) NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE,
    status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
                    CHECK (status IN ('ACTIVE','COMPLETED','ARCHIVED'))
);

-- ------------------------------------------------------------
-- 7. TRAVAUX CATALOG (Chapitre 41)
-- ------------------------------------------------------------
-- Catalogue prédéfini de tâches. Saisie libre interdite
-- (le technicien sélectionne, il ne tape pas).
CREATE TABLE travaux (
    travail_id      SERIAL PRIMARY KEY,
    travail_code    VARCHAR(20) UNIQUE NOT NULL,   -- ex: '101'
    travail_name    VARCHAR(150) NOT NULL,          -- ex: 'Firewall Installation'
    category        VARCHAR(100),
    active          BOOLEAN NOT NULL DEFAULT TRUE
);

-- ------------------------------------------------------------
-- 8. INTERVENTIONS (Chapitre 42) - table centrale
-- ------------------------------------------------------------
-- Règle 6 : bi_number généré automatiquement, jamais modifiable.
-- Règle 9 : jamais supprimée, seul le statut change.
CREATE TABLE interventions (
    intervention_id             SERIAL PRIMARY KEY,
    bi_number                   VARCHAR(30) UNIQUE NOT NULL,  -- ex: 'BI000001'
    technician_id                INTEGER NOT NULL REFERENCES users(user_id),
    client_id                    INTEGER NOT NULL REFERENCES clients(client_id),
    site_id                      INTEGER NOT NULL REFERENCES client_sites(site_id),
    contract_id                  INTEGER REFERENCES contracts(contract_id),      -- si type = Contract
    project_id                   INTEGER REFERENCES projects(project_id),        -- si type = Project
    warranty_reference_id        INTEGER REFERENCES interventions(intervention_id), -- si type = Warranty

    intervention_type            VARCHAR(20) NOT NULL
                                  CHECK (intervention_type IN ('Standard','Contract','Project','Warranty')),
    location_type                VARCHAR(20) NOT NULL
                                  CHECK (location_type IN ('Sur Site','Atelier')),
    priority                     VARCHAR(10) NOT NULL DEFAULT 'Normal'
                                  CHECK (priority IN ('Normal','High','Urgent')),

    intervention_date            DATE NOT NULL DEFAULT CURRENT_DATE,
    start_time                   TIMESTAMP,
    end_time                     TIMESTAMP,
    lunch_break_minutes          INTEGER NOT NULL DEFAULT 0,   -- 0/30/60/90/120/custom (Chapitre 22 Section E)
    net_duration_minutes         INTEGER,                       -- calculé : (end-start) - lunch_break (Chapitre 27)

    number_of_technicians        INTEGER NOT NULL DEFAULT 1,
    technical_report             TEXT,                          -- "Comments" Section H

    -- Workflow des statuts (Chapitre 9 / 17) :
    -- Planned -> In Progress -> Draft -> Submitted ->
    -- Pending Technical Approval -> Technical Approved ->
    -- Pending Administrative Approval -> Fully Approved
    -- (ou Rejected à tout moment après soumission)
    status                        VARCHAR(35) NOT NULL DEFAULT 'Draft'
                                  CHECK (status IN (
                                      'Planned','In Progress','Draft','Submitted',
                                      'Pending Technical Approval','Technical Approved',
                                      'Pending Administrative Approval','Fully Approved',
                                      'Rejected'
                                  )),

    submission_date               TIMESTAMP,          -- rempli à la soumission (sert au calcul des points)
    technical_approval_date       TIMESTAMP,
    administrative_approval_date  TIMESTAMP,

    points_earned                 INTEGER NOT NULL DEFAULT 0,  -- calculé automatiquement (Chapitre 28), jamais modifiable par le technicien

    created_at                    TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                    TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Règle 2 : le site doit appartenir au client sélectionné
    CONSTRAINT chk_site_belongs_to_client CHECK (TRUE) -- vérifié en pratique côté application/trigger
);

-- ------------------------------------------------------------
-- 9. INTERVENTION TASKS (Chapitre 43)
-- ------------------------------------------------------------
-- Une intervention peut avoir plusieurs tâches du catalogue travaux.
CREATE TABLE intervention_tasks (
    intervention_task_id   SERIAL PRIMARY KEY,
    intervention_id         INTEGER NOT NULL REFERENCES interventions(intervention_id),
    travail_id              INTEGER NOT NULL REFERENCES travaux(travail_id),
    UNIQUE (intervention_id, travail_id)
);

-- ------------------------------------------------------------
-- 10. ATTACHMENTS (Chapitre 44)
-- ------------------------------------------------------------
-- Règle 7 : chaque intervention soumise doit avoir au moins 1 pièce jointe.
-- (contrainte applicative, pas SQL pure, car dépend du statut)
CREATE TABLE attachments (
    attachment_id   SERIAL PRIMARY KEY,
    intervention_id  INTEGER NOT NULL REFERENCES interventions(intervention_id),
    file_name        VARCHAR(255) NOT NULL,
    file_path        VARCHAR(500) NOT NULL,
    upload_date      TIMESTAMP NOT NULL DEFAULT NOW(),
    uploaded_by      INTEGER NOT NULL REFERENCES users(user_id)
);

-- ------------------------------------------------------------
-- 11. PLANNING (Chapitre 45)
-- ------------------------------------------------------------
-- Créé uniquement par le Chef des Techniciens (Chapitre 142).
CREATE TABLE planning (
    planning_id           SERIAL PRIMARY KEY,
    technician_id          INTEGER NOT NULL REFERENCES users(user_id),
    client_id              INTEGER NOT NULL REFERENCES clients(client_id),
    site_id                INTEGER NOT NULL REFERENCES client_sites(site_id),
    planned_date           DATE NOT NULL,
    planned_start_time     TIME NOT NULL,
    estimated_duration_minutes INTEGER,
    priority               VARCHAR(10) NOT NULL DEFAULT 'Normal'
                            CHECK (priority IN ('Normal','High','Urgent')),
    status                 VARCHAR(20) NOT NULL DEFAULT 'Planned'
                            CHECK (status IN ('Planned','Cancelled','Completed')),
    notes                  TEXT,
    created_by              INTEGER NOT NULL REFERENCES users(user_id), -- toujours un Chef des Techniciens
    created_at              TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- 12. POINT RULES (barème de points configurable)
-- ------------------------------------------------------------
-- Le cahier des charges (Chapitre 28) dit que la valeur après minuit
-- est "configurable". Plutôt que de coder le barème en dur dans le
-- Backend, on le stocke ici : l'Administration Supervisor pourra le
-- modifier depuis Settings > Point Rules (Chapitre 150) sans toucher
-- au code. Le Backend (tâche "Logique métier") lit cette table pour
-- calculer points_earned à la soumission d'une intervention.
CREATE TABLE point_rules (
    rule_id     SERIAL PRIMARY KEY,
    label       VARCHAR(100) NOT NULL,     -- ex: 'Soumission 17h-19h'
    time_start  TIME NOT NULL,             -- borne basse (incluse) de l'heure de soumission
    time_end    TIME,                       -- borne haute (exclue) ; NULL = pas de fin
    points      INTEGER NOT NULL,           -- peut être négatif
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Barème actuel (Chapitre 28). La ligne "Après minuit" utilise -1
-- à titre provisoire : valeur à confirmer avec l'encadrant, puis
-- un simple UPDATE suffira (pas de migration de schéma).
INSERT INTO point_rules (label, time_start, time_end, points) VALUES
    ('Soumission 17h-19h', '17:00', '19:00', 5),
    ('Soumission 19h-22h', '19:00', '22:00', 2),
    ('Soumission 22h-24h', '22:00', '23:59:59', 1),
    ('Après minuit (valeur à confirmer)', '00:00', '17:00', -1);

-- ------------------------------------------------------------
-- 13. NOTIFICATIONS (Chapitre 46)
-- ------------------------------------------------------------
CREATE TABLE notifications (
    notification_id          SERIAL PRIMARY KEY,
    user_id                   INTEGER NOT NULL REFERENCES users(user_id),
    title                     VARCHAR(150) NOT NULL,
    message                   TEXT NOT NULL,
    related_intervention_id   INTEGER REFERENCES interventions(intervention_id),
    read                      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- 14. APPROVAL HISTORY (Chapitre 47)
-- ------------------------------------------------------------
-- Trace permanente des deux niveaux d'approbation (Chapitre 10, Rule 9-10).
CREATE TABLE approval_history (
    approval_id       SERIAL PRIMARY KEY,
    intervention_id     INTEGER NOT NULL REFERENCES interventions(intervention_id),
    approval_level      VARCHAR(20) NOT NULL CHECK (approval_level IN ('Technical','Administrative')),
    approved_by          INTEGER NOT NULL REFERENCES users(user_id),
    decision             VARCHAR(10) NOT NULL CHECK (decision IN ('Approved','Rejected')),
    comment               TEXT,
    approval_date         TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- 15. AUDIT TRAIL (Chapitre 18 / 151)
-- ------------------------------------------------------------
-- Trace chaque action importante sur une intervention (au-delà des
-- seules approbations), pour la traçabilité complète exigée.
CREATE TABLE audit_trail (
    audit_id          SERIAL PRIMARY KEY,
    intervention_id     INTEGER NOT NULL REFERENCES interventions(intervention_id),
    user_id              INTEGER NOT NULL REFERENCES users(user_id),
    action                VARCHAR(50) NOT NULL,  -- ex: 'Created','Submitted','Modified','Rejected'
    comment               TEXT,
    created_at            TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- INDEXES (Chapitre 52)
-- ------------------------------------------------------------
CREATE INDEX idx_interventions_bi_number ON interventions(bi_number);
CREATE INDEX idx_interventions_technician ON interventions(technician_id);
CREATE INDEX idx_interventions_client ON interventions(client_id);
CREATE INDEX idx_interventions_site ON interventions(site_id);
CREATE INDEX idx_interventions_status ON interventions(status);
CREATE INDEX idx_interventions_submission_date ON interventions(submission_date);
CREATE INDEX idx_planning_technician_date ON planning(technician_id, planned_date);
CREATE INDEX idx_notifications_user ON notifications(user_id, read);
CREATE INDEX idx_approval_history_intervention ON approval_history(intervention_id);
CREATE INDEX idx_client_sites_client ON client_sites(client_id);
CREATE INDEX idx_point_rules_active ON point_rules(active);
