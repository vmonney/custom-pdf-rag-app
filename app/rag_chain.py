"""Chain to answer questions using the RAG model."""

import os
from operator import itemgetter
from typing import TypedDict

from dotenv import load_dotenv
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_community.chat_message_histories.sql import SQLChatMessageHistory
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.messages.utils import get_buffer_string
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.runnables import RunnableParallel
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables.passthrough import RunnablePassthrough
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


multiquery = MultiQueryRetriever.from_llm(
    retriever=vector_store.as_retriever(),
    llm=llm,
)

no_history = (
    RunnableParallel(
        context=(itemgetter("question") | multiquery),
        question=(itemgetter("question")),
    )
    | RunnableParallel(anwser=(ANSWER_PROMPT | llm), docs=itemgetter("context"))
).with_types(input_type=RagInput)

history_retriever = lambda session_id: SQLChatMessageHistory(
    connection_string=os.getenv("POSTGRES_MEMORY_URL"),
    session_id=session_id,
)

_template = """Given the following conversation and a follow up question,
rephrase the follow up question to be a standalone question, in its original
language.

Chat History:
{chat_history}
Follow up input: {question}
standalone question:"""

condense_question_prompt = PromptTemplate.from_template(_template)

standalone_question = RunnableParallel(
    question=RunnableParallel(
        question=RunnablePassthrough(),
        chat_history=lambda x: get_buffer_string(x["chat_history"]),
    )
    | condense_question_prompt
    | llm
    | StrOutputParser(),
)

final_chain = RunnableWithMessageHistory(
    runnable=standalone_question | no_history,
    input_messages_key="question",
    history_messages_key="chat_history",
    output_messages_key="anwser",
    get_session_history=history_retriever,
)
