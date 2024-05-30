
import os
import streamlit as st
from openai import OpenAI
from langchain_community.graphs import Neo4jGraph

NEO4J_URL = os.environ['NEO4J_URI']
NEO4J_USER = os.environ['NEO4J_USER']
NEO4J_PASSWORD = os.environ['NEO4J_PASS']
OPENAI_KEY = os.environ['OPENAI_API_KEY']

EMBEDDING_MODEL = "text-embedding-ada-002"
OPENAI_MODEL = "gpt-4-turbo"  # replace with gpt-4 for production

st.title('🦜🔗 AppSec Verification Standard (ASVS) Chat App')
st.write("This program looks up ASVS requirements relevant to your feature description.")
with st.sidebar:
    st.subheader("Browse the full ASVS:")
    st.write("https://github.com/OWASP/ASVS/tree/master/4.0/en")
    st.subheader("Here is an example of feature description:")
    st.markdown('''_We want to add some pay-per-use features in our SaaS product. Each cloud tenant will have
     an agent monitoring the usage of these features. The agents send data through a custom proxy to BigQuery.
     We will use the data in BigQuеry to bill the customers._ 
    ''')
    st.subheader("Some params you can tweak:")
    num_reqs = st.number_input("Maximum number of ASVS requirements to take into account", 2, 20, value=10,
                                help='''Number of reqs above similarity threshold to pass to OpenAI."
                                  If you have lots of relevant requirements, increase this param to pass them on.''')
    threshold = st.number_input("Cut-off for low scoring matches", 0.5, 0.99, value=0.87,
                                help='''Semantic similarity threshold in vector lookup, 0.99 is the most strict.
                                        0.85 seems reasonable, but YMMV. Passing in irrelevant reqs will lead to
                                        hallucinations.''')

    st.subheader("Bring your own key:")
    open_api_key = st.text_input("OpenAI API Key", type="password")

llm = OpenAI()

graph = Neo4jGraph(
    url=NEO4J_URL,
    username=NEO4J_USER,
    password=NEO4J_PASSWORD
)

# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = OPENAI_MODEL

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def generate_response(input_text):
    embedding = llm.embeddings.create(input=input_text, model=EMBEDDING_MODEL)

    r = graph.query("""

        // 2. Find other requirements which have high semantic similarity on description
        CALL db.index.vector.queryNodes("embeddingIndex", $lookup_num, $feature_embedding) YIELD node, score
        WITH node, score
        WHERE score > $threshold // exclude low-scoring matches

        // 3. From the returned Embedding nodes, find their connected Requirement nodes
        MATCH (m2:Requirement)-[:HAS_EMBEDDING]->(node)
        WHERE node.key = '`Verification Requirement`'

        RETURN  m2.`#` AS reqNumber, m2.`Verification Requirement` AS requirement, score
        ORDER BY score DESC;""",
                    {'feature_embedding': embedding.data[0].embedding,
                            'lookup_num': num_reqs,
                            'threshold': threshold})

    if not r:
        # The graph didn't return anything, abandon mission
        st.write('''Your feature description doesn't bring up any relevant ASVS requirements, maybe it doesn't have
                    security impact? Lucky you! Maybe try a lower cut-off, just to be sure''')
        return "Come back with your next feature."

    with st.expander("Here are some requirements for your feature in descending order of relevance, click for details"):
        for entry in r:
            st.write(entry)

    messages = [{
        "role": "system",
        "content": """
            You are an application security specialist. Your role is to assist developers in
            identifying relevant security requirements. You are knowledgeable about OWASP and ASVS in particular
            Attempt to answer the users question with the context provided.
            Respond in a short, but friendly way.
            Use your knowledge to fill in any gaps, but no hallucinations please.
            If you cannot answer the question, ask for more clarification.
            When formatting your answer, break long text to multiple lines of
            up to 70 characters
            """
    }, {
        "role": "assistant",
        "content": """
                Your Context:
                {}
            """.format(r)
    }, {
        "role": "user",
        "content": """
            Answer the users question, wrapped in three backticks:

            ```
            {}
            ```
            """.format(input_text)
    }]

    with st.spinner("Let me summarise it for you..."):
        # Send the message to OpenAI
        chat_completion = llm.chat.completions.create(model=OPENAI_MODEL, messages=messages)

    return chat_completion.choices[0].message.content


with st.form('my_form'):
    text = st.text_area('Provide a paragraph describing your feature:', 'As a Neo4j PM...')
    submitted = st.form_submit_button('Submit')

    if submitted:
        response = generate_response(text)
        if not response:
            st.write("Something went wrong with OpenAI call.")
        else:
            st.write(response)
