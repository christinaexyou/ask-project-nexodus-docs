import os
import glob

from langchain.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

from transformers import pipeline 
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from peft import PeftModel, PeftConfig

import streamlit as st


def main():
    # set page title
    st.set_page_config(page_title="Project Nexodus Documentation Retreival", page_icon="📖", layout="wide")
    st.header("📖 Ask Project Nexodus Docs")
    # set description
    st.markdown("""
                Generates answers to your questions about Project Nexodus by leveraging foundation models to perform search and retreival of Nexodus documentation.\n
                
                Feeling stuck? Here are some examples of questions you can ask:
                * How do I run the control plane for Nexodus?
                * How do I monitor the Nexodus stack locally?
                * How can I contribute to Project Nexodus?
                """)
    # set sidebar
    with st.sidebar:
        # create instructions for use 
        st.markdown("""
                    # How to use:\n
                    1. Enter your HuggingFace API token below
                    2. Select your answer generation strategy from the dropdown menu
                    3. Ask a question about Linux networking
                    4. Click on the `Submit` button or optionally, click on the `Feeling Lucky`
                    """)
         # create input box for HF API token                                                                                                  
        API_KEY = st.text_input('Hugging Face API Token 🤗', type='password', 
                                placeholder='Paste your HuggingFace token here (sk-...)', 
                                help="You can get your API token from https://huggingface.co/docs/hub/security-tokens.")
        
        st.markdown("""
                    # About 
                    Talk to Project Nexodus is a web application that answers your questions about Nexodus,
                    with the goal of exploring the capabilities and limitations of Large Language Models (LLMs) for question and 
                    answering tasks. It demonstrates the following strategies for question answering: extractive, abstractive, and 
                    generative. 
                    
                     This project is still in beta and mainly used for research purposes. It is highly unadvised for users to rely on it for Project Nexodus troubleshooting. 
                     Please refer to the [official Nexodus documentation](https://github.com/nexodus-io/nexodus) for help. Proceed at your own risk 💀
                    """)
    if API_KEY:
        strategy = st.selectbox('Q&A Strategy', ['Extractive', 'Abstractive', 'Finetuned with LoRA'])
        question = st.text_input("Enter your question here:")
        col1, col2 = st.columns([1,1])
        with col1:
            generate_answer = st.button("Generate Answer")
        with col2:
            feeling_lucky = st.button("Feeling Lucky")

        if question != "": 
            if strategy and generate_answer:
                answer = get_answer(question, strategy)
                st.write(answer)
            elif feeling_lucky:
                answer = get_answer(question, 'Generative')
                st.write(answer)

def load_db():
    # initalize embedder 
    print('Loading FAISS index...')
    embeddings = HuggingFaceEmbeddings()
    # load FAISS vector database storing Nexodus documentation
    db = FAISS.load_local("models/nexodus_index.faiss", embeddings)
    return db

def load_model():
    llm = "deepset/roberta-base-squad2"
    return llm

def load_model_tokenizer(strategy):
    model_name = "google/flan-t5-base"
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name,load_in_8bit=True, device_map='auto')
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    if strategy == 'Finetuned with LoRA':
        print(f"Loading finetuned {model_name} with LoRA...") 
        model = PeftModel.from_pretrained(model, 'exyou/nexodus-flan-T5')
        print("Model sucessfully loaded")
        
    return model, tokenizer

def provide_context(context):
    context = [f"<P> {m.page_content}" for m in context]
    context = " ".join(context)
    return context

def get_answer(question, strategy):
    if strategy == 'Generative':
        model, tokenizer = load_model_tokenizer(strategy)
        context = ""
        question_context = f"Question: ## {question} ##\n Context: ## {context} ##"
        input_ids = tokenizer(question_context, return_tensors="pt", truncation=True).input_ids.cuda()
        outputs = model.generate(input_ids=input_ids, max_new_tokens=1000, do_sample=True, top_p=1)
        answer = tokenizer.batch_decode(outputs.detach().cpu().numpy(), skip_special_tokens=True)[0]
        return answer
        
    else:
        db = load_db()
        if strategy == 'Finetuned with LoRA':
            model, tokenizer = load_model_tokenizer(strategy)
            # get the top 3 most similar sentences in the docs to the inputted question
            top_3 = db.similarity_search(question, k=3)
            # set as context for the question
            context = provide_context(top_3)
            question_context = f"Question: ## {question} ##\n Context: ## {context} ##"
            input_ids = tokenizer(question_context, return_tensors="pt", truncation=True).input_ids.cuda()
            outputs = model.generate(input_ids=input_ids, max_new_tokens=1000, do_sample=True, top_p=1)
            answer = tokenizer.batch_decode(outputs.detach().cpu().numpy(), skip_special_tokens=True)[0]
            return answer
        
        else: 
            llm = load_model()
            if strategy == 'Extractive':
                output = db.similarity_search(question, k=1)
                answer = output[0].page_content
                return answer

            elif strategy == 'Abstractive':
                top_3 = db.similarity_search(question, k=3)
                context = provide_context(top_3)
                text2text_generator = pipeline(task='question-answering', tokenizer=llm, model=llm)
                output = text2text_generator(question=question, context=context, temperature=1.5, min_length=5, max_length=50)
                answer = output["answer"]
                return answer

    return answer

if __name__ == "__main__":
    main()
        
