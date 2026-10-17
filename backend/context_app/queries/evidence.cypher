MATCH (s:Shipment {id:$shipment_id, revision:$revision})-[:HAS_FIELD]->(f:CanonicalField {id:$field_id})
MATCH (s)-[:HAS_DOCUMENT]->(d:Document)-[:CONTAINS]->(a:Assertion)-[:ASSERTS_VALUE_FOR]->(f)
WHERE d.active = true AND a.active = true
RETURN a.payload ORDER BY a.id LIMIT 101
