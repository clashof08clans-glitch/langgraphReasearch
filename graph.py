from typing import TypedDict
from langchain_tavily import TavilySearch
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

import psycopg2

load_dotenv()

llm_fast = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite" , temperature =0) 
llm_quality = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

search_tool = TavilySearch(max_results = 2)

class ReseachState(TypedDict):
    topic: str
    query: list
    results: list
    sufficient: str
    answer : str
    itr: int


def get_connection():
     return psycopg2.connect(
          dbname = "research_agent",
          user = "postgres",
          password = os.getenv("DB_PASSWORD"),
          host = "localhost",
          port = "5432"
     )

def setup_db():
     conn = get_connection()
     cursor = conn.cursor()
     cursor.execute("""
          CREATE TABLE IF NOT EXISTS cache(
          topic TEXT PRIMARY KEY,
          answer TEXT
          )
     """)
     conn.commit()
     conn.close()


def extract_text(content):
    if isinstance(content, list):
        return " ".join([part["text"] for part in content if isinstance(part, dict) and "text" in part])
    return str(content)


def generate_query(state:ReseachState):
    
        prompt = f"""You are a helpful agent. You generate query for the given topic.
                    Strictly generate query and nothing else. Refine queries based on the information/context you are provided.
                    Query should not be of more than 10 words
                    
                    Topic:{state["topic"]}
                    Already found context: {str(state["results"])[:500]}
                    """
        response = llm_fast.invoke(prompt)
        content = response.content

        query = extract_text(content)
    
        query = query.strip()
        return {'query':query,'itr':state["itr"]+1}


def search(state:ReseachState):
      response = search_tool.invoke(state["query"])
      clean_results = [r["content"] for r in response["results"]]
      return {"results":clean_results}


def check_sufficiency(state:ReseachState):
    prompt = f"""Your are a helpful agent, your task is to check whether the context
    provided to you about the topic is enough or not , check the sufficiency in a general context.
    If you think it is sufficient return True else return False. Strictly return True or False.

    Context:{state['results']}
    """

    response = llm_fast.invoke(prompt)
    content = response.content
    
    sufficient = extract_text(content)
    
    sufficient = sufficient.strip()
    return {'sufficient':sufficient}

def route(state:ReseachState):
     if state["sufficient"]=="True" or state["itr"]>=5:
          return "end"
     else:

          return "continue"

def synthesize(state:ReseachState):
     prompt = f"""You are a helpful agent. You summarize the content given to you
     by in terms of introduction , key points , and final conclusion.  
     
     content:{state['results']}
     """
     response= llm_quality.invoke(prompt)
     answer = extract_text(response.content).strip()
     return {'answer':answer}

def load_cache(topic):
     try:
         conn = get_connection()
         cursor = conn.cursor()
         cursor.execute("SELECT answer FROM cache WHERE topic = %s",(topic,))
         result = cursor.fetchone()
         conn.close()
         return result[0] if result else ""
     except Exception as e:
          print(f"Cache load error: {e}")
          return ""

     
def save_cache(topic,answer):
     try:
          conn = get_connection()
          cursor = conn.cursor()
          cursor.execute("""
               INSERT INTO cache (topic,answer)
               VALUES (%s,%s)
               ON CONFLICT (topic) DO UPDATE SET answer = EXCLUDED.answer
               """,(topic,answer)
          )
          conn.commit()
          conn.close()
     except Exception as e:
        print(f"Cache save error: {e}")

def get_all_topics():
     try:
          conn = get_connection()
          cursor = conn.cursor()
          cursor.execute("SELECT topic FROM cache ")
          topics = [row[0] for row in cursor.fetchall()]
          conn.close()
          return topics
     except Exception as e:
          print(f"Error:{e}")
          return []

setup_db()

graph = StateGraph(ReseachState)
graph.add_node("generate_query",generate_query)
graph.add_node("search",search)
graph.add_node("check_sufficiency",check_sufficiency)
graph.add_node("synthesize",synthesize)

graph.set_entry_point("generate_query")
graph.add_edge("generate_query","search")
graph.add_edge("search","check_sufficiency")
graph.add_conditional_edges(
     "check_sufficiency",
      route,
      {
           "end":"synthesize",
           "continue": "generate_query"
      }

)
graph.add_edge("synthesize",END)

app = graph.compile()

# result = app.invoke({"topic":"akbar","query":"","results":[],"sufficient":"","answer":"","itr":0})
# print(result["answer"])

if __name__ == "__main__":
    topic = "akbar"
    
    cached = load_cache(topic)
    if cached:
        print(cached)
    else:
        result = app.invoke({"topic": topic, "query": "", "results": [], "sufficient": "", "answer": "", "itr": 0})
        save_cache( topic, result["answer"])
        print(result["answer"])