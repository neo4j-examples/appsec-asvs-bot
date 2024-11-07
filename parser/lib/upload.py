import os

from neo4j import GraphDatabase

URI = os.environ['NEO4J_URI']
USER = os.environ['NEO4J_USER']
PASS = os.environ['NEO4J_PASS']


def get_driver():
    return GraphDatabase.driver(URI, auth=(USER, PASS))

def upload(data):
    driver = get_driver()

    with driver.session(database="neo4j") as s:
        print("Connection established.")

        # CHAPTERS
        print("Creating chapters...")

        s.run("""CREATE CONSTRAINT `uniq_standard` IF NOT EXISTS
                FOR (st:Standard)
                REQUIRE (st.name) IS UNIQUE
        """)

        s.run("""CREATE (n: `Standard` {`name`: 'ASVS', `version`: 'v5.0'})
        """)

        s.run("""CREATE CONSTRAINT `uniq_chapter_id` IF NOT EXISTS
                FOR (c:Chapter)
                REQUIRE (c.ID) IS UNIQUE
        """)

        s.run("""
            UNWIND $nodeRecords AS nodeRecord
            MERGE (c: `Chapter` { `ID`: nodeRecord.`ID` })
            SET c = nodeRecord
            WITH *
            MATCH (s: Standard)
            MERGE (s)-[:HAS_CHAPTER]->(c)
        """, {'nodeRecords': data['chapters']}).consume()

        # SECTIONS
        print("Creating sections...")

        s.run("""CREATE CONSTRAINT `uniq_section_id` IF NOT EXISTS
                FOR (s:Section)
                REQUIRE (s.ID) IS UNIQUE
        """)

        s.run("""
            UNWIND $nodeRecords AS nodeRecord
            MERGE (s: `Section` { `ID`: nodeRecord.`ID` })
            SET s = nodeRecord
            WITH *
            MATCH (c: Chapter {ID: nodeRecord.`chapterId`})
            MERGE (c)-[:HAS_SECTION]->(s)
        """, {'nodeRecords': data['sections']}).consume()

        # REQUIREMENTS
        print("Creating requirements...")

        s.run("""CREATE CONSTRAINT `uniq_req_id` IF NOT EXISTS
                FOR (r:Requirement)
                REQUIRE (r.ID) IS UNIQUE
        """)

        s.run("""
            UNWIND $nodeRecords AS nodeRecord
            MERGE (r: `Requirement` { `ID`: nodeRecord.`ID` })
            SET r = nodeRecord
            WITH *
            MATCH (s: Section {ID: nodeRecord.`sectionId`})
            MERGE (s)-[:HAS_REQUIREMENT]->(r)
        """, {'nodeRecords': data['requirements']}).consume()



    driver.close()