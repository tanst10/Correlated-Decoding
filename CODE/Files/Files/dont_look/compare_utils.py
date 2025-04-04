from io import BytesIO
from cairosvg import svg2png
from jupyter_compare_view import compare
import matplotlib.image as mpimg
import numpy as np
from .correct_surface_code import *
import stim

def compare_svg_diagram(d1, d2):
    with BytesIO(svg2png(bytestring=d1._repr_svg_())) as fp:
        img = mpimg.imread(fp, format='png')

    with BytesIO(svg2png(bytestring=d2._repr_svg_())) as fp:
        img2 = mpimg.imread(fp, format='png')

    print(f"Your circuit's diagram (left) {'IS' if img.shape == img2.shape and np.all(img == img2) else 'is NOT'} \
identical to the reference one (right).")
    return compare(img,
                 img2,
                 start_mode='horizontal',
                 #height=285,
                 display_format='png',
                 add_controls=False,
                 )

def compare_plt_fig(fig1, filename):
    b1 = BytesIO()
    fig1.savefig(b1, format='png')
    b1.seek(0)
    img1 = b1.getvalue()
    b1.close()
    
    with open(filename, 'rb') as fp:
        img2 = fp.read()
    
    return compare(img1,
                 img2,
                 start_mode='horizontal',
                 #height=285,
                 display_format='png',
                 add_controls=False,
                 )

def compare_circuit(circuit1, circuit2, without_noise=False, diagram_type='timeline-svg'):
    if without_noise:
        circuit1 = circuit1.without_noise()
        circuit2 = circuit2.without_noise()
    d1, d2 = circuit1.diagram(diagram_type), circuit2.diagram(diagram_type)
    return compare_svg_diagram(d1, d2)

def compare_lattice(circuit, distance, p, without_noise=False, diagram_type='timeline-svg'):
    c2 = stim.Circuit(coord_circuit(distance) 
                      + lattice_with_noise(distance, p))
    return compare_circuit(circuit, c2, without_noise, diagram_type)

def compare_stabilizers(circuit, distance, p, without_noise=False, diagram_type='timeline-svg'):
    c2 = stim.Circuit(coord_circuit(distance) 
                      + stabilizers_with_noise(distance, p))
    return compare_circuit(circuit, c2, without_noise, diagram_type)

def compare_initialization(circuit, distance, p, without_noise=False, diagram_type='timeline-svg'):
    c2 = stim.Circuit(coord_circuit(distance) 
                      + initialization_step(distance, p))
    return compare_circuit(circuit, c2, without_noise, diagram_type)

def compare_init_and_rounds(circuit, distance, rounds, p, without_noise=False, diagram_type='timeline-svg'):
    c2 = stim.Circuit(coord_circuit(distance) 
                      + initialization_step(distance, p) 
                      + rounds_step(distance, rounds, p))
    return compare_circuit(circuit, c2, without_noise, diagram_type)

def compare_surface(circuit, distance, rounds, p, without_noise=False, diagram_type='timeline-svg'):
    c2 = stim.Circuit(surface_code_circuit_string(distance, rounds, p))
    return compare_circuit(circuit, c2, without_noise, diagram_type)
    
def compare_error_per_shot(fig):
    return compare_plt_fig(fig, 'dont_look/error_per_shot.png')
    
def compare_error_per_round(fig):
    return compare_plt_fig(fig, 'dont_look/error_per_round.png')
    
def compare_projection(fig):
    return compare_plt_fig(fig, 'dont_look/projection.png')