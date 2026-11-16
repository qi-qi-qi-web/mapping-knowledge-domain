// Case 07: levels and criteria for one triage scale.
// Parameter: scale_id (for example 'esi_v4_2005').
MATCH (s:TriageScale {scale_id: $scale_id})-[:HAS_LEVEL]->(l:TriageLevel)-[r:LEVEL_CRITERION]->(crit:Entity)
RETURN l.level AS level,
       l.label_zh AS level_label,
       crit.id AS criterion_id,
       crit.label_zh AS criterion_label,
       r.criterion_type AS criterion_type,
       r.source_id AS source_id,
       r.quote AS quote
ORDER BY toInteger(l.level), criterion_id
