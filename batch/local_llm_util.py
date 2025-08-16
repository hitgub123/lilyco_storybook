import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
from transformers import pipeline

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

device = "cuda" if torch.cuda.is_available() else "cpu"


# google/gemma-2b-it
# google/gemma-3-270m-it
class Local_llm:
    def __init__(self, llm_name="google/gemma-3-270m-it"):
        self.llm_name = llm_name
        self.pipe = pipeline("text-generation", model=self.llm_name)
        # llm_name = "google/gemma-3-1b-it"
        # self.tokenizer = AutoTokenizer.from_pretrained(llm_name)
        # self.model = AutoModelForCausalLM.from_pretrained(llm_name)
        # self.model.eval()

    def get_model(self):
        return self.model

    def get_tokenizer(self):
        return self.tokenizer


    def invoke(self, messages):
        
        # messages = [
        #     {"role": "system", "content": "用中文回答我的问题。"},{"role": "user", "content": query},
        # ]
        response=self.pipe(messages)
        print('response',response)
        return response

    def invoke_query(self, query):
        
        messages = [
            {"role": "system", "content": "用中文回答我的问题。"},{"role": "user", "content": query},
        ]
        response=self.pipe(messages)

        print('response',response)
        return response

    def invoke_custom(self, query):
        messages = [
            # {"role": "system", "content": "你是智能AI助手，用中文回答我的问题。"},
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
            max_new_tokens=1024,
            temperature=0.5,
            top_p=0.9,
            do_sample=True,
        )
        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[-1] :], skip_special_tokens=True
        )
        print('response',response)
        return response

if __name__ == "__main__":
    # llm=Local_llm()
    llm=Local_llm(llm_name="google/gemma-3-1b-it")
    # res=llm.invoke("法国首都是是哪里")
    res=llm.invoke("where is japan")
    print(res)
