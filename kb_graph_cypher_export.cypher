// ============ CREATE CONSTRAINTS ============
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT category_id IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT query_text IF NOT EXISTS FOR (q:Query) REQUIRE q.text IS UNIQUE;

// ============ CREATE INDEXES ============
CREATE INDEX user_type IF NOT EXISTS FOR (u:User) ON (u.type);
CREATE INDEX product_type IF NOT EXISTS FOR (p:Product) ON (p.type);

// ============ SAMPLE NODES ============
CREATE (u0:User {id: 1, type: 'User'});
CREATE (u1:User {id: 2, type: 'User'});
CREATE (u2:User {id: 3, type: 'User'});
CREATE (u3:User {id: 4, type: 'User'});
CREATE (u4:User {id: 5, type: 'User'});
CREATE (p0:Product {id: 1, category: 'Electronics', type: 'Product'});
CREATE (p1:Product {id: 2, category: 'Clothing', type: 'Product'});
CREATE (p2:Product {id: 3, category: 'Clothing', type: 'Product'});
CREATE (p3:Product {id: 4, category: 'Garden', type: 'Product'});
CREATE (p4:Product {id: 5, category: 'Electronics', type: 'Product'});
CREATE (c0:Category {id: 'Automotive', type: 'Category'});
CREATE (c1:Category {id: 'Beauty', type: 'Category'});
CREATE (c2:Category {id: 'Books', type: 'Category'});
CREATE (c3:Category {id: 'Clothing', type: 'Category'});
CREATE (c4:Category {id: 'Electronics', type: 'Category'});

// ============ SAMPLE EDGES ============
MATCH (u:User {id: 456}), (p:Product {id: 443})
CREATE (u)-[:INTERACTED {weight: 2.5}]->(p);
MATCH (u:User {id: 314}), (p:Product {id: 257})
CREATE (u)-[:INTERACTED {weight: 2.0}]->(p);
MATCH (u:User {id: 417}), (p:Product {id: 450})
CREATE (u)-[:INTERACTED {weight: 1.0}]->(p);
MATCH (u:User {id: 116}), (p:Product {id: 676})
CREATE (u)-[:INTERACTED {weight: 1.0}]->(p);
MATCH (u:User {id: 245}), (p:Product {id: 270})
CREATE (u)-[:INTERACTED {weight: 0.5}]->(p);
MATCH (p:Product {id: 210}), (c:Category {id: 'Clothing'}) 
CREATE (p)-[:BELONGS_TO]->(c);
MATCH (p:Product {id: 344}), (c:Category {id: 'Clothing'}) 
CREATE (p)-[:BELONGS_TO]->(c);
MATCH (p:Product {id: 185}), (c:Category {id: 'Garden'}) 
CREATE (p)-[:BELONGS_TO]->(c);
MATCH (p:Product {id: 351}), (c:Category {id: 'Sports'}) 
CREATE (p)-[:BELONGS_TO]->(c);
MATCH (p:Product {id: 153}), (c:Category {id: 'Electronics'}) 
CREATE (p)-[:BELONGS_TO]->(c);