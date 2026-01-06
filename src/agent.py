import modal

# 1. Define the environment
image = modal.Image.debian_slim().pip_install("groq")
app = modal.App("drug-discovery-agent")

# 2. Agent Function
@app.function(image=image, secrets=[modal.Secret.from_name("my-groq-secret")])
def propose_modification(current_smiles: str, history: list):
    import os
    import re
    from groq import Groq

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    # Format history
    history_text = "\n".join([f"- Tried: {h['smiles']}, Score: {h['score']}" for h in history])

    prompt = f"""
    ROLE: You are an expert Medicinal Chemist and Cheminformatics Specialist.
    TASK: Optimize the molecule below to lower LogP (improve water solubility).    
    
    Current Molecule: {current_smiles}

    HISTORY OF FAILURES (Do not repeat these):
    {history_text}
    
    CONSTRAINTS & RULES:
    1. VALIDITY: The output must be a chemically valid SMILES string. Check valency (e.g., Carbon has max 4 bonds).
    2. STRATEGY: Make a SINGLE modification. Preferred actions: 
       - Add a polar group (OH, NH2, COOH).
       - Perform a bioisosteric replacement (e.g., C -> N in a ring).
    3. SIMPLICITY: Do not fragment the molecule. Keep the core scaffold intact.
    
    OUTPUT FORMAT:
    Return ONLY the SMILES string. Do not include "Here is the molecule", do not include reasoning, and do not use markdown code blocks (```).
    Just the string."""

    # API call to Groq Llama-3.3
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Output only SMILES."},
            {"role": "user", "content": prompt},
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.4, 
    )

    # Response cleaning  (It contains metadata like token usage, headers, and a list of possible answers.)
    raw_response = chat_completion.choices[0].message.content.strip()

    # --- THE REGEX FIX ---
    smiles_pattern = r"([BCNOPSFIbcnopsfilr0-9\(\)\[\]=\#\-\+\.\\\/@%]+)"
    matches = re.findall(smiles_pattern, raw_response)
    
    if matches:
        clean_smiles = max(matches, key=len)
    else:
        clean_smiles = raw_response # Fallback
        
    return clean_smiles


#-------------------------------------------------------------------------
# 3. DEV/TEST ENTRYPOINT 
#  Run this locally via `modal run Agent.py` to test the AI logic 
#  without spinning up the full Temporal orchestration engine.
#  NOTE: This uses MOCK scoring, not real physics.
#-------------------------------------------------------------------------

@app.local_entrypoint()
def main():
    # Starting state
    current_smiles = "c1ccccc1" # Benzene (Very non-polar)
    history = []
    
    print(f"Starting Drug Discovery Agent...")
    print(f"Goal: Optimize {current_smiles} (Benzene) to be water soluble.")
    print("-" * 50)

    for step in range(1, 4): # Run 3 iterations
        print(f"\n Iteration {step}: Asking Agent...")
        
        # Call the remote function
        new_smiles = propose_modification.remote(current_smiles, history)
        
        # Mock Scoring (In real life, this calls docking.py)
        # We'll pretend the agent is getting better scores
        mock_score = 3.0 - (step * 0.8) 
        
        print(f"   Agent proposed: {new_smiles}")
        print(f"   Mock LogP Score: {mock_score:.2f}")

        # Update state
        history.append({"smiles": new_smiles, "score": mock_score})
        current_smiles = new_smiles
        
        if mock_score < 1.0:
            print("\n SUCCESS: Molecule is soluble!")
            break
            
    print("\n Discovery loop finished.")