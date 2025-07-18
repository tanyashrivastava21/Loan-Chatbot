# -*- coding: utf-8 -*-
"""loanbot_app

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1XGG7c2RfYqj7nmAJJXgLZq0Oz2mmMo_M
"""

import streamlit as st
import pandas as pd
import faiss
import numpy as np
import os
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Load Gemini API Key from secrets
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

# Load and clean the dataset
@st.cache_resource
def load_data():
    df = pd.read_csv("Training Dataset.csv")
    df.columns = df.columns.str.strip().str.replace(" ", "_")
    df.fillna("Unknown", inplace=True)
    return df

df = load_data()

# Convert rows into descriptive sentences
@st.cache_resource
def convert_rows(df):
    def row_to_text(row):
        return (
            f"Applicant ID {row['Loan_ID']} is a {row['Gender']} {row['Education']} applicant, "
            f"married: {row['Married']}, self-employed: {row['Self_Employed']}, "
            f"income: {row['ApplicantIncome']}, co-applicant income: {row['CoapplicantIncome']}, "
            f"loan amount: {row['LoanAmount']} for {row['Loan_Amount_Term']} months, "
            f"credit history: {row['Credit_History']}, property area: {row['Property_Area']}, "
            f"loan approved: {row['Loan_Status']}."
        )
    return df.apply(row_to_text, axis=1).tolist()

texts = convert_rows(df)

# Embedding model and FAISS index
@st.cache_resource
def build_index(texts):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    return model, index, embeddings

embedding_model, faiss_index, _ = build_index(texts)

# Ask Gemini
def ask_gemini(question, top_k=5):
    q_embedding = embedding_model.encode([question])
    D, I = faiss_index.search(np.array(q_embedding), k=top_k)
    context = "\n".join([texts[i] for i in I[0]])
    prompt = f"""You are an assistant for analyzing loan approval data. Use the context below to answer the question.

Context:
{context}

Question: {question}
Answer:"""
    response = model.generate_content(prompt)
    return response.text

# Streamlit UI
st.set_page_config(page_title="LoanBot AI", layout="centered")
st.title("🤖 LoanBot AI – Chat With Loan Approval Data")

question = st.text_input("Ask a question about the dataset:")

if question:
    with st.spinner("Thinking..."):
        answer = ask_gemini(question)
    st.markdown("### 💡 Gemini's Answer:")
    st.write(answer)
