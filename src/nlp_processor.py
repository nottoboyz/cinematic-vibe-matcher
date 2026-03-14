# src/nlp_processor.py

from sentence_transformers import SentenceTransformer
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class NLPProcessor:
    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.nlp = spacy.load("en_core_web_sm")
        self.analyzer = SentimentIntensityAnalyzer()

    def get_embedding(self, text: str) -> list:
        if not text or not text.strip():
            return [0.0] * 768 # return vector ว่างแทน error
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def extract_entities(self, text: str) -> dict:
        doc = self.nlp(text)

        result = {"persons": [], "locations": [], "dates": []}

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                result["persons"].append(ent.text)
            elif ent.label_ == "GPE":
                result["locations"].append(ent.text)
            elif ent.label_ == "DATE":
                result["dates"].append(ent.text)

        return result
    
    def get_sentiment(self, text: str) -> float:
        scores = self.analyzer.polarity_scores(text)
        return scores['compound']