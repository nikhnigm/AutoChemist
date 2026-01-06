import asyncio
from datetime import timedelta
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker

# --- ACTIVITY 1: THE BRAIN ---
@activity.defn
async def call_ai_agent(current_smiles: str, history: list) -> str: # <--- FIXED: Now accepts 'list' to match workflow args
    import modal
    f = modal.Function.from_name("drug-discovery-agent", "propose_modification")
    # This calls Llama-3 on Groq
    return f.remote(current_smiles, history)

# --- ACTIVITY 2: THE MUSCLE ---
@activity.defn
async def call_modal_docking(smiles: str) -> dict: # Correctly set to return dict
    import modal
    f = modal.Function.from_name("drug-discovery-muscle", "score_molecule")
    return f.remote(smiles)

# --- THE ORCHESTRATOR ---
@workflow.defn
class DiscoveryWorkflow:
    @workflow.run
    async def run(self, start_smiles: str):
        current_smiles = start_smiles
        history = []
        
        print(f"Starting Optimization Loop for: {start_smiles}")

        for i in range(1, 6): # Max 5 iterations
            print(f"\n--- Iteration {i} ---")
            
            # Step 1: Lab Test (Muscle)
            lab_result = await workflow.execute_activity(
                call_modal_docking,
                current_smiles,
                start_to_close_timeout=timedelta(minutes=1)
            )
            
            score = lab_result.get("score", 999)
            print(f"Measured LogP: {score}")
            
            # Check for Success
            if score < 1.0:
                print("SUCCESS! Solubility Goal Met.")
                return {"status": "Solved", "molecule": current_smiles, "final_score": score, "iterations": i}

            # Record History
            history.append({"smiles": current_smiles, "score": score})

            # Step 2: Ask Agent for Redesign (Brain)
            print("Score too high. Asking Agent to redesign...")
            new_smiles = await workflow.execute_activity(
                call_ai_agent,
                args=[current_smiles, history], # Passes [str, list]
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            print(f"Agent Suggested: {new_smiles}")
            current_smiles = new_smiles # Update for next loop

        return {"status": "Failed to converge", "history": history}

# ... Main block ...
async def main():
    client = await Client.connect("localhost:7233")
    async with Worker(
        client,
        task_queue="agent-queue",
        workflows=[DiscoveryWorkflow],
        activities=[call_ai_agent, call_modal_docking],
    ):
        result = await client.execute_workflow(
            DiscoveryWorkflow.run,
            "c1ccccc1", # Benzene
            id="drug-loop-003", # <--- UPDATED ID
            task_queue="agent-queue",
        )
        print(f"\nWorkflow Result: {result}\n")

if __name__ == "__main__":
    asyncio.run(main())