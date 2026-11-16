// Case 10: fact counts by source, for provenance coverage review.
// No parameters.
MATCH ()-[r]->()
WHERE r.source_id IS NOT NULL
RETURN r.source_id AS source_id,
       count(*) AS facts
ORDER BY facts DESC, source_id
