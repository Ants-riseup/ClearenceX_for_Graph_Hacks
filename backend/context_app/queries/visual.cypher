MATCH (n {shipment_id:$shipment_id, revision:$revision})
OPTIONAL MATCH (n)-[r]->(m {shipment_id:$shipment_id, revision:$revision})
RETURN n.id, n.node_type, n.payload, type(r), m.id LIMIT 2001
