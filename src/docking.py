import modal
import subprocess
import os

# 1. Define the Cloud Environment
# We start with a slim Debian Linux image and install our bio-tools
# NOTE: We install 'autodock-vina' and 'meeko' for future 3D docking capabilities.
# For this MVP, we are using RDKit's LogP as a lightweight proxy for binding affinity.

image = modal.Image.debian_slim()\
    .apt_install("autodock-vina", "openbabel")\
    .pip_install("rdkit", "meeko", "numpy")

app = modal.App("drug-discovery-muscle")

# 2. Define the Helper Function (Runs INSIDE the container)
@app.function(image=image)
def verify_tools():
    """
    Sanity check: Runs version commands to ensure tools are installed correctly.
    """
    results = {}
    
    # Check Vina
    try:
        vina_out = subprocess.check_output(["vina", "--version"], text=True)
        results["vina"] = vina_out.strip()
    except Exception as e:
        results["vina"] = f"FAILED: {e}"

    # Check OpenBabel
    try:
        ob_out = subprocess.check_output(["obabel", "-V"], text=True)
        results["openbabel"] = ob_out.split("\n")[0]
    except Exception as e:
        results["openbabel"] = f"FAILED: {e}"

    # Check RDKit
    try:
        
        import rdkit
        results["rdkit"] = rdkit.__version__
    except ImportError:
        results["rdkit"] = "FAILED: Not installed"

    return results

# 3. Define the Real Docking Function
@app.function(image=image)
def score_molecule(smiles: str):
    from rdkit import Chem
    from rdkit.Chem import Crippen
    
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return {"error": "Invalid SMILES", "score": 999.0}

    # Calculate LogP (The measure of lipophilicity/solubility)
    # Lower LogP = More water soluble
    logp = Crippen.MolLogP(mol)
    
    return {
        "smiles": smiles, 
        "score": round(logp, 2), 
        "status": "Success"
    }