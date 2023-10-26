#!/usr/bin/python3

def pseudo_test_pattern_fast(adc_bits=14):
    # we represent each bit by an integer (0/1)
    # Even though this pseudo-random sequence has a period of 511, we start with 1022
    # because we want to have an integer number of times the number of ADC bits. ADC bits is 8, 12 or 14
    # so we will need an even number of bits, for sure
    bits = 1022
    bitseq = bytearray(bits)
    bitseq[0:8] = [1,1,1,1,1,0,1,1]  # first 8 bits
    for i in range(bits-8):
        c = (bitseq[4]+bitseq[8])%2
        bitseq[1:bits] = bitseq[0:bits-1]  # shift the array forward by 1 index
        bitseq[0] = c

    # Now replicate the bit-sequence as many times as needed to fit an integer times the number
    # of ADC bits
    bitseq1 = bitseq
    for i in range(14):
        if len(bitseq)%adc_bits == 0:
            break
        bitseq = bitseq + bitseq1

    # the number of generated samples (adc_bits bits transformed into integers)    
    sample_len = len(bitseq)//adc_bits
    assert sample_len*adc_bits == len(bitseq)

    pseudo_samples = [0]*sample_len
    for isample in range(sample_len):
        for bit in range(adc_bits):
            if bitseq[len(bitseq)-(isample+1)*adc_bits+bit]:
                pseudo_samples[isample] |= 1<<bit;
        
    return pseudo_samples



def match_pattern(signals,pattern):
        """
        Generate a peuseo random number pattern according to the standard, and try to match against the received
        data from the ADC

        Parameters:
        ^^^^^^^^^^^
        signals: a list of values corresponding to subsequent samples from a single channel
        pattern: the pseudo-random sequence, which is assumed to be periodic

        Returns:
        ^^^^^^^^
        True/False: indicating whether a full match was found
        matches   : a list of (eventually partial) matches. Each element of this list is a 2-element list, 
                    the first element being the start index of the signal sequence within the pattern sequence,
                    the 2nd element is the length of values matching
        
        """

        # A list of matches. Each element of this list is a 2-element list, the first element of which is
        # the starting position of the match within the pattern sequence, the 2nd element is the length of the match
        matches = []

        n = len(pattern)

        if signals is None:
            return False,[]

        for i in range(n):
            if signals[0] == pattern[i]:
                matches.append([i,1])  # So far we matched 1 value at index i

        if len(matches) == 0:
            return False,matches

        full_match = False
        for i_signal in range(1,len(signals)):
            for match in matches:
                # match[1] is the number of matching characters. It must be equal to i_signal, otherwise
                # the match was broken already before, so we should not continue comparing
                if match[1] != i_signal:
                    continue

                # index within the pattern sequence, cyclized
                pattern_index = (match[0]+i_signal)%n

                # If we match this element as well, increase the number of 
                if pattern[pattern_index] == signals[i_signal]:
                    match[1] += 1
                    # If this is the last signal value and we matched, we have a full match
                    if i_signal == len(signals)-1:
                        full_match = True

        return full_match,matches


pattern = [1,3,5,7,11,13]
signals = [7,1]
print(match_pattern(signals,pattern))
