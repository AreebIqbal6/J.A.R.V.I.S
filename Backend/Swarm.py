import threading
import time
from groq import Groq
from dotenv import dotenv_values
import os

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

def run_agent(agent_role, task, results_dict):
    """Runs a single agent thread using Groq API."""
    try:
        client = Groq(api_key=GroqAPIKey)
        
        system_prompt = f"You are an expert AI agent with the role: {agent_role}. Complete the following task concisely and professionally."
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task}
            ],
            temperature=0.4,
            max_tokens=1000
        )
        
        results_dict[agent_role] = completion.choices[0].message.content
        print(f">> [HOUSE PARTY]: Agent '{agent_role}' completed its task.")
        
    except Exception as e:
        results_dict[agent_role] = f"Error running agent: {str(e)}"
        print(f"!! [HOUSE PARTY ERROR]: {agent_role} failed - {str(e)}")

def InitiateHousePartyProtocol(goal: str):
    """
    Spawns multiple parallel LLM threads to accomplish sub-tasks simultaneously.
    """
    print(f"\n>> [HOUSE PARTY PROTOCOL]: Initiated for goal: {goal}")
    print(">> [HOUSE PARTY PROTOCOL]: Spawning sub-agents...")
    
    # 1. Ask the LLM to divide the task into 3 distinct roles/prompts
    try:
        client = Groq(api_key=GroqAPIKey)
        breakdown_prompt = f"Divide this master goal into 3 distinct sub-tasks for a Researcher, Coder, and Designer agent. Output format:\nResearcher: <task>\nCoder: <task>\nDesigner: <task>\n\nGoal: {goal}"
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": breakdown_prompt}],
            temperature=0.2,
            max_tokens=300
        )
        breakdown = completion.choices[0].message.content
        
        # Naive parsing
        tasks = {}
        for line in breakdown.split('\n'):
            if ':' in line:
                role, task = line.split(':', 1)
                tasks[role.strip()] = task.strip()
                
        if not tasks:
            tasks = {
                "Researcher": "Research the feasibility and background.",
                "Coder": "Write the core logic and scripts.",
                "Designer": "Format the final output."
            }
            
    except Exception as e:
        return f"Failed to initialize swarm: {str(e)}"

    # 2. Spawn Threads
    results = {}
    threads = []
    
    for role, task in tasks.items():
        print(f">> [HOUSE PARTY]: Booting {role} agent...")
        t = threading.Thread(target=run_agent, args=(role, task, results))
        threads.append(t)
        t.start()
        
    # Wait for all to finish
    for t in threads:
        t.join()
        
    print(">> [HOUSE PARTY PROTOCOL]: All agents have merged their work.")
    
    # 3. Compile Report
    final_report = f"--- HOUSE PARTY PROTOCOL REPORT ---\nMaster Goal: {goal}\n\n"
    for role, content in results.items():
        final_report += f"### {role}'s Output\n{content}\n\n"
        
    # Save to desktop (simulating merging into a folder/file)
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    report_path = os.path.join(desktop, "HouseParty_Report.md")
    
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(final_report)
        return f"House Party Protocol complete. All parallel agents have finished their tasks. The compiled report has been saved to your Desktop at {report_path}."
    except Exception as e:
        return f"House Party Protocol complete, but failed to save to desktop: {str(e)}\n\nReport Preview:\n{final_report[:500]}..."
