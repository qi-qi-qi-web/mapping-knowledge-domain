// Case 03: red-flag findings for conditions linked to one complaint.
// Parameter: complaint_id (for example 'cc.chest_pain').
MATCH (c:ChiefComplaint {id: $complaint_id})-[:MAY_INDICATE]->(d:Condition)-[r:HAS_RED_FLAG]->(f:Finding)
RETURN d.id AS condition_id,
       d.label_zh AS condition_label,
       f.id AS finding_id,
       f.label_zh AS finding_label,
       r.source_id AS source_id,
       r.quote AS quote
ORDER BY condition_id, finding_id
