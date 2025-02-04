# ASVS bot

This repo includes ASVS-v5-with-ada-002.backup: graph representation of ASVS v5 with pre-calculated vector embeddings and vector index.

Import it to your Aura instance or your local Neo4j server and use the connection URI and the credentials

It has several scripts that can be run locally (or adapted and deployed in your environment)

To run the bot:
`> streamlit run asvs_bot.py`

If you want to import a fresh version of ASVS and recalculate the embeddings use code under `/parser`.

For more details, see https://neo4j.com/developer-blog/asvs-security-graph-chatbot/

## To run locally, set the following env variables:
- NEO4J_URI
- NEO4J_USER
- NEO4J_PASS
- OPENAI_KEY
