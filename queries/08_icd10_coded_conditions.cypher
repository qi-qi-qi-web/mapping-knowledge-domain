// Case 08: conditions with a curated ICD-10 code.
// No parameters.
MATCH (d:Condition)
WHERE d.icd10 IS NOT NULL AND d.icd10 <> ''
RETURN d.id AS condition_id,
       d.label_zh AS label_zh,
       d.icd10 AS icd10
ORDER BY icd10, condition_id
