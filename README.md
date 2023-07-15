# Ask Project Nexodus Docs
The goal of this project is to explore different LLM QA strategies for Project Nexodus documentation to better understand their capabilities and limitations. This repository documents my work over the course of my Summer 2023 Red Hat internship where I experimented with extractive, abstractive, and generative question answering strategies, as well as fine-tuning a flan-t5-base model with LoRA (Low Rank Approximation). Additionally, I developed a web application via Streamlit to automate the process of having a user input a question and the selected stategy output an answer. 

## Repository Structure
```
├── data  
|    ├── docs   <- Project Nexodus documentation
│    ├── results   <- Intermediate data that has been transformed.
│    └── Network-Training-QAs.md   <- ChatGPT generate question and answer pairs
|
├── models
|     ├── nexodus-flan-t5   <- Fine-tuned flan-t5-base model using LoRA 
|     └── nexodus_index.faiss <- FAISS vector index which stores embeddings of docs
|
├── notebooks 
|      ├── 00-start_here.ipynb   <- Demonstrates extractive, abstrative, and generative QA
|      ├── 01-finetuning_llm.ipynb   <- Fine-tuning flan-t5-base model using LoRA on QA pairs
|      ├── 02-strategy_evaluation.ipynb   <- Evaluates performance of the different strategies against each other
|      └── requirements.txt
|      
├── streamlit 
|      ├── app.py   <- Web application source code
|      └── requirements.txt
|
└── README.md <-   You are here
```

## Application Preview


https://github.com/christinaexyou/ask_project_nexodus_docs/assets/77992688/9a8aa0a0-0ff2-44f4-a239-5bb325815e9c



## Contact Info 
Please contact Christina Xu (cjxu@bu.edu) for any questions/concerns/feedback.
