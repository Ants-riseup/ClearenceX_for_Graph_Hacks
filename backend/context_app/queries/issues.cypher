MATCH (s:Shipment {id:$shipment_id, revision:$revision})-[:HAS_FIELD]->(f:CanonicalField)
RETURN f.payload ORDER BY f.id LIMIT 101
