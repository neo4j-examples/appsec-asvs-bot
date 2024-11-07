from langchain_text_splitters import MarkdownHeaderTextSplitter
import requests
from lib.upload import upload
from lib.vector import LoadEmbedding

chapters = []
sections = []
requirements = []

def create_chapter(md):
    chapter = dict()
    chapter['Control Objective'] = md.page_content
    chapter_num, sep, chapter_name = md.metadata['Chapter'].partition(" ")
    chapter['ID'] = chapter_num
    chapter['name'] = chapter_name
    chapters.append(chapter)

def update_chapter(md):
    chapter_num, sep, chapter_name = md.metadata['Chapter'].partition(" ")
    chapter = [c for c in chapters if c['ID'] == chapter_num]  # find the right existing chapter
    if not chapter:
        return
    chapter[0][f'{md.metadata['Section']}'] = md.page_content

def create_requirement(md, section_num):
    NIST = '' # Not all requirements have NIST reference, need to treat like optional
    if md.count("|") == 7:
        dummy1, req_num, req, L1, L2, L3, CWE, dummy2 = md.split('|')
    elif md.count("|") == 8:
        dummy1, req_num, req, L1, L2, L3, CWE, NIST, dummy2 = md.split('|')
    else: # who knows what is this, skipping for now
        return

    requirement = dict()
    requirement['ID'] = req_num.strip("' *")
    if req.startswith(' ['):
        requirement['Description'] = req.rsplit('] ')[1]
    else:
        requirement['Description'] = req
    if not requirement['Description']:
        return  # Some weird edge cases where "split to" doesn't leave anything behind, like 14.5.3
    requirement['CWE'] = CWE
    requirement['NIST'] = NIST
    requirement['L1'] = (L1 != ' ')
    requirement['L2'] = (L2 != ' ')
    requirement['L3'] = (L3 != ' ')
    requirement['sectionId'] = section_num
    requirements.append(requirement)

def create_section(chapter_num, section_num, name):
    section = [s for s in sections if s['ID'] == section_num]     # first check if it already exists
    if section:
        return

    section = dict(ID=section_num, name=name, chapterId = chapter_num, Description = '')
    sections.append(section)


def update_section(line, section_num):
    if line.startswith("| "): # This in not the kind of text we are after
        return
    section = [s for s in sections if s['ID'] == section_num]  # find the right existing section
    if not section:
        return
    section[0]['Description'] += line


def split_requirements(md):
    section_num, sep, section_name = md.metadata['Section'].removeprefix('V').partition(" ")
    chapter_num, sep, chapter_name = md.metadata['Chapter'].partition(" ")
    create_section(chapter_num, section_num, section_name)
    for line in md.page_content.splitlines():
        if not line.startswith(f"| **{section_num}"):
            update_section(line, section_num)
            continue # skip non-requirement lines
        if not any(trigger in line for trigger in ('DELETED', 'MOVED TO')):  # skip removed reqs
            print(line)
            create_requirement(line, section_num)


def weird_section(md):
    if ('References' in md or
            'Additional US Agency Requirements' in md or
            'Glossary of terms' in md or
            'Definition' in md):
        return True
    else:
        return False


def cleanup(data):
    clean_sections = []

    # Some sections don't have a description, we copy section name to have something useful there

    for section in data['sections']:
        clean_section = section
        if not clean_section['Description']:
            clean_section['Description'] = clean_section['name']

        clean_sections.append(clean_section)

    clean_data = {
        'chapters': chapters,
        'sections': clean_sections,
        'requirements': requirements
    }

    return clean_data

if __name__ == "__main__":

    targets = [
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x11-V2-Authentication.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x12-V3-Session-management.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x12-V4-Access-Control.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x13-V5-Validation-Sanitization-Encoding.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x14-V6-Cryptography.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x15-V7-Error-Logging.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x16-V8-Data-Protection.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x17-V9-Communications.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x18-V10-Malicious.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x19-V11-BusLogic.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x20-V12-Files-Resources.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x21-V13-API.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x22-V14-Config.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x50-V50-Web-Frontend-Security.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x51-V51-OAuth2.md",
        "https://github.com/irene221b/ASVS/raw/refs/heads/master/5.0/en/0x53-V53-WebRTC.md"
    ]

    headers_to_split_on = [
        ("#", "Chapter"),
        ("##", "Section")
    ]

    for target_url in targets:
        text = requests.get(target_url).text

        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
        md_header_splits = markdown_splitter.split_text(text)

        for doc in md_header_splits:
            print("============================")
            if 'Control Objective' in doc.metadata['Section']:
                print(doc.page_content)
                print(doc.metadata)
                create_chapter(doc)
            elif weird_section(doc.metadata['Section']):
                print(doc.page_content)
                print(doc.metadata)
                update_chapter(doc)
            else: # need to split requirements
                split_requirements(doc)
                print(doc.metadata)

    data = {
        'chapters': chapters,
        'sections': sections,
        'requirements': requirements
    }
    # #
    print("Parsing Complete!")
    #

    clean_data = cleanup(data)

    print("Loading to Neo4j...")
    upload(clean_data)
    print("Upload completed!")
    # #


    print("Calculating vector embeddings")
    loader = LoadEmbedding()

    loader.load_embedding_to_node_property("Chapter", "`Control Objective`")
    loader.load_embedding_to_node_property("Section", "Description")
    loader.load_embedding_to_node_property("Requirement", "Description")
    loader.create_index()
    loader.close()

    # print("Embeddings completed!")
  
