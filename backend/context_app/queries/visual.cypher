MATCH (n {shipment_id:$shipment_id, revision:$revision})
OPTIONAL MATCH (n)-[r]->(m {shipment_id:$shipment_id, revision:$revision})
RETURN n.id, labels(n)[0], n.payload, type(r), m.id LIMIT 2001
