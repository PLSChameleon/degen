import requests

def query_subgraph(url, pair_id):
    query = """
    {
        pairs(where: { id: "%s" }) {
            id
            token0 {
                id
            }
            token1 {
                id
            }
        }
    }
    """ % pair_id
    
    response = requests.post(url, json={'query': query})
    
    if response.status_code == 200:
        data = response.json()
        if 'data' in data:
            return data['data']['pairs']
        else:
            print(f"Error in response: {data}")
            return None
    else:
        raise Exception(f"Query failed with status code {response.status_code}")

def check_pair_in_subgraphs(pair_id):
    v1_url = "https://graph.pulsechain.com/subgraphs/name/pulsechain/pulsex-v1"
    v2_url = "https://graph.pulsechain.com/subgraphs/name/pulsechain/pulsex-v2"
    
    v1_result = query_subgraph(v1_url, pair_id)
    v2_result = query_subgraph(v2_url, pair_id)
    
    print("PulseX V1 Results:")
    if v1_result:
        for pair in v1_result:
            print(f"Pair ID: {pair['id']}, Token0 ID: {pair['token0']['id']}, Token1 ID: {pair['token1']['id']}")
    else:
        print("Pair not found in PulseX V1 subgraph.")
    
    print("\nPulseX V2 Results:")
    if v2_result:
        for pair in v2_result:
            print(f"Pair ID: {pair['id']}, Token0 ID: {pair['token0']['id']}, Token1 ID: {pair['token1']['id']}")
    else:
        print("Pair not found in PulseX V2 subgraph.")

def to_lowercase(pair_id):
    return pair_id.lower()

if __name__ == "__main__":
    pair_id = "0xd7E98780C10c9c716A87A7f76E76cB1d49556dA1"
    pair_id = to_lowercase(pair_id)
    check_pair_in_subgraphs(pair_id)
