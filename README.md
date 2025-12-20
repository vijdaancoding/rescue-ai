# 🚨 Alif Urdu Emergency Response

Fine-tuned Alif 8B model for Pakistani emergency call handling with high-quality Urdu dataset generation pipeline.

## Overview

This project creates a specialized Urdu language model for Rescue 1122 emergency operators. The model handles medical emergencies, fires, accidents, and natural disasters in authentic Pakistani Urdu.

**Key Features:**
- Pure Urdu dataset (no English contamination)
- 99/100 quality score
- Fine-tuned Alif 8B model
- Automated dataset generation

## Quick Start

```bash
# Setup
git clone <repository-url>
pip install -r requirements.txt

# Configure API (create .env file)
GCP_API_KEY="your-gemini-api-key"

# Generate dataset
python main.py

# Analyze quality
python analyze_conversational.py
```

## Dataset Format

```json
{
  "messages": [
    {
      "role": "user",
      "content": "ہیلو، مجھے مدد چاہیے! میرے والد کو دل کا دورہ پڑا ہے!"
    },
    {
      "role": "assistant", 
      "content": "آپ کہاں ہیں؟ مکمل پتہ بتائیں تاکہ ایمبولینس بھیج سکیں۔"
    }
  ]
}
```

## Model Usage

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Load fine-tuned model
tokenizer = AutoTokenizer.from_pretrained("large-traversaal/Alif-1.0-8B-Instruct")
base_model = AutoModelForCausalLM.from_pretrained("large-traversaal/Alif-1.0-8B-Instruct")
model = PeftModel.from_pretrained(base_model, "hamza-amin/alif-emergency-finetuned")

# Chat
def emergency_chat(prompt):
    text = f"### User:\n{prompt}\n\n### Assistant:\n"
    inputs = tokenizer(text, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=150)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

response = emergency_chat("میں کراچی سے بول رہا ہوں۔ یہاں آگ لگی ہے۔")
```

## Training Results

- **Base Model:** Alif-1.0-8B-Instruct
- **Method:** QLoRA (4-bit quantization)
- **Dataset:** 5,000 conversations
- **Training Loss:** 0.387
- **Validation Loss:** 0.396
- **Model:** [hamza-amin/alif-emergency-finetuned](https://huggingface.co/hamza-amin/alif-emergency-finetuned)

## Project Structure

```
├── data/alif_conversational_train.jsonl  # Training dataset
├── training/                             # Kaggle notebooks
├── config.py                            # Configuration
├── generator.py                         # Dataset generation
├── main.py                             # Main pipeline
├── analyze_conversational.py           # Quality analysis
└── test_new_pipeline.py               # Testing
```

## Quality Metrics

- **Language Purity:** 100% Urdu
- **Diversity:** 100% unique conversations
- **Coverage:** All major emergency types
- **Cultural Accuracy:** Pakistani locations and expressions

## Use Cases

- Emergency call centers
- Voice assistants
- Automated emergency guidance
- Operator training
- Urdu NLP research

---

*Built for Pakistani emergency response community*