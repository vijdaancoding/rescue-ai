-- Migration: add room_name to call_sessions
-- Run this once against your Supabase database.
-- Safe to re-run (IF NOT EXISTS guard).

ALTER TABLE call_sessions
    ADD COLUMN IF NOT EXISTS room_name TEXT;
