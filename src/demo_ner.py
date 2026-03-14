import spacy

nlp = spacy.load("en_core_web_sm")

overview = """
Dom Cobb is a skilled thief who steals secrets from people's dreams.
Set in Paris and Tokyo, this 2010 film explores the subconscious mind.
"""

doc = nlp(overview)

print("Entitles found:")
for ent in doc.ents:
    print(f" '{ent.text}' → {ent.label_} ({spacy.explain(ent.label_)})")