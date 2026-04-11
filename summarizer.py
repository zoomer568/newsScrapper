from transformers import BartForConditionalGeneration, BartTokenizer
import os

MODEL_PATH = '/workspaces/newsScrapper/models/bart_xsum_model'

_model = None
_tokenizer = None

def load_model():
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        if os.path.exists(MODEL_PATH):
            _model = BartForConditionalGeneration.from_pretrained(MODEL_PATH)
            _tokenizer = BartTokenizer.from_pretrained(MODEL_PATH)
            print("Model and tokenizer loaded successfully.")
        else:
            raise FileNotFoundError(f"Model path not found: {MODEL_PATH}")
    return _model, _tokenizer

def summarize(article_text, max_length=164, num_beams=4):
    model, tokenizer = load_model()
    
    inputs = tokenizer(article_text, max_length=1024, truncation=True, return_tensors="pt")
    
    summary_ids = model.generate(
        inputs["input_ids"],
        num_beams=num_beams,
        max_length=max_length,
        early_stopping=True
    )
    
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

if __name__ == "__main__":
    test_article = """
    City Council voted 6-1 to approve a proposal to transform a three-block corridor of underused lots 
    in the city center into a new public park and greenway. The initiative will begin construction 
    this summer with a projected opening in late 2027.
    """
    
    summary = summarize(test_article)
    print(f"Summary: {summary}")