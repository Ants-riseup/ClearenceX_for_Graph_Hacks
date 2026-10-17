MATCH (s:Shipment {id:$shipment_id, revision:$revision})-[:HAS_DOCUMENT]->(source:Document {id:$source_id})
MATCH (affected)-[:DEPENDS_ON*1..4]->(source)
WHERE affected.shipment_id = $shipment_id AND affected.revision = $revision
  AND (affected:Decision OR affected:Memory OR affected:ReviewTask)
RETURN DISTINCT affected.id, labels(affected)[0] ORDER BY affected.id LIMIT 101
