// Case 01: differential diagnoses for one chief complaint.
// Parameter: complaint_id (for example 'cc.chest_pain').
MATCH (c:ChiefComplaint {id: $complaint_id})-[r:MAY_INDICATE]->(d:Condition)
RETURN d.id AS condition_id,
       d.label_zh AS label_zh,
       coalesce(r.risk, d.risk) AS risk,
       d.icd10 AS icd10,
       r.source_id AS source_id,
       r.quote AS quote
ORDER BY condition_id
