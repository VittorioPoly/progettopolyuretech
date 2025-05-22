-- Migration: aggiungi colonna percentuale a dipendente_competenza
-- Esegui questo script una sola volta!
 
ALTER TABLE dipendente_competenza ADD COLUMN percentuale INTEGER DEFAULT 0; 