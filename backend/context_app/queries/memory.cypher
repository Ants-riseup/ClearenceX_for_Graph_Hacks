MATCH (m:Memory {shipment_id:$shipment_id, revision:$revision})-[:DERIVED_FROM]->(d:Decision)
WHERE m.status = 'active'
RETURN m.payload ORDER BY m.id LIMIT 101
