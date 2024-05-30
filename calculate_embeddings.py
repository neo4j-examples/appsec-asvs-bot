from neo4j import GraphDatabase, Query
from openai.embeddings_utils import get_embedding
import openai
import os

"""
LoadEmbedding: call OpenAI embedding API to generate embeddings for each property of node in Neo4j
Version: 1.1
"""

EMBEDDING_MODEL = "text-embedding-ada-002"

NEO4J_URL = os.environ['NEO4J_URI']
NEO4J_USER = os.environ['NEO4J_USER']
NEO4J_PASSWORD = os.environ['NEO4J_PASS']
OPENAI_KEY = os.environ['OPENAI_KEY']


class LoadEmbedding:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        openai.api_key = OPENAI_KEY

    def close(self):
        self.driver.close()

    def load_embedding_to_node_property(self, node_label, node_property):
        self.driver.verify_connectivity()

        with self.driver.session(database="neo4j") as session:

            result = session.run(f"""
                MATCH (a:{node_label})
                WHERE a.{node_property} IS NOT NULL
                RETURN id(a) AS id, a.{node_property} AS node_property
            """)


            # call OpenAI embedding API to generate embeddings for each property of node
            # for each node, update the embedding property
            count = 0
            for record in result.data():
                id = record["id"]
                text = record["node_property"]
                # Below, instead of using the text as the input for embedding, we add label and property name in
                # front of it
                embedding = get_embedding(f"{node_label} {node_property} - {text}", EMBEDDING_MODEL)
                # key property of Embedding node differentiates different embeddings
                cypher = "CREATE (e:Embedding) SET e.key=$key, e.value=$embedding"
                cypher = cypher + " WITH e MATCH (n) WHERE id(n) = $id CREATE (n) -[:HAS_EMBEDDING]-> (e)"
                session.run(cypher, key=node_property, embedding=embedding, id=id)
                count = count + 1

            print("Processed " + str(count) + " " + node_label + " nodes for property @" + node_property + ".")
            return count


if __name__ == "__main__":
    loader = LoadEmbedding(NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD)
    loader.load_embedding_to_node_property("Control", "`Control Name`")
    loader.load_embedding_to_node_property("Area", "Area")
    loader.load_embedding_to_node_property("Requirement", "`Verification Requirement`")
    print("done")
    loader.close()
