MATCH (s:Shipment {id:$shipment_id, revision:$revision})-[:HAS_DOCUMENT]->(source:Document {id:$source_id})
MATCH (affected)-[:DEPENDS_ON*1..4]->(source)
WHERE affected.shipment_id = $shipment_id AND affected.revision = $revision
  AND (affected:Decision OR affected:Memory OR affected:ReviewTask OR affected:ExportSnapshot OR affected:GoodsReview)
RETURN DISTINCT affected.id, CASE WHEN affected:Decision THEN 'Decision' WHEN affected:Memory THEN 'Memory' WHEN affected:ReviewTask THEN 'ReviewTask' WHEN affected:GoodsReview THEN 'GoodsReview' ELSE 'ExportSnapshot' END, affected.payload ORDER BY affected.id LIMIT 101
