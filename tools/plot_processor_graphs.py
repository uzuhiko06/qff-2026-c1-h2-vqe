import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import matplotlib.pyplot as plt
import networkx as nx
import qff_chem as qff

def plot_processor_graphs():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "figures")
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Load Processor D
    d_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "processors", "processor_D.json")
    with open(d_path) as f:
        proc_d = json.load(f)
    
    processors = [
        ("Processor A (5Q Tree)", qff.PROCESSOR_A["edges"], 5, "processor_A_graph.png"),
        ("Processor B (9Q Planar Mesh)", qff.PROCESSOR_B["edges"], 9, "processor_B_graph.png"),
        (f"Processor D (6Q Chemistry Co-Design)", proc_d["edges"], proc_d["num_qubits"], "processor_D_graph.png"),
    ]
    
    for title, edges, n_qubits, filename in processors:
        G = nx.Graph()
        G.add_nodes_from(range(n_qubits))
        G.add_edges_from([tuple(e) for e in edges])
        
        plt.figure(figsize=(6, 5), dpi=300)
        
        if n_qubits == 5: # Processor A
            pos = {0: (0, 1), 1: (1, 1), 2: (2, 1), 3: (1, 0), 4: (2, 0)}
        elif n_qubits == 6: # Processor D
            # Core K4 in diamond/square: 0: top, 1: left, 2: bottom, 3: right
            # Ancilla: 4: right-middle, 5: outer-right
            pos = {
                0: (1.0, 2.0),
                1: (0.0, 1.0),
                2: (1.0, 0.0),
                3: (2.0, 1.0),
                4: (3.2, 0.5),
                5: (4.4, 0.5)
            }
        else: # Processor B
            pos = nx.spring_layout(G, seed=42)
            
        # Draw nodes
        node_colors = []
        for node in G.nodes():
            if n_qubits == 6 and node in [0, 1, 2, 3]:
                node_colors.append("#2b5c8f") # Active core
            elif n_qubits == 6 and node in [4, 5]:
                node_colors.append("#d95f02") # Diagnostic / ancilla
            else:
                node_colors.append("#1f77b4")
                
        nx.draw_networkx_nodes(G, pos, node_size=800, node_color=node_colors, edgecolors="black", linewidths=1.5)
        nx.draw_networkx_labels(G, pos, font_size=12, font_color="white", font_weight="bold")
        nx.draw_networkx_edges(G, pos, width=2.0, edge_color="#444444")
        
        plt.title(f"{title}\nCoupling Topology ({len(edges)} edges, max degree {max(dict(G.degree()).values())})",
                  fontsize=12, fontweight="bold", pad=12)
        plt.axis("off")
        plt.tight_layout()
        save_path = os.path.join(out_dir, filename)
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
        print(f"Saved: {save_path}")

if __name__ == "__main__":
    plot_processor_graphs()
