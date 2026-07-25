from groq import Groq 
import os 
from dotenv import load_dotenv
from tavily import TavilyClient
import json
load_dotenv()



groq_client = Groq(api_key=os.getenv("GROQ_API"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_KEY"))

def get_findings_text(findings, limit=200):
    return "\n\n".join([r["content"] for r in findings])[:limit]

def save_cache(topic, value):
    try:
        with open("cache.json", "r") as file:
            current_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        current_data = {}
    
    current_data[topic] = value
    
    with open("cache.json", "w") as file:
        json.dump(current_data, file, indent=4)

def load_cache(topic):
    try:
        with open("cache.json", "r") as file:
            data = json.load(file)
        if topic in data:
            return data.get(topic)
        else:
            return ""
    except (FileNotFoundError, json.JSONDecodeError):
        return ""

def search_web(query):
    try:
        query = query[:400]
        response = tavily_client.search(query)
        return response["results"]
    except Exception as e:
        print(f"Tavily Error: {e}")
        return []
    

def research(topic):
    findings = []
    t = "a"
    itr = 0
    while t != "True" and itr < 5:
        try:
            prompt = f"""You are a helpful searching agent, you will create a suitable query 
            for the given topic so that it is easy to gather information related to it.
            Generate a short search query of maximum 10 words. Return only the query, nothing else.
            You will strictly follow the topic, and refine the search quality based on the findings 
            you already have.

            Context: {topic}
            
            Findings: {get_findings_text(findings)}
            """
            query = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You generate query strictly based on the context provided"},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0,
            )
            query = query.choices[0].message.content.strip()
            findings.extend(search_web(query))
        except Exception as e:
            print(f"Query generation Error: {e}")
            break

        try:
            findings_text = get_findings_text(findings)
            prmpt = f"""You are a helpful checking agent, you will take the content given to you
            and check whether it is sufficient in the context provided. Return True if sufficient, else False.
            Be accurate in your evaluations.

            Context: {topic}
            Content: {findings_text}
            """
            t = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You have to strictly return True or False only"},
                    {"role": "user", "content": prmpt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0,
            )
            t = t.choices[0].message.content.strip()
            # print(f"Iteration {itr+1}: Sufficient? {t}")
        except Exception as e:
            print(f"Sufficiency check Error: {e}")
            break

        itr += 1

    return findings


def synthesize(topic, findings):
    try:
        context = get_findings_text(findings, limit=3000)
        prompt = f"""You are a helpful assistant, you have to summarize the content given to you
        in the context of the topic provided. Include an introduction, key findings, and conclusion.

        Topic: {topic}
        Context: {context}
        """
        answer = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You summarize the content as stated"},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0,
        )
        return answer.choices[0].message.content.strip()
    except Exception as e:
        print(f"Synthesis Error: {e}")
        return "Something went wrong during synthesis, please try again."


# if __name__ == "__main__":
#     cached = load_cache(topic)
#     if cached:
#         print(cached)
#     else:
#         findings = research(topic)
#         answer = synthesize(topic, findings)
#         save_cache(topic, answer)
#         print(answer)







