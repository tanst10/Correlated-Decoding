# ============================
# Provided utility functions
def data_coords(distance):
    # Returns coordinate pairs from (1,1) to (distance,distance).
    coords = []
    for row in range(1, distance+1):
        for col in range(1, distance+1):
            coords.append((col, row))
    return coords

def z_measure_coords(distance):
    # Returns coordinate pairs for Z measure qubits, offset from
    #  the data qubits by 0.5.
    coords = []
    for row in range(1, distance): # don't include the last row
        for col in range(1, distance+1, 2): # only take every other qubit
            if row%2: 
                coords.append((col-0.5, row+0.5))
            else:
                coords.append((col+0.5, row+0.5))
    return coords

def x_measure_coords(distance):
    # Returns coordinate pairs for X measure qubits, offset from
    #  the data qubits by 0.5 and opposite the Y measure qubits.
    coords = []
    for row in range(1, distance+2): # include extra for last row measures
        for col in range(2, distance, 2): # start from second column, ignore last
            if row%2:
                coords.append((col+0.5, row-0.5))
            else:
                coords.append((col-0.5, row-0.5))
    return coords

def coords_to_index(coords):
    # Inverts a list of coordinates into a dict that maps the coord 
    #  to its index in the list.
    return {tuple(c):i for i,c in dict(enumerate(coords)).items()}

def adjacent_coords(coord):
    # Returns the four coordinates at diagonal 0.5 offsets from the input coord.
    # Follows the X-stabilizer plaquette corner ordering from the lecture: 
    #  top-left, top-right, bottom-left, bottom-right.
    col, row = coord
    adjacents = [(col-0.5, row-0.5), (col+0.5, row-0.5),
               (col-0.5, row+0.5), (col+0.5, row+0.5),
              ]
    return adjacents

def index_string(coord_list, c2i):
    # Returns the indicies for each coord in a list as space-delimited string.
    return ' '.join(str(c2i[coord]) for coord in coord_list)

def prepare_coords(distance):
    # Returns coordinates for data qubits, x measures and z measures, along with 
    #  a coordinate-to-index mapping for all of the qubits.
    # The indices are ordered: data first, then x measures, then z measures.
    datas = data_coords(distance)
    x_measures = x_measure_coords(distance)
    z_measures = z_measure_coords(distance)
    c2i = coords_to_index(datas+x_measures+z_measures)
    return datas, x_measures, z_measures, c2i

def coord_circuit(distance):
    # Returns a Stim circuit string that adds a QUBIT_COORDS instruction for each
    #  qubit, based on the coordinate-to-index mapping.
    _, _, _, c2i = prepare_coords(distance)
    stim_circuit = ""
    for coord, index in c2i.items():
        stim_circuit += f"QUBIT_COORDS({','.join(map(str, coord))}) {index}\n"
    return stim_circuit

def label_indices(distance):
    # Returns a Stim circuit string that labels each of the qubits with their 
    #  type and index in the coordinate-to-index mapping.
    # Uses ERROR operations to do the labeling: X_ and Z_ERRORs correspond to
    #  qubits that will be used for X and Z type stabilizer measurements, and
    #  Y_ERRORs label the data qubits. 
    # The index of the qubit is encoded in the operation's error probability: 
    #  The value after the decimal is the index. Eg. 0.01 is 1 and 0.1 is 10.
    datas, x_measures, z_measures, c2i = prepare_coords(distance)
    all_qubits = datas + x_measures + z_measures
    i = 0
    stim_string = ""
    for coord in datas:
        stim_string += f"Y_ERROR(0.{i:>02}) {c2i[coord]}\n"
        i += 1
    stim_string += "TICK\n"
    for coord in x_measures:
        stim_string += f"X_ERROR(0.{i:>02}) {c2i[coord]}\n"
        i += 1
    stim_string += "TICK\n"
    for coord in z_measures:
        stim_string += f"Z_ERROR(0.{i:>02}) {c2i[coord]}\n"
        i += 1

    return stim_string

# ======================================================
# hidden answer functions

def lattice_with_noise(distance, p):
    datas, x_measures, z_measures, c2i = prepare_coords(distance)

    stim_string = ""
    for i in range(4):
        cx_qubits = []
        for measure in z_measures:
            z_controls = adjacent_coords(measure)
            control = z_controls[i]
            if control in c2i:
                cx_qubits.extend([control, measure])
        
        for measure in x_measures:
            x_targets = adjacent_coords(measure)
            index_reorder = [0, 2, 1, 3]
            target = x_targets[index_reorder[i]]
            if target in c2i:
                cx_qubits.extend([measure, target]) # flipped order!
        
        idle_qubits = [coord for coord in c2i.keys() if coord not in cx_qubits]
        
        stim_string += f"""
        CX {index_string(cx_qubits, c2i)}
        DEPOLARIZE2({p}) {index_string(cx_qubits, c2i)}
        DEPOLARIZE1({p}) {index_string(idle_qubits, c2i)}
        TICK
        """

    return stim_string


def stabilizers_with_noise(distance, p):
    datas, x_measures, z_measures, c2i = prepare_coords(distance)
    all_measures = x_measures + z_measures
    all_qubits = datas + all_measures
    
    stim_string = f"""
    R {index_string(all_measures, c2i)}
    X_ERROR({p}) {index_string(all_measures, c2i)}
    DEPOLARIZE1({p}) {index_string(datas, c2i)}
    TICK
    H {index_string(x_measures, c2i)}
    DEPOLARIZE1({p}) {index_string(all_qubits, c2i)}
    TICK
    """

    stim_string += lattice_with_noise(distance, p)

    stim_string += f"""
    H {index_string(x_measures, c2i)}
    DEPOLARIZE1({p}) {index_string(all_qubits, c2i)}
    TICK
    X_ERROR({p}) {index_string(all_measures, c2i)}
    DEPOLARIZE1({p}) {index_string(datas, c2i)}
    M {index_string(all_measures, c2i)}
    TICK
    """
    
    return stim_string

def initialization_step(distance, p):
    datas, x_measures, z_measures, c2i = prepare_coords(distance)
    all_measures = x_measures + z_measures
    all_qubits = datas + all_measures

    stim_string = f"""
    R {index_string(all_qubits, c2i)}
    X_ERROR({p}) {index_string(all_qubits, c2i)}
    TICK
    H {index_string(x_measures, c2i)}
    DEPOLARIZE1({p}) {index_string(all_qubits, c2i)}
    TICK
    """

    stim_string += lattice_with_noise(distance, p)

    stim_string += f"""
    H {index_string(x_measures, c2i)}
    DEPOLARIZE1({p}) {index_string(all_qubits, c2i)}
    TICK
    X_ERROR({p}) {index_string(all_measures, c2i)}
    M {index_string(all_measures, c2i)}
    DEPOLARIZE1({p}) {index_string(datas, c2i)}
    TICK
    """

    for i in range(1, len(z_measures)+1):
        stim_string += f"DETECTOR({i}, 0) rec[{-i}]\n"
    return stim_string

def rounds_step(distance, rounds, p):
    if rounds <= 2:
        return "\n"
    datas, x_measures, z_measures, c2i = prepare_coords(distance)

    stim_string = f"REPEAT {rounds-2} {{\n"
    stim_string += stabilizers_with_noise(distance, p)

    num_measures_per_type = len(z_measures) # number of measures per type per round
    for i in range(1, num_measures_per_type+1): # offset to the previous round
        stim_string += f"DETECTOR({i}, 0) rec[{-i}] rec[{-(i+2*num_measures_per_type)}]\n"
    for i in range(1, num_measures_per_type+1): # offset to the other type and to the previous round
        stim_string += f"DETECTOR({i}, 0) rec[{-(i+num_measures_per_type)}] rec[{-(i+3*num_measures_per_type)}]\n"
        
    stim_string += """
    }
    """ # end repeat block

    return stim_string

def final_step(distance, p):
    datas, x_measures, z_measures, c2i = prepare_coords(distance)
    all_measures = x_measures + z_measures
    all_qubits = datas + all_measures

    stim_string = f"""
    R {index_string(all_measures, c2i)}
    X_ERROR({p}) {index_string(all_measures, c2i)}
    DEPOLARIZE1({p}) {index_string(datas, c2i)}
    TICK
    H {index_string(x_measures, c2i)}
    DEPOLARIZE1({p}) {index_string(all_qubits, c2i)}
    TICK
    """

    stim_string += lattice_with_noise(distance, p)

    stim_string += f"""
    H {index_string(x_measures, c2i)}
    DEPOLARIZE1({p}) {index_string(all_qubits, c2i)}
    TICK
    X_ERROR({p}) {index_string(all_qubits, c2i)}
    M {index_string(all_qubits, c2i)}
    """
    # remember measure order is datas, x_measures, z_measures
    # do previous-round detectors first
    num_measures_per_type = len(z_measures) # number of measures per type per round
    num_datas = len(datas)
    for i in range(1, num_measures_per_type+1): # offset to the previous round
        stim_string += f"DETECTOR({i}, 0) rec[{-i}] rec[{-(i+2*num_measures_per_type+num_datas)}]\n"
    for i in range(1, num_measures_per_type+1): # offset to the other type and to the previous round
        stim_string += f"DETECTOR({i}, 0) rec[{-(i+num_measures_per_type)}] rec[{-(i+3*num_measures_per_type+num_datas)}]\n"
    
    # now the confusing one: the final data measurements and their adjacent measure measurements
    # create a dict that maps each coord to the record index of the most recent measurement on it
    coord_to_record_index = {coord: i-len(all_qubits) for i, coord in enumerate(all_qubits)}
    for i, measure in enumerate(z_measures):
        record_indices = []
        record_indices.append(coord_to_record_index[measure])
        adjacent_datas = adjacent_coords(measure)
        
        for data in adjacent_datas:
            if data in all_qubits:
                record_indices.append(coord_to_record_index[data])
        recs = [f"rec[{j}]" for j in record_indices]
        stim_string += f"DETECTOR({i}, 0) {' '.join(recs)}\n"
    
    obs_recs = [f"rec[{-(i+2*num_measures_per_type)}]" for i in range(1, distance+1)]
    stim_string += f"OBSERVABLE_INCLUDE(0) {' '.join(obs_recs)}"

    return stim_string


def surface_code_circuit_string(distance, rounds, p):
    string = coord_circuit(distance)
    string += initialization_step(distance, p)
    string += rounds_step(distance, rounds, p)
    string += final_step(distance, p)
    return string
