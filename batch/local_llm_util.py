import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

device = "cuda" if torch.cuda.is_available() else "cpu"



class Local_llm:
    def __init__(self, llm_name="google/gemma-3-1b-it"):
        self.llm_name = llm_name
        # llm_name = "meta-llama/Llama-3.2-1B-Instruct"
        # llm_name = "google/gemma-3-1b-it"
        self.tokenizer = AutoTokenizer.from_pretrained(llm_name)
        self.model = AutoModelForCausalLM.from_pretrained(llm_name)
        self.model.eval()

    def get_model(self):
        return self.model

    def get_tokenizer(self):
        return self.tokenizer

    def invoke(self, query):
        messages = [
            # {"role": "system", "content": "You are a factual AI assistant. Provide direct, concise answers to questions without additional commentary or questions."},
            {"role": "user", "content": query},
        ]
        inputs = self.tokenizer.apply_chat_template(
            messages,
            # load_in_4bit=True,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=128,
            temperature=0.5,
            top_p=0.9,
            do_sample=True,
        )
        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[-1] :], skip_special_tokens=True
        )
        print('response',response)
        return response
