This is a ResearchAgent
The work it performs is summarizing data retrieved about a topic of research through web search
This agent uses langraph as framework
The workflow of this agent is as follows:-
1) The entrypoint is a generate query Node which generates short queries for research on the given  User Topic
2) The result from this node moves to SEARCH node which uses Tavily to perform deep web search based on the query
3) The result the moves to CHECK SUFFICIENCY node , which has a conditional edge , if sufficient goes to Summarizing node else goes back to Generate Query node
4) Summarization node does the summarization using "gemini 2.5 flash"
5) Rest all the node use "gemini 3.1 flash lite"

The User site is made Using Streamlit UI and the Database uses id PostgreSQL.

## Setup
1. Clone the repo
2. Create a virtual environment and install dependencies:
   pip install -r requirements.txt
3. Create a .env file with:
   GOOGLE_API_KEY=your_key
   TAVILY_API_KEY=your_key
   DB_PASSWORD=your_postgres_password
4. Set up PostgreSQL and create a database called research_agent
5. Run the app:
   streamlit run display.py
