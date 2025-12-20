# 🚨 Alif Urdu Emergency Response Dataset & Fine-tuning Pipeline

A comprehensive pipeline for generating high-quality Urdu emergency response conversations and fine-tuning the Alif 8B model for emergency call handling in Pakistan.

## 🎯 Overview

This project creates a specialized Urdu language model for handling emergency calls in Pakistan. The model is trained to respond as a Rescue 1122 operator, providing appropriate assistance for various emergency situations including medical emergencies, fires, accidents, and natural disasters.

**Key Features:**
- 🇵🇰 Pure Urdu language dataset (no English contamination)
- 🚑 Realistic Pakistani emergency scenarios
- 🤖 Fine-tuned Alif 8B model for emergency response
- 📊 High-quality conversational format (99/100 quality score)
- 🔄 Automated dataset generation pipeline

## 📁 Project Structure

```
├── data/
│   └── alif_conversational_train.jsonl    # Generated training dataset
├── training/
│   ├── fine-tuning-alif.ipynb            # Kaggle training notebook
│   └── Inference_My_Alif.ipynb           # Model inference testing
├── config_new.py                         # Enhanced configuration
├── generator_new.py                      # Conversation generator
├── main_new.py                           # Main pipeline script
├── utils_new.py                          # Utility functions
├── schemas.py                            # Data schemas
├── analyze_conversational.py             # Quality analysis tool
└── test_new_pipeline.py                  # Pipeline testing
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
git clone <repository-url>
cd alif-emergency-response
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file:
```bash
GCP_API_KEY="your-gemini-api-key"
```

### 3. Generate Dataset

```bash
# Test the pipeline
python test_new_pipeline.py

# Generate full dataset (500 conversations)
python main_new.py
```

### 4. Analyze Quality

```bash
python analyze_conversational.py
```

## 📊 Dataset Format

The dataset uses a conversational format perfect for fine-tuning:

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

## 🎓 Model Training

The fine-tuning was performed on Kaggle using:
- **Base Model:** Alif-1.0-8B-Instruct
- **Method:** QLoRA (4-bit quantization)
- **Dataset Size:** 5,000 conversations
- **Training Time:** ~5 hours on T4 GPU
- **Final Model:** [hamza-amin/alif-emergency-finetuned](https://huggingface.co/hamza-amin/alif-emergency-finetuned)

### Training Results
- Training Loss: 0.387
- Validation Loss: 0.396
- Quality Score: 99/100

## 💬 Usage

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Load model
tokenizer = AutoTokenizer.from_pretrained("large-traversaal/Alif-1.0-8B-Instruct")
base_model = AutoModelForCausalLM.from_pretrained("large-traversaal/Alif-1.0-8B-Instruct")
model = PeftModel.from_pretrained(base_model, "hamza-amin/alif-emergency-finetuned")

# Chat function
def emergency_chat(prompt):
    text = f"### User:\n{prompt}\n\n### Assistant:\n"
    inputs = tokenizer(text, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=150)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Test
response = emergency_chat("میں کراچی سے بول رہا ہوں۔ یہاں آگ لگی ہے۔")
print(response)
```

## 🔧 Configuration

Key settings in `config_new.py`:
- **TARGET_ROWS:** 500 (adjustable)
- **BATCH_SIZE:** 15 conversations per API call
- **LOCATIONS:** 10 major Pakistani cities with specific areas
- **EMERGENCY_TYPES:** Medical, fire, crime, accidents, natural disasters
- **MESSAGE_TYPES:** 8 different conversation patterns

## 📈 Quality Metrics

- **Language Purity:** 100% (no English contamination)
- **Diversity:** 100% unique conversations
- **Length:** Optimal (8-25 words per message)
- **Emergency Coverage:** All major emergency types
- **Cultural Accuracy:** Pakistani locations and expressions

## 🛠️ Pipeline Features

### Enhanced Generation
- Realistic Pakistani emergency scenarios
- Multiple conversation types (initial calls, follow-ups, status checks)
- Varied emotional states (panic, calm, pain, anger)
- Authentic Urdu expressions and local terminology

### Quality Assurance
- Automatic English detection and filtering
- Duplicate conversation removal
- Length and content validation
- Emergency keyword coverage analysis

### Scalability
- Batch processing with retry logic
- Memory-efficient generation
- Progress tracking and resumption
- Configurable output targets

## 🎯 Use Cases

- **Emergency Call Centers:** Train operators for Urdu-speaking callers
- **Voice Assistants:** Emergency response in Urdu
- **Chatbots:** Automated emergency guidance
- **Training Simulations:** Emergency response training
- **Research:** Urdu NLP and emergency response systems

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `test_new_pipeline.py`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **Traversaal AI** for the Alif base model
- **Google Gemini** for dataset generation
- **Hugging Face** for model hosting and tools
- **Kaggle** for free GPU training resources

## 📞 Contact

For questions or collaboration opportunities, please open an issue or contact the maintainers.

---

*Built with ❤️ for the Pakistani emergency response community*