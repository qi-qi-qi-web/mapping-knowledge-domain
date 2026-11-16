// Case 06: treatment options for conditions indicated by one complaint.
// Parameter: complaint_id (for example 'cc.chest_pain').
MATCH (c:ChiefComplaint {id: $complaint_id})-[:MAY_INDICATE]->(d:Condition)<-[r:TREATS]-(i:Intervention)
RETURN d.id AS condition_id,
       d.label_zh AS condition_label,
       i.id AS intervention_id,
       i.label_zh AS intervention_label,
       r.urgency AS urgency,
       r.context AS context,
       r.source_id AS source_id,
       r.quote AS quote
ORDER BY condition_id, intervention_id
