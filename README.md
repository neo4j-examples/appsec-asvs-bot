# ASVS bot

This repo includes ASVS-neo4j.dump: graph representation of ASVS v4.0.3 with pre-calculated vector embeddings and vector index.

Import it to your Aura instance or your local Neo4j server and use the connection URI and the credentials

It has two scripts that can be run locally (or adapted and deployed in your environment)

To run the bot:
`> streamlit asvs_bot.py`

If you want to recalculate the embeddings (with a different model or params), delete them and the index and recalculate using
`calculate_embeddings.py` as an example

For more details, see https://neo4j.com/developer-blog/asvs-security-graph-chatbot/


## To run locally, set the following env variables:
- NEO4J_URI
- NEO4J_USER
- NEO4J_PASS
- OPENAI_KEY
