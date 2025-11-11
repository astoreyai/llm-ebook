#!/usr/bin/env python3
"""
Generate SVG diagrams for the LLM Prompt Engineering book.
Creates visual representations of key concepts.
"""

def create_rag_pipeline_svg():
    """Generate RAG pipeline architecture diagram."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400">
  <!-- Title -->
  <text x="400" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="#333">
    RAG Pipeline Architecture
  </text>

  <!-- User Query -->
  <rect x="50" y="80" width="120" height="60" fill="#E3F2FD" stroke="#1976D2" stroke-width="2" rx="5"/>
  <text x="110" y="115" text-anchor="middle" font-size="14" fill="#333">User Query</text>

  <!-- Arrow 1 -->
  <path d="M 170 110 L 230 110" stroke="#666" stroke-width="2" fill="none" marker-end="url(#arrowhead)"/>

  <!-- Embedding -->
  <rect x="230" y="80" width="120" height="60" fill="#FFF3E0" stroke="#F57C00" stroke-width="2" rx="5"/>
  <text x="290" y="110" text-anchor="middle" font-size="14" fill="#333">Embed</text>
  <text x="290" y="125" text-anchor="middle" font-size="12" fill="#666">Query</text>

  <!-- Arrow 2 -->
  <path d="M 350 110 L 410 110" stroke="#666" stroke-width="2" fill="none" marker-end="url(#arrowhead)"/>

  <!-- Vector Search -->
  <rect x="410" y="80" width="120" height="60" fill="#F3E5F5" stroke="#7B1FA2" stroke-width="2" rx="5"/>
  <text x="470" y="110" text-anchor="middle" font-size="14" fill="#333">Vector</text>
  <text x="470" y="125" text-anchor="middle" font-size="12" fill="#666">Search</text>

  <!-- Arrow 3 -->
  <path d="M 530 110 L 590 110" stroke="#666" stroke-width="2" fill="none" marker-end="url(#arrowhead)"/>

  <!-- Top-K Docs -->
  <rect x="590" y="80" width="120" height="60" fill="#E8F5E9" stroke="#388E3C" stroke-width="2" rx="5"/>
  <text x="650" y="110" text-anchor="middle" font-size="14" fill="#333">Top-K</text>
  <text x="650" y="125" text-anchor="middle" font-size="12" fill="#666">Documents</text>

  <!-- Arrow down to LLM -->
  <path d="M 650 140 L 650 220" stroke="#666" stroke-width="2" fill="none" marker-end="url(#arrowhead)"/>
  <text x="660" y="180" font-size="12" fill="#666">Context</text>

  <!-- LLM Generation -->
  <rect x="530" y="220" width="240" height="80" fill="#FCE4EC" stroke="#C2185B" stroke-width="2" rx="5"/>
  <text x="650" y="250" text-anchor="middle" font-size="16" font-weight="bold" fill="#333">LLM Generation</text>
  <text x="650" y="270" text-anchor="middle" font-size="12" fill="#666">Query + Retrieved Context</text>
  <text x="650" y="285" text-anchor="middle" font-size="12" fill="#666">→ Generated Answer</text>

  <!-- Arrow to Answer -->
  <path d="M 650 300 L 650 330" stroke="#666" stroke-width="2" fill="none" marker-end="url(#arrowhead)"/>

  <!-- Final Answer -->
  <rect x="530" y="330" width="240" height="50" fill="#C8E6C9" stroke="#388E3C" stroke-width="3" rx="5"/>
  <text x="650" y="360" text-anchor="middle" font-size="14" font-weight="bold" fill="#333">Grounded Answer + Citations</text>

  <!-- Vector Database (side component) -->
  <rect x="50" y="220" width="150" height="100" fill="#FFF9C4" stroke="#F9A825" stroke-width="2" rx="5"/>
  <text x="125" y="245" text-anchor="middle" font-size="14" font-weight="bold" fill="#333">Vector Database</text>
  <text x="125" y="265" text-anchor="middle" font-size="11" fill="#666">• Document chunks</text>
  <text x="125" y="280" text-anchor="middle" font-size="11" fill="#666">• Embeddings</text>
  <text x="125" y="295" text-anchor="middle" font-size="11" fill="#666">• Metadata</text>
  <text x="125" y="310" text-anchor="middle" font-size="11" fill="#666">• Index (HNSW/IVF)</text>

  <!-- Connection to Vector Search -->
  <path d="M 200 270 L 410 110" stroke="#999" stroke-width="1" stroke-dasharray="5,5" fill="none"/>

  <!-- Arrow marker definition -->
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#666"/>
    </marker>
  </defs>
</svg>'''
    return svg


def create_raptor_tree_svg():
    """Generate RAPTOR hierarchical tree diagram."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500">
  <!-- Title -->
  <text x="400" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="#333">
    RAPTOR: Hierarchical Summarization Tree
  </text>

  <!-- Level 2: Root Summary -->
  <rect x="325" y="60" width="150" height="50" fill="#FFCDD2" stroke="#C62828" stroke-width="2" rx="5"/>
  <text x="400" y="80" text-anchor="middle" font-size="12" font-weight="bold" fill="#333">Global Summary</text>
  <text x="400" y="95" text-anchor="middle" font-size="10" fill="#666">(Level 2)</text>

  <!-- Lines from root to level 1 -->
  <line x1="350" y1="110" x2="150" y2="160" stroke="#666" stroke-width="2"/>
  <line x1="400" y1="110" x2="400" y2="160" stroke="#666" stroke-width="2"/>
  <line x1="450" y1="110" x2="650" y2="160" stroke="#666" stroke-width="2"/>

  <!-- Level 1: Cluster Summaries -->
  <rect x="75" y="160" width="150" height="50" fill="#BBDEFB" stroke="#1565C0" stroke-width="2" rx="5"/>
  <text x="150" y="180" text-anchor="middle" font-size="11" font-weight="bold" fill="#333">Cluster A Summary</text>
  <text x="150" y="195" text-anchor="middle" font-size="9" fill="#666">(4 documents)</text>

  <rect x="325" y="160" width="150" height="50" fill="#BBDEFB" stroke="#1565C0" stroke-width="2" rx="5"/>
  <text x="400" y="180" text-anchor="middle" font-size="11" font-weight="bold" fill="#333">Cluster B Summary</text>
  <text x="400" y="195" text-anchor="middle" font-size="9" fill="#666">(3 documents)</text>

  <rect x="575" y="160" width="150" height="50" fill="#BBDEFB" stroke="#1565C0" stroke-width="2" rx="5"/>
  <text x="650" y="180" text-anchor="middle" font-size="11" font-weight="bold" fill="#333">Cluster C Summary</text>
  <text x="650" y="195" text-anchor="middle" font-size="9" fill="#666">(3 documents)</text>

  <!-- Lines from level 1 to level 0 -->
  <!-- Cluster A to docs -->
  <line x1="100" y1="210" x2="50" y2="280" stroke="#999" stroke-width="1.5"/>
  <line x1="130" y1="210" x2="110" y2="280" stroke="#999" stroke-width="1.5"/>
  <line x1="160" y1="210" x2="170" y2="280" stroke="#999" stroke-width="1.5"/>
  <line x1="190" y1="210" x2="230" y2="280" stroke="#999" stroke-width="1.5"/>

  <!-- Cluster B to docs -->
  <line x1="370" y1="210" x2="310" y2="280" stroke="#999" stroke-width="1.5"/>
  <line x1="400" y1="210" x2="380" y2="280" stroke="#999" stroke-width="1.5"/>
  <line x1="430" y1="210" x2="450" y2="280" stroke="#999" stroke-width="1.5"/>

  <!-- Cluster C to docs -->
  <line x1="620" y1="210" x2="540" y2="280" stroke="#999" stroke-width="1.5"/>
  <line x1="650" y1="210" x2="620" y2="280" stroke="#999" stroke-width="1.5"/>
  <line x1="680" y1="210" x2="700" y2="280" stroke="#999" stroke-width="1.5"/>

  <!-- Level 0: Base Documents -->
  <!-- Cluster A docs -->
  <rect x="20" y="280" width="60" height="40" fill="#C8E6C9" stroke="#2E7D32" stroke-width="1.5" rx="3"/>
  <text x="50" y="303" text-anchor="middle" font-size="10" fill="#333">Doc 1</text>

  <rect x="90" y="280" width="60" height="40" fill="#C8E6C9" stroke="#2E7D32" stroke-width="1.5" rx="3"/>
  <text x="120" y="303" text-anchor="middle" font-size="10" fill="#333">Doc 2</text>

  <rect x="160" y="280" width="60" height="40" fill="#C8E6C9" stroke="#2E7D32" stroke-width="1.5" rx="3"/>
  <text x="190" y="303" text-anchor="middle" font-size="10" fill="#333">Doc 3</text>

  <rect x="230" y="280" width="60" height="40" fill="#C8E6C9" stroke="#2E7D32" stroke-width="1.5" rx="3"/>
  <text x="260" y="303" text-anchor="middle" font-size="10" fill="#333">Doc 4</text>

  <!-- Cluster B docs -->
  <rect x="310" y="280" width="60" height="40" fill="#C8E6C9" stroke="#2E7D32" stroke-width="1.5" rx="3"/>
  <text x="340" y="303" text-anchor="middle" font-size="10" fill="#333">Doc 5</text>

  <rect x="380" y="280" width="60" height="40" fill="#C8E6C9" stroke="#2E7D32" stroke-width="1.5" rx="3"/>
  <text x="410" y="303" text-anchor="middle" font-size="10" fill="#333">Doc 6</text>

  <rect x="450" y="280" width="60" height="40" fill="#C8E6C9" stroke="#2E7D32" stroke-width="1.5" rx="3"/>
  <text x="480" y="303" text-anchor="middle" font-size="10" fill="#333">Doc 7</text>

  <!-- Cluster C docs -->
  <rect x="540" y="280" width="60" height="40" fill="#C8E6C9" stroke="#2E7D32" stroke-width="1.5" rx="3"/>
  <text x="570" y="303" text-anchor="middle" font-size="10" fill="#333">Doc 8</text>

  <rect x="620" y="280" width="60" height="40" fill="#C8E6C9" stroke="#2E7D32" stroke-width="1.5" rx="3"/>
  <text x="650" y="303" text-anchor="middle" font-size="10" fill="#333">Doc 9</text>

  <rect x="700" y="280" width="60" height="40" fill="#C8E6C9" stroke="#2E7D32" stroke-width="1.5" rx="3"/>
  <text x="730" y="303" text-anchor="middle" font-size="10" fill="#333">Doc 10</text>

  <!-- Algorithm steps -->
  <rect x="50" y="360" width="700" height="120" fill="#F5F5F5" stroke="#999" stroke-width="1" rx="5"/>
  <text x="400" y="380" text-anchor="middle" font-size="14" font-weight="bold" fill="#333">Algorithm</text>

  <text x="70" y="405" font-size="11" fill="#333">
    <tspan x="70">1. <tspan font-weight="bold">Cluster</tspan>: Group similar documents using k-means (Level 0 → Level 1)</tspan>
    <tspan x="70" dy="18">2. <tspan font-weight="bold">Summarize</tspan>: Generate summary for each cluster using LLM</tspan>
    <tspan x="70" dy="18">3. <tspan font-weight="bold">Repeat</tspan>: Recursively cluster and summarize until single root (Level 1 → Level 2)</tspan>
    <tspan x="70" dy="18">4. <tspan font-weight="bold">Retrieve</tspan>: Search all levels simultaneously, return top-k across tree</tspan>
  </text>
</svg>'''
    return svg


def create_position_effects_svg():
    """Generate position effects (lost-in-the-middle) curve."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 500">
  <!-- Title -->
  <text x="350" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="#333">
    Lost-in-the-Middle: Position Effects in Long Contexts
  </text>

  <!-- Subtitle -->
  <text x="350" y="55" text-anchor="middle" font-size="14" fill="#666">
    Information recall accuracy by position in context window
  </text>

  <!-- Axes -->
  <line x1="80" y1="400" x2="620" y2="400" stroke="#333" stroke-width="2"/>
  <line x1="80" y1="400" x2="80" y2="100" stroke="#333" stroke-width="2"/>

  <!-- Y-axis labels -->
  <text x="70" y="105" text-anchor="end" font-size="12" fill="#333">100%</text>
  <text x="70" y="175" text-anchor="end" font-size="12" fill="#333">90%</text>
  <text x="70" y="245" text-anchor="end" font-size="12" fill="#333">80%</text>
  <text x="70" y="315" text-anchor="end" font-size="12" fill="#333">70%</text>
  <text x="70" y="385" text-anchor="end" font-size="12" fill="#333">60%</text>
  <text x="70" y="405" text-anchor="end" font-size="12" fill="#333">50%</text>

  <!-- X-axis labels -->
  <text x="80" y="420" text-anchor="middle" font-size="12" fill="#333">0%</text>
  <text x="215" y="420" text-anchor="middle" font-size="12" fill="#333">25%</text>
  <text x="350" y="420" text-anchor="middle" font-size="12" fill="#333">50%</text>
  <text x="485" y="420" text-anchor="middle" font-size="12" fill="#333">75%</text>
  <text x="620" y="420" text-anchor="middle" font-size="12" fill="#333">100%</text>

  <!-- X-axis title -->
  <text x="350" y="450" text-anchor="middle" font-size="14" font-weight="bold" fill="#333">
    Position in Context Window
  </text>

  <!-- Y-axis title -->
  <text x="30" y="250" text-anchor="middle" font-size="14" font-weight="bold" fill="#333" transform="rotate(-90 30 250)">
    Recall Accuracy
  </text>

  <!-- Grid lines -->
  <line x1="80" y1="170" x2="620" y2="170" stroke="#DDD" stroke-width="1" stroke-dasharray="5,5"/>
  <line x1="80" y1="240" x2="620" y2="240" stroke="#DDD" stroke-width="1" stroke-dasharray="5,5"/>
  <line x1="80" y1="310" x2="620" y2="310" stroke="#DDD" stroke-width="1" stroke-dasharray="5,5"/>

  <!-- Performance curve -->
  <path d="M 80 120
           Q 140 115, 180 125
           Q 220 140, 260 200
           Q 300 260, 340 280
           Q 380 285, 420 275
           Q 460 250, 500 180
           Q 540 140, 580 125
           Q 600 120, 620 115"
        stroke="#D32F2F" stroke-width="3" fill="none"/>

  <!-- Highlight zones -->
  <!-- Good zone (beginning) -->
  <rect x="80" y="100" width="100" height="300" fill="#4CAF50" opacity="0.1"/>
  <text x="130" y="95" text-anchor="middle" font-size="11" font-weight="bold" fill="#2E7D32">Beginning</text>
  <text x="130" y="430" text-anchor="middle" font-size="10" fill="#2E7D32">92% recall</text>

  <!-- Poor zone (middle) -->
  <rect x="260" y="100" width="160" height="300" fill="#F44336" opacity="0.1"/>
  <text x="340" y="95" text-anchor="middle" font-size="11" font-weight="bold" fill="#C62828">Middle</text>
  <text x="340" y="430" text-anchor="middle" font-size="10" fill="#C62828">62% recall (-30pp)</text>

  <!-- Good zone (end) -->
  <rect x="500" y="100" width="120" height="300" fill="#4CAF50" opacity="0.1"/>
  <text x="560" y="95" text-anchor="middle" font-size="11" font-weight="bold" fill="#2E7D32">End</text>
  <text x="560" y="430" text-anchor="middle" font-size="10" fill="#2E7D32">88% recall</text>

  <!-- Annotation arrows -->
  <path d="M 340 290 L 340 320" stroke="#C62828" stroke-width="2" marker-end="url(#arrow-red)"/>
  <text x="340" y="285" text-anchor="middle" font-size="12" font-weight="bold" fill="#C62828">
    Lost in the Middle
  </text>

  <!-- Key findings box -->
  <rect x="50" y="460" width="600" height="30" fill="#FFF9C4" stroke="#F9A825" stroke-width="1" rx="3"/>
  <text x="350" y="480" text-anchor="middle" font-size="11" fill="#333">
    <tspan font-weight="bold">Key Finding:</tspan> Information in the middle of long contexts has ~30% lower recall [Liu et al. 2023]
  </text>

  <!-- Arrow marker -->
  <defs>
    <marker id="arrow-red" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#C62828"/>
    </marker>
  </defs>
</svg>'''
    return svg


def create_cot_comparison_svg():
    """Generate Chain-of-Thought comparison chart."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400">
  <!-- Title -->
  <text x="300" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="#333">
    Chain-of-Thought vs Direct Prompting
  </text>

  <!-- Subtitle -->
  <text x="300" y="55" text-anchor="middle" font-size="14" fill="#666">
    Performance on GSM8K Math Reasoning
  </text>

  <!-- Axes -->
  <line x1="80" y1="320" x2="520" y2="320" stroke="#333" stroke-width="2"/>
  <line x1="80" y1="320" x2="80" y2="100" stroke="#333" stroke-width="2"/>

  <!-- Y-axis labels -->
  <text x="70" y="325" text-anchor="end" font-size="12" fill="#333">0%</text>
  <text x="70" y="270" text-anchor="end" font-size="12" fill="#333">20%</text>
  <text x="70" y="215" text-anchor="end" font-size="12" fill="#333">40%</text>
  <text x="70" y="160" text-anchor="end" font-size="12" fill="#333">60%</text>
  <text x="70" y="105" text-anchor="end" font-size="12" fill="#333">80%</text>

  <!-- Grid lines -->
  <line x1="80" y1="265" x2="520" y2="265" stroke="#EEE" stroke-width="1"/>
  <line x1="80" y1="210" x2="520" y2="210" stroke="#EEE" stroke-width="1"/>
  <line x1="80" y1="155" x2="520" y2="155" stroke="#EEE" stroke-width="1"/>
  <line x1="80" y1="100" x2="520" y2="100" stroke="#EEE" stroke-width="1"/>

  <!-- Bar 1: Direct Prompting -->
  <rect x="150" y="271" width="100" height="49" fill="#EF5350" stroke="#C62828" stroke-width="2" rx="3"/>
  <text x="200" y="300" text-anchor="middle" font-size="16" font-weight="bold" fill="white">17.9%</text>
  <text x="200" y="345" text-anchor="middle" font-size="14" fill="#333">Direct</text>
  <text x="200" y="362" text-anchor="middle" font-size="12" fill="#666">Prompting</text>

  <!-- Bar 2: CoT Prompting -->
  <rect x="350" y="165" width="100" height="155" fill="#66BB6A" stroke="#2E7D32" stroke-width="2" rx="3"/>
  <text x="400" y="248" text-anchor="middle" font-size="16" font-weight="bold" fill="white">57.1%</text>
  <text x="400" y="345" text-anchor="middle" font-size="14" fill="#333">Chain-of-Thought</text>
  <text x="400" y="362" text-anchor="middle" font-size="12" fill="#666">Prompting</text>

  <!-- Improvement arrow and label -->
  <path d="M 260 240 L 340 210" stroke="#FF9800" stroke-width="3" marker-end="url(#arrow-orange)"/>
  <text x="300" y="220" text-anchor="middle" font-size="14" font-weight="bold" fill="#FF6F00">
    +39.2pp
  </text>
  <text x="300" y="235" text-anchor="middle" font-size="11" fill="#FF6F00">
    improvement
  </text>

  <!-- Reference citation -->
  <rect x="100" y="375" width="400" height="20" fill="#E3F2FD" stroke="#1976D2" stroke-width="1" rx="3"/>
  <text x="300" y="389" text-anchor="middle" font-size="10" fill="#333">
    Source: Wei et al. (2022) "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"
  </text>

  <!-- Arrow marker -->
  <defs>
    <marker id="arrow-orange" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#FF9800"/>
    </marker>
  </defs>
</svg>'''
    return svg


def main():
    """Generate all SVG diagrams."""
    diagrams = {
        'rag-pipeline.svg': create_rag_pipeline_svg(),
        'raptor-tree.svg': create_raptor_tree_svg(),
        'position-effects.svg': create_position_effects_svg(),
        'cot-comparison.svg': create_cot_comparison_svg()
    }

    import os
    output_dir = 'figures'
    os.makedirs(output_dir, exist_ok=True)

    for filename, svg_content in diagrams.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(svg_content)
        print(f"✓ Generated: {filepath}")

    print(f"\nTotal diagrams generated: {len(diagrams)}")
    print(f"Output directory: {output_dir}/")


if __name__ == '__main__':
    main()
