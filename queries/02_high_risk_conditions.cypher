// Case 02: all high-risk conditions with presentation and red-flag counts.
// No parameters.
MATCH (d:Condition {risk: 'high'})
OPTIONAL MATCH (d)-[:PRESENTS_WITH]->(f:Finding)
OPTIONAL MATCH (d)-[:HAS_RED_FLAG]->(rf:Finding)
RETURN d.id AS condition_id,
       d.label_zh AS label_zh,
       d.icd10 AS icd10,
       count(DISTINCT f) AS presentations,
       count(DISTINCT rf) AS red_flags
ORDER BY condition_id
