// Case 05: initial tests recommended for one chief complaint.
// Parameter: complaint_id (for example 'cc.dyspnea').
MATCH (c:ChiefComplaint {id: $complaint_id})-[r:RECOMMENDED_TEST]->(t:Test)
RETURN t.id AS test_id,
       t.label_zh AS test_label,
       r.priority AS priority,
       r.timing AS timing,
       r.context AS context,
       r.source_id AS source_id,
       r.quote AS quote
ORDER BY test_id
