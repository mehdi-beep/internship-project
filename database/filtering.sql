-- ============================================================
-- TÂCHE : FILTRER (interventions)
-- ============================================================
-- Cahier des charges, Chapitre 69 - Filters :
-- Date, Client, Technicien, Statut, Priorité, Projet, Contrat,
-- Site, Type d'intervention. Combinables entre eux.
--
-- En pratique, le Backend construit dynamiquement la clause WHERE
-- selon les filtres réellement choisis par l'utilisateur (un
-- technicien ne filtre que ses propres interventions, un Chef ou
-- l'Administration peuvent filtrer sur tout le monde - Chapitre 16).
-- Les requêtes ci-dessous sont des exemples de référence.
-- ============================================================

-- 1. Filtre simple : par statut
-- --------------------------------------------------------
SELECT * FROM interventions
WHERE status = 'Pending Technical Approval'
ORDER BY submission_date DESC;

-- 2. Filtre simple : par technicien
-- --------------------------------------------------------
SELECT * FROM interventions
WHERE technician_id = 6
ORDER BY intervention_date DESC;

-- 3. Filtre par plage de dates
-- --------------------------------------------------------
SELECT * FROM interventions
WHERE intervention_date BETWEEN '2026-07-01' AND '2026-07-31'
ORDER BY intervention_date;

-- 4. Combinaison : client + statut + priorité
-- --------------------------------------------------------
SELECT * FROM interventions
WHERE client_id = 3
  AND status = 'Fully Approved'
  AND priority = 'Urgent'
ORDER BY intervention_date DESC;

-- 5. Combinaison large : tous les filtres du Chapitre 69 à la fois
-- --------------------------------------------------------
-- (exemple générique montrant comment tout combiner ; en pratique
-- le Backend n'ajoute que les conditions correspondant aux filtres
-- réellement sélectionnés par l'utilisateur)
SELECT i.*
FROM interventions i
WHERE (i.intervention_date BETWEEN '2026-07-01' AND '2026-08-31')
  AND (i.client_id = 3)
  AND (i.technician_id = 6)
  AND (i.status = 'Fully Approved')
  AND (i.priority IN ('High', 'Urgent'))
  AND (i.project_id = 2)
  AND (i.contract_id IS NULL)          -- exemple : pas de contrat
  AND (i.site_id = 5)
  AND (i.intervention_type = 'Project')
ORDER BY i.intervention_date DESC;

-- 6. Filtre par technicien ASSIGNÉ (vue "Technician") vs vue globale
-- --------------------------------------------------------
-- Un Technician ne doit voir QUE ses propres interventions
-- (Chapitre 16 - Intervention Visibility). Le Backend applique
-- automatiquement ce filtre selon le rôle connecté, en plus des
-- filtres choisis par l'utilisateur :
SELECT * FROM interventions
WHERE technician_id = :current_user_id   -- imposé par le Backend, pas par l'utilisateur
  AND status = 'Rejected';               -- filtre choisi par le technicien lui-même

-- 7. Recherche instantanée (Chapitre 68 - Search Module)
-- --------------------------------------------------------
-- BI Number, Client, Site, Technicien, Projet, Contrat, Statut.
-- Utilise ILIKE pour une recherche insensible à la casse.
SELECT i.intervention_id, i.bi_number, c.client_name, u.first_name, u.last_name
FROM interventions i
JOIN clients c ON c.client_id = i.client_id
JOIN users u ON u.user_id = i.technician_id
WHERE i.bi_number ILIKE '%000123%'
   OR c.client_name ILIKE '%orange%'
   OR u.last_name ILIKE '%ait ali%'
ORDER BY i.intervention_date DESC
LIMIT 20;

-- 8. Filtres sur le Planning (Chapitre 63)
-- --------------------------------------------------------
SELECT * FROM planning
WHERE technician_id = 6
  AND planned_date BETWEEN '2026-08-10' AND '2026-08-16'
  AND priority = 'Urgent'
ORDER BY planned_date, planned_start_time;
