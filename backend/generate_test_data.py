import os
import time

ROOT = os.path.join(os.path.dirname(__file__), "..", "root")
os.makedirs(ROOT, exist_ok=True)

files = {
    "quantum_mechanics_1.txt": """
    Quantum mechanics is a fundamental theory in physics that provides a description of the physical properties of nature at the scale of atoms and subatomic particles. 
    It is the foundation of all quantum physics including quantum chemistry, quantum field theory, quantum technology, and quantum information science.
    Wave-particle duality is the concept that every particle or quantum entity may be described as either a particle or a wave.
    """,
    "quantum_mechanics_2.txt": """
    The Schrödinger equation is a linear partial differential equation that governs the wave function of a quantum-mechanical system.
    It is a key result in quantum mechanics, and its discovery was a significant landmark in the development of the subject.
    The equation is named after Erwin Schrödinger, who postulated the equation in 1925, and published it in 1926.
    """,
    "quantum_computing.txt": """
    Quantum computing is a type of computation whose operations can exploit the phenomena of quantum mechanics, such as superposition, interference, and entanglement.
    Devices that perform quantum computations are known as quantum computers.
    """,
    "newtonian_physics_1.txt": """
    Classical mechanics is a physical theory describing the motion of macroscopic objects, from projectiles to parts of machinery, and astronomical objects, such as spacecraft, planets, stars and galaxies.
    For objects governed by classical mechanics, if the present state is known, it is possible to predict how it will move in the future (determinism) and how it has moved in the past (reversibility).
    """,
    "newtonian_laws.txt": """
    Newton's laws of motion are three basic laws of classical mechanics that describe the relationship between the motion of an object and the forces acting on it.
    First law: In an inertial frame of reference, an object either remains at rest or continues to move at a constant velocity, unless acted upon by a force.
    Second law: In an inertial frame of reference, the vector sum of the forces F on an object is equal to the mass m of that object multiplied by the acceleration a of the object: F = ma.
    """,
    "gravity_intro.txt": """
    Gravity, or gravitation, is a natural phenomenon by which all things with mass or energy—including planets, stars, galaxies, and even light—are brought toward one another.
    On Earth, gravity gives weight to physical objects, and the Moon's gravity causes the ocean tides.
    """,
    "genetics_intro.txt": """
    Genetics is the study of genes, genetic variation, and heredity in organisms.
    It is an important branch in biology because heredity is vital to organisms' evolution.
    Gregor Mendel, a Moravian Augustinian friar working in the 19th century in Brno, was the first to study genetics scientifically.
    """,
    "dna_structure.txt": """
    Deoxyribonucleic acid (DNA) is a molecule composed of two polynucleotide chains that coil around each other to form a double helix carrying genetic instructions for the development, functioning, growth and reproduction of all known organisms and many viruses.
    DNA and ribonucleic acid (RNA) are nucleic acids.
    """,
    "crispr_technology.txt": """
    CRISPR is a family of DNA sequences found in the genomes of prokaryotic organisms such as bacteria and archaea.
    These sequences are derived from DNA fragments of bacteriophages that had previously infected the prokaryote.
    They are used to detect and destroy DNA from similar bacteriophages during subsequent infections.
    """,
    "cell_biology_1.txt": """
    Cell biology is the study of cell structure and function, and it revolves around the concept that the cell is the fundamental unit of life.
    Focusing on the cell provides a detailed understanding of the tissues and organisms that cells compose.
    """,
    "mitosis_process.txt": """
    In cell biology, mitosis is a part of the cell cycle when replicated chromosomes are separated into two new nuclei.
    Cell division gives rise to genetically identical cells in which the number of chromosomes is maintained.
    In general, mitosis (division of the nucleus) is preceded by the S stage of interphase (during which the DNA is replicated) and is often followed by telophase and cytokinesis.
    """
}

print(f"Creating {len(files)} test files in {ROOT}...")

for filename, content in files.items():
    path = os.path.join(ROOT, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Created: {filename}")
    time.sleep(0.5) # Slight delay to simulate realistic arrival

print("Done. Watch the dashboard for updates!")
