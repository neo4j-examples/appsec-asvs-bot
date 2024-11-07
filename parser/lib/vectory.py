from openai import OpenAI
import os
from neo4j import GraphDatabase

NEO4J_URL = os.environ['NEO4J_URI']
NEO4J_USER = os.environ['NEO4J_USER']
NEO4J_PASSWORD = os.environ['NEO4J_PASS']
OPENAI_KEY = os.environ['OPENAI_API_KEY']

EMBEDDING_MODEL = "text-embedding-3-small"

class LoadEmbedding:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.client = OpenAI()
        self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def create_index(self):
        with self.driver.session(database="neo4j") as s:
            s.run("""
            CREATE VECTOR INDEX embeddingIndex IF NOT EXISTS
            FOR (s:Embedding)
            ON s.embedding
            OPTIONS { indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }};
            """)

    def load_embedding_to_node_property(self, node_label, node_property):
        with self.driver.session(database="neo4j") as s:

            # let's add extra label to these nodes, to signify they have embeddings

            result = s.run(
                f"""
                MATCH (a:{node_label})
                SET a:Embedding
                RETURN labels(a)
                """
            ).consume()

            # calculate embedding on name (if exists) + the required property
            # store as node property

            result = s.run(f"""
                MATCH (a: {node_label})
                WHERE a.{node_property} IS NOT NULL and a.embedding is NULL
                WITH a, coalesce(a.name,"") + " " + coalesce(a.{node_property},"") AS text
                WITH a, genai.vector.encode(text, "OpenAI", {{token: "{OPENAI_KEY}", model: "{EMBEDDING_MODEL}"}}) as embedding
                CALL db.create.setNodeVectorProperty(a, 'embedding', embedding)
                RETURN count(a) as count
            """)

            processed = result.data()[0]["count"]

            print(f"Processed {processed} {node_label} nodes for property {node_property}.")
