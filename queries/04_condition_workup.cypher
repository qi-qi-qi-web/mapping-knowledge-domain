// Case 04: recommended tests for one condition, with priority and timing.
// Parameter: condition_id (for example 'cond.acute_mi').
MATCH (d:Condition {id: $condition_id})-[r:RECOMMENDED_TEST]->(t:Test)
RETURN t.id AS test_id,
       t.label_zh AS test_label,
       r.priority AS priority,
       r.timing AS timing,
       r.context AS context,
       r.source_id AS source_id,
       r.quote AS quote
ORDER BY test_id
