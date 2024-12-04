import math

def freqdict_to_termvec(word_dict):
    
    word_dict_ordered_keys = sorted(word_dict.keys())
    
    term_order = []
    term_vals  = []

    for key in word_dict_ordered_keys:
        term_order.append(key)
        term_vals.append(word_dict.get(key));

    return { 'term_order': term_order, 'term_vals': term_vals }

def aligned_freqdict_to_termvec(ground_truth_termvec_rec,word_dict):

    aligned_term_order = []
    aligned_term_vals  = []
        
    for key in ground_truth_termvec_rec['term_order']:
        aligned_term_order.append(key)
        val = word_dict.get(key,0)
        aligned_term_vals.append(val)
        
    return { 'term_order': aligned_term_order, 'term_vals': aligned_term_vals }


def calc_cosine_similarity(termvec_rec1, termvec_rec2):

    termvec_vals1 = termvec_rec1['term_vals']
    termvec_vals2 = termvec_rec2['term_vals']
    termvec_rec1_len = len(termvec_vals1)
    termvec_rec2_len = len(termvec_vals2)

    if (termvec_rec1_len != termvec_rec2_len):
        print(f"calc_cosine_similarity(): different vector lengths ({termvec_rec1_len} vs {termvec_rec2_len} => returning similarity score of 0")
        return 0.0

    dot_prod = 0.0
    mag_squared_vec1 = 0.0
    mag_squared_vec2 = 0.0

    
    for i in range(0,termvec_rec1_len):
        vec1_cpt = termvec_vals1[i]
        vec2_cpt = termvec_vals2[i]

        dot_prod += (vec1_cpt * vec2_cpt)

        mag_squared_vec1 += (vec1_cpt * vec1_cpt)
        mag_squared_vec2 += (vec2_cpt * vec2_cpt)

    if mag_squared_vec1 == 0.0 or mag_squared_vec2 == 0.0:
        print(f"Degenerative vector, all terms were 0 => returning similarity score of 0")
        return 0.0
    
    mag_vec1 = math.sqrt(mag_squared_vec1)
    mag_vec2 = math.sqrt(mag_squared_vec2)

    cos_sim = dot_prod / (mag_vec1 * mag_vec2)

    return cos_sim
