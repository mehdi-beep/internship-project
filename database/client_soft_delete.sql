-- ============================================================
-- TÂCHE : SUPPRIMER LES CLIENTS DE LA BD (soft delete)
-- ============================================================
-- Règle du cahier des charges (Chapitre 50 - Cascade Rules) :
-- aucune suppression physique. On désactive via active = FALSE.
-- Les contrats, projets, sites et interventions liés à ce client
-- restent INTACTS en base (traçabilité complète, Chapitre 9/18).
-- ============================================================

-- 1. "Supprimer" un client = le désactiver
-- --------------------------------------------------------
-- Exemple : désactiver le client ID 7
UPDATE clients
SET active = FALSE
WHERE client_id = 7;

-- 2. Ce qu'il faut faire voir/cacher côté application (Frontend)
-- --------------------------------------------------------
-- Le dropdown "Client" du formulaire d'intervention (Chapitre 22
-- Section B) doit uniquement lister les clients actifs :
--
-- SELECT client_id, client_name FROM clients WHERE active = TRUE ORDER BY client_name;

-- 3. Les données déjà liées à ce client restent visibles
-- --------------------------------------------------------
-- Un client désactivé garde tout son historique consultable
-- (utile pour les rapports/audit, Chapitre 9) :
--
-- SELECT * FROM interventions WHERE client_id = 7;      -- reste consultable
-- SELECT * FROM contracts WHERE client_id = 7;            -- reste consultable
-- SELECT * FROM client_sites WHERE client_id = 7;          -- reste consultable
--
-- Rien de tout ça n'est supprimé ni caché automatiquement :
-- seule la CRÉATION de nouvelles interventions pour ce client
-- doit être bloquée côté application (validation Backend).

-- 4. Réactiver un client (annuler la "suppression")
-- --------------------------------------------------------
UPDATE clients
SET active = TRUE
WHERE client_id = 7;

-- 5. Bonus : lister les clients désactivés (utile pour l'écran
--    "Clients archivés" côté Administration Supervisor)
-- --------------------------------------------------------
SELECT client_id, client_name, phone, email
FROM clients
WHERE active = FALSE
ORDER BY client_name;
