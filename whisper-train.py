import os
import torch
from datasets import load_dataset, Audio
from transformers import (
    WhisperProcessor,
    WhisperForConditionalGeneration,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)


print("Loading Urdu TTS dataset...")
dataset = load_dataset("muhammadsaadgondal/urdu-tts")

dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))

print("Dataset preview:")
print(dataset)

model_name = "openai/whisper-small"
print(f"Loading Whisper model ({model_name})...")
processor = WhisperProcessor.from_pretrained(model_name)
model = WhisperForConditionalGeneration.from_pretrained(model_name)

def prepare_dataset(batch):

    audio = batch["audio"]["array"]
    batch["input_features"] = processor(audio, sampling_rate=16000).input_features[0]


    batch["labels"] = processor.tokenizer(batch["text"]).input_ids
    return batch


print("Preprocessing dataset...")
dataset = dataset.map(prepare_dataset, remove_columns=["audio", "text", "filename"])
print("Preprocessing complete.")

def data_collator(batch):
    input_features = torch.tensor(
        [f["input_features"] for f in batch], dtype=torch.float32
    )

    max_label_len = max(len(f["labels"]) for f in batch)
    labels = torch.full(
        (len(batch), max_label_len), processor.tokenizer.pad_token_id, dtype=torch.long
    )
    for i, f in enumerate(batch):
        labels[i, : len(f["labels"])] = torch.tensor(f["labels"], dtype=torch.long)

    return {"input_features": input_features, "labels": labels}

output_dir = "./whisper-urdu-model"
training_args = Seq2SeqTrainingArguments(
    output_dir=output_dir,
    per_device_train_batch_size=2,  
    num_train_epochs=1,
    logging_steps=10,
    save_steps=50,
    save_total_limit=2,
    predict_with_generate=True,
    fp16=False, 
)


trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    data_collator=data_collator, 
    tokenizer=None,  
)


print("Starting training...")
trainer.train()

print(f"Saving model and processor to {output_dir}...")
model.save_pretrained(output_dir)
processor.save_pretrained(output_dir)
print("Training complete. Model saved.")
