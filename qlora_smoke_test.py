import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    DataCollatorForLanguageModeling,
    Trainer,
)
from peft import LoraConfig, get_peft_model

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

print("Torch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL, use_fast=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Loading model in 4-bit...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    quantization_config=bnb_config,
    device_map="auto",
)

print("Applying LoRA...")
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Tiny dataset
raw = Dataset.from_list([
    {"text": "Topic: AI in education\nPro: AI improves personalization and feedback.\n"},
    {"text": "Topic: AI in education\nCon: AI increases privacy risks and dependency.\n"},
    {"text": "Topic: Capital punishment\nPro: It may deter some violent crime.\n"},
    {"text": "Topic: Capital punishment\nCon: It risks wrongful execution and bias.\n"},
])

def tokenize(batch):
    out = tokenizer(
        batch["text"],
        truncation=True,
        max_length=256,
        padding="max_length",
    )
    out["labels"] = out["input_ids"].copy()
    return out

print("Tokenizing dataset...")
ds = raw.map(tokenize, batched=True, remove_columns=["text"])

args = TrainingArguments(
    output_dir="./qlora_test_out",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=1,
    max_steps=20,
    logging_steps=1,
    save_steps=20,
    fp16=True,
    report_to="none",
)

collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

print("Training (Transformers Trainer)...")
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=ds,
    data_collator=collator,
)

trainer.train()

print("Saving adapter...")
model.save_pretrained("./qlora_adapter_test")
print("OK: QLoRA smoke test finished.")
