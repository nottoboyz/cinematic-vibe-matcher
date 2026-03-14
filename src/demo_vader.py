from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

overviews = {
    "Inception": "A mind-bending thriller full of tension and dark sercrets",
    "Toy Story": "A wonderful heartwarming adventure filled with joy and friendship",
    "No Country": "Brutal violence and relentless pursuit. Dark and hopeless."
}

for title, text in overviews.items():
    scores = analyzer.polarity_scores(text)
    print(f"\n{title}:")
    print(f" Positive: {scores['pos']:.3f}")
    print(f" Negative: {scores['neg']:.3f}")
    print(f" Neutral:  {scores['neu']:.3f}")
    print(f" Compound: {scores['compound']:.3f}")