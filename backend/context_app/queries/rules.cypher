MATCH (s:Shipment {id:$shipment_id, revision:$revision})-[:HAS_FIELD]->(f:CanonicalField {id:$field_id})
MATCH (e:RuleEvaluation)-[:EVALUATES]->(f)
MATCH (e)-[:USES_RULE]->(r:Rule)
RETURN e.payload, r.payload LIMIT 10
