"""Chain to answer questions using the RAG model."""

import os
from operator import itemgetter
from typing import TypedDict

from dotenv import load_dotenv
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from config import PG_COLLECTION_NAME

load_dotenv()

vector_store = PGVector(
    collection_name=PG_COLLECTION_NAME,
    connection_string=os.getenv("POSTGRES_URL"),
    embedding_function=OpenAIEmbeddings(),
)

template = """
Répondez en vous basant sur le contexte suivant :
{context}

Question: {question}
"""

ANSWER_PROMPT = ChatPromptTemplate.from_template(template)

llm = ChatOpenAI(temperature=0, model="gpt-4o-2024-05-13", streaming=True)


class RagInput(TypedDict):
    """Input type for the RAG chain."""

    question: str


final_chain = (
    RunnableParallel(
        context=(itemgetter("question") | vector_store.as_retriever()),
        question=(itemgetter("question")),
    )
    | RunnableParallel(anwser=(ANSWER_PROMPT | llm), docs=itemgetter("context"))
).with_types(input_type=RagInput)
