// Case 09: all incoming and outgoing evidence for one condition.
// Parameter: condition_id (for example 'cond.aad').
MATCH (d:Condition {id: $condition_id})-[r]-(o:Entity)
RETURN type(r) AS predicate,
       startNode(r).id AS subject_id,
       endNode(r).id AS object_id,
       o.id AS other_id,
       o.label_zh AS other_label,
       r.source_id AS source_id,
       r.quote AS quote
ORDER BY predicate, subject_id, object_id
