# Knowledge base: read the report PDFs, cut them into small pieces ("chunks"),
# and find the pieces that best match a question. No AI here, just Python.
import math
import re
from pypdf import PdfReader

STOP_WORDS = set("""a an the of in on for to and or is are was were be been what which who how many much
when where why did does do with by from at as it its this that these those there their they you your
i me my we our can could would should will about into than then so if not no yes please tell show""".split())


def load_chunks(pdf_files, size=150, step=120):
    """Return a list of {"file", "page", "text"} pieces of about `size` words."""
    chunks = []
    for name in pdf_files:
        reader = PdfReader(name)
        for page_no, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            # drop the running header that repeats on every page, so it does not confuse the search
            text = re.sub(r"Dubai Residential Market Review\s*-\s*Q\d \d{4}", " ", text)
            words = text.split()
            for start in range(0, len(words), step):
                text = " ".join(words[start:start + size])
                if len(text) > 80:
                    chunks.append({"file": name, "page": page_no, "text": text})
    return chunks


def stem(word):
    """Very small 'stemmer' so communities -> community, prices -> price."""
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def tokens(text):
    return [stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP_WORDS]


def search(chunks, question, top=4):
    """Score every chunk by how many question words it contains; return the best ones."""
    q_words = set(tokens(question))
    all_words = [set(tokens(c["text"])) for c in chunks]
    # rare words matter more: a word found in 1 chunk is a stronger clue than one found in every chunk
    weight = {w: math.log((len(chunks) + 1) / (1 + sum(w in ws for ws in all_words))) + 1 for w in q_words}
    scored = []
    for chunk in chunks:
        c_words = tokens(chunk["text"])
        score = sum(min(c_words.count(w), 3) * weight[w] for w in q_words)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [chunk for score, chunk in scored[:top]]


if __name__ == "__main__":
    chunks = load_chunks(["q1-2026.pdf"])
    print("Chunks:", len(chunks))
    for q in ["How many homes above $10 million were sold?",
              "Which community has the biggest pipeline supply?",
              "What happened to prime prices?"]:
        best = search(chunks, q, top=1)
        print("\nQ:", q)
        print("Best match (page %d):" % best[0]["page"], best[0]["text"][:250] if best else "nothing found")
