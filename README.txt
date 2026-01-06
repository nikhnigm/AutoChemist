# AutoChemist: Fault-Tolerant Drug Discovery 

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Temporal](https://img.shields.io/badge/Orchestration-Temporal.io-black)](https://temporal.io/)
[![Modal](https://img.shields.io/badge/Compute-Serverless%20Modal-green)](https://modal.com/)
[![Groq](https://img.shields.io/badge/AI-Groq%20LPU-orange)](https://groq.com/)

A resilient, cloud-native Agentic Workflow that automates the **Design-Make-Test cycle** of computational drug discovery.

---

## Project Overview

This project focuses on making AI agents robust enough for production environments by treating them as **distributed systems**. While many current agent frameworks can be brittle, often crashing completely if a single API times out, this system is designed for resilience.

It uses the **Distributed Saga Pattern** to manage state persistence automatically. This means the workflow is durable: even if a crash occurs in the middle of a long simulation, the system is built to recover and resume from the last successful step, rather than losing progress and starting over.

### The Problem
* **Fragility:** Long-running scientific scripts crash easily (network errors, OOM).
* **Cost:** Keeping GPU clusters running for intermittent inference is expensive.
* **Latency:** Iterative design loops are too slow with standard CPUs.

### The Solution
* **Orchestrator (The Brain):** Temporal.io manages state, retries, and timeouts.
* **Reasoning (The Voice):** Groq (Llama-3) provides sub-second chemical optimization.
* **Simulation (The Muscle):** Modal runs serverless containers with heavy bioinformatics tools (RDKit, AutoDock Vina).

---

## Architecture

The system is decoupled into three independent microservices:

```mermaid
graph TD
    A[Local Machine] -->|Starts Workflow| B(Temporal Server)
    B -->|Schedule Task| C{Orchestration Worker}
    
    C -->|Activity: Design| D[Agent.py / Modal Cloud]
    D -->|Inference| E[Groq LPU / Llama-3]
    E -->|SMILES String| C
    
    C -->|Activity: Test| F[Docking.py / Modal Cloud]
    F -->|Calculation| G[RDKit / AutoDock Container]
    G -->|LogP Score| C
    
    C -->|Decision| H{Goal Met?}
    H -->|No| C
    H -->|Yes| I[Success Result]
```


## Project Structure
```
.
├── src/
│   ├── workflow.py           # The Temporal Orchestrator (State Machine)
│   ├── agent.py              # The AI Chemist (Groq + Llama-3)
│   ├── docking.py            # The Physics Engine (RDKit container)
│   └── infrastructure_test.py # Smoke test for cloud connectivity
├── requirements.txt          # Project dependencies
├── .gitignore                # Git configuration
└── README.md                 # Documentation
```

## Installation & Setup

### 1. Clone & Install

```
git clone [https://github.com/nikhnigm/autochemist.git](https://github.com/nikhnigm/autochemist.git)
cd autochemist

# Create virtual environment
python -m venv venv

# For Mac/Linux
source venv/bin/activate  

# For Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

You need a Modal account and a Groq API key.
 ```
 # Authenticate with Modal
modal setup

# Set your Groq API key in Modal's encrypted storage
modal secret create my-groq-secret GROQ_API_KEY=gsk_your_key_here...
```

### 3. Start the Orchestration Engine
This project requires a local Temporal server to manage state.

```
# Mac (Homebrew)
brew install temporal
temporal server start-dev

# Linux / Windows (curl)
curl -sSf [https://temporal.download/cli.sh](https://temporal.download/cli.sh) | sh
temporal server start-dev
```

Keep this terminal running.

## How to Run

### Phase 1: Deploy Cloud Functions
Upload the "Brain" and "Muscle" code to the serverless cloud.

```
modal deploy agent.py
modal deploy docking.py
```

### Phase 2: Run the Workflow
Execute the orchestrator from your local machine.
```
python workflow.py
```

Open the Temporal UI at http://localhost:8233 to visualize the workflow in real-time, inspect history, and simulate crashes.

##  Technical Highlights

| Component | Technology | Why? |
| :--- | :--- | :--- |
| **Fault Tolerance** | **Temporal** | Retries failed API calls automatically and persists variable state across system reboots, ensuring long-running workflows never restart from zero. |
| **Environment** | **Modal (Docker)** | Implements "Infrastructure as Code" by defining complex bio-dependencies (`openbabel`, `meeko`) directly in Python, eliminating manual container setup. |
| **Inference** | **Groq LPU** | Ultra-low latency inference enables tight, rapid iterative feedback loops that would be too slow on standard GPU hardware. |
| **Safety** | **Regex & RDKit** | Implements "Cheminformatics Guardrails" to parse AI output and mathematically verify that generated SMILES strings represent valid molecular graphs. |

