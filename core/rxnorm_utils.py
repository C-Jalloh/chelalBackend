import requests

RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"

def get_rxcui_for_drug(drug_name):
    """Get RxCUI (RxNorm Concept Unique Identifier) for a drug name."""
    resp = requests.get(f"{RXNORM_BASE_URL}/rxcui.json", params={"name": drug_name})
    if resp.status_code == 200:
        data = resp.json()
        return data.get("idGroup", {}).get("rxnormId", [None])[0]
    return None

def check_drug_interactions(rxcui_list):
    """Check for drug-drug interactions given a list of RxCUIs."""
    if not rxcui_list:
        return []
    rxcuis = ",".join(rxcui_list)
    resp = requests.get(f"{RXNORM_BASE_URL}/interaction/list.json", params={"rxcuis": rxcuis})
    if resp.status_code == 200:
        data = resp.json()
        interactions = data.get("fullInteractionTypeGroup", [])
        return interactions
    return []
