#Author: Ngoc Hai Nguyen
#ID : 32212046
import sys
def reverse_boyer_moore_search(txt, pat):
    if len(pat) == 0 or len(txt) == 0:
        return []  # Return an empty list for an empty string
    
    ASCII_OFFSET = 33  # Define ASCII_OFFSET to map characters to table indices
    RBC = compute_rbc_table(pat)  # repair a reversed bad character table
    z_table = compute_z_table(pat) # computing z tablle
    goodsuffix = compute_good_suffix_table(pat)  # computing Good Suffix table for the pattern
    matchedprefix = compute_matched_prefix(pat)  # computing matched prefix values for the pattern

    skip_start, skip_stop = None, None  # Initialize skip region tracking, for galil's optimization

    m, n = len(pat), len(txt)

    match_positions = []  # Initialize list to capture match positions
    
    s = n - m  # Initial alignment of the pattern at the rightmost end of the text
    while s >= 0:
        j = 0 # current position that being point into in the scan
        # Scan and compare characters from left to right within the pattern
        while j < m and pat[j] == txt[s + j]:

            #galil's optimization
            if skip_start is not None and skip_stop is not None and j >= skip_start and j <= skip_stop:
                #skipped throught the previous shifted region, where skip stop indicating the end of the previous shift
                j = skip_stop + 1  # Skip the matched region
                skip_start, skip_stop = None, None  # Reset skip region
            else:
                j += 1
        # if the j == m, mean that we have reach over the len of the pattern => a match occurs
        if j == m:
            print(f"Pattern found at position {s}")
            # print(f"Text    : {txt}")
            # print(f"Pattern : {' ' * s}{pat}")
            match_positions.append(s + 1)  # Append match position in 1-based indexing
            #case 2 in good suffix
            #check if there are any prefix that match the suffix
            if matchedprefix[m - 2] > 1:
                #shifted by the matched prefix value, the second to last value
                shift = matchedprefix[m - 2]
                #as matched prefix value correcly indicating the shift value, so skip start = shift
                skip_start = shift  # Corrected to start from the beginning of the pattern
                # and this is a prefix so it will be the last position of the patter as the skip region
                skip_stop = m - 1
            else:
                # shift by 1 of case 2 not happend
                shift = 1    
                # when shifted, reset all the galil's regeion
                skip_start, skip_stop = None, None  # Reset skip region

            # print(f"Shift calculated: {shift} positions to the left.")
            s -= shift
        else:
            # reset the region as soon as another mismatch happended
            skip_start, skip_stop = None, None  # Reset skip region
            #extract and convert it to ascii value - offset since table stating index is 0 not 33
            mismatch_char = txt[s + j]
            mismatch_char_index = ord(mismatch_char) - ASCII_OFFSET
                
            # Convert j to k for decreasing index order
            k = m - 1 - j  # Adjusting j to k for reverse-index logic, as this is what did to followed the lecture concept
                
            # Lookup in RBC table with adjusted index k
            rk_value = RBC[k][mismatch_char_index]
            # Calculate the shift
            rbc_shift  = k - rk_value

            # init good suffix value
            gs_shift = goodsuffix[j - 1]
             # Initialize gs_shift, case 1b, if goodsuffix[j - 1] == 0 mean there no alternate suffix avaliable for that suffix
            if j > 0 and goodsuffix[j - 1] == 0:  # Check for matched prefix condition
                gs_shift = matchedprefix[j - 1] # check for good prefix position j-1, 1 position to the right as we are in the reverse order
                skip_start = gs_shift  # Corrected to start from the beginning of the pattern
                skip_stop = m - 1 # prefix so stop = end position
            #case 1a
            elif j > 0:
                gs_shift = goodsuffix[j - 1]  # extract the good suffix value
                skip_start = gs_shift  # as goodsuffix value will also returned with the shift's value
                skip_stop = skip_start + z_table[gs_shift] - 1 # calculate the len of the shifted pattern + skip start to identify the skip stop

            #tie-breaking between 2, bad character and gs shift
            shift = max(rbc_shift, gs_shift)
            # this is an edge case where rbc_shift and gs_shift
            if shift == rbc_shift:
                skip_start, skip_stop = None, None  # Reset skip region based on the assumption that the shift is made by RBC

            # print(f"\nMismatch at position {s + j} ('{mismatch_char}') in text")
            # print(f"Shift calculated: {shift} positions to the left.")
            s -= shift  # Apply the calculated shift
    return match_positions  # Return the list of match positions

def compute_z_table(s):
    # Initialize the Z-array with zeros for each character in the string
    z = [0] * len(s)
    # The first Z-value is the length of the entire string
    z[0] = len(s)
    
    # Initialize pointers for the Z-box: left and right boundaries
    left, right = 0, 0
    for i in range(1, len(s)): # Start from the second character
        if i > right:
            # If i is outside the current Z-box, we start a new Z-box at i
            left, right = i, i # reset the z-box pointer, set it to i

             # Expand the Z-box as long as the substring from left matches the prefix of the string
            while right < len(s) and s[right - left] == s[right]:
                right += 1
            # The length of the matched substring is stored in Z[i]
            z[i] = right - left
            right -= 1 # decrease right as the last i implement is not a match
        else:
            # if I inside the z box, we used the already computed value in the z table
            k = i - left # k is the mirror position of i in the z box

            # if the z value at the position does not exceed the z box
            if z[k] < right - i + 1:
                z[i] = z[k] # We can assign the Z-value of k to i
            else:
            # if z value exceed the z box, we have to manually expand the Z-box 
                left = i
                # Expand the Z-box as long as the substring from left matches the prefix of the string
                while right < len(s) and s[right - left] == s[right]:
                    right += 1
                z[i] = right - left
                right -= 1 # decrease right as the last i implement is not a match
    return z

def compute_good_suffix_table(pat):
    #compute the z table
    z_suffix = compute_z_table(pat)
    
    m = len(pat)
    goodsuffix = [0] * (m + 1)  # Initialize Good Suffix table with an appropriate size

    # Process the Z-table from right to left for Good Suffix table updates
    for p in range(m - 1, 0, -1):  # Decrementing to move from right to left
        # as we are doing reverse boyer moore, the pat no need to be reverse so we can directly extact the position like this
        j = z_suffix[p] - 1 # Calculate the position to update in the Good Suffix table
        # update the gs value of the value of the alternate suffix position
        goodsuffix[j] = p

    return goodsuffix

def compute_matched_prefix(pat):
    m = len(pat)
    z = compute_z_table(pat)  # Compute the Z-array for pat
    mp = [-1] * m  # Initialize matched prefix array with -1

    start_position = -1  # Initialize start position for matched segments

    # Access Z-values from right to left, including index 0
    for j in range(m-1, -1, -1):
        # z[j] == m - j indicating the length of the matched suffix at position j have a length that able to reached to the end of the
        #patther which mean a matched prefix
        if z[j] == m - j:
            # If a full match to the end of the pattern is found, update start_position
            # we are going from right to left so that it make sure that all the prefix value are at it highest
            start_position = j
        
        # Update mp for positions that correspond to this segment
        mp[m-j-1] = start_position
    
    return mp

def compute_rbc_table(pat):
    ASCII_range = 94  # Covering printable ASCII characters [33, 126]
    ASCII_start = 33
    m = len(pat)
    
    # Initialize the RBC table with -1, indicating that initially, no occurrence to the right is known
    RBC = [[-1 for _ in range(ASCII_range)] for _ in range(m)]
    
    # Process each character in the pattern from left to right, as we doing reverse boyer moore
    for i in range(m):
        for j in range(i + 1, m):
            next_char_index = ord(pat[j]) - ASCII_start
            if RBC[m - 1 - i][next_char_index] == -1:  # If no closer occurrence has been recorded
                RBC[m - 1 - i][next_char_index] = m - 1 - j  # Record it in reverse order

    return RBC



s = "acabadbacaba"
# Compute and visualize the Z-table
# compute_z_table(s)


txt = "aaabbcbcaaabbcbcaacaabcdcaabbcbca"
pat = "abcd"
pat = "aa"
pat = "aab"
txt = "  aaa   "
# pat = "abcd"
# pat = " "
#match prefix test
# txt = "bbb"
# pat = " "
# txt = "ccaaccaaccaacc"
# pat = "ccaac"



def main(text_filename, pattern_filename):
    # Read the text and pattern from the given files
    with open(text_filename, 'r') as text_file:
        txt = text_file.read().strip()
    with open(pattern_filename, 'r') as pattern_file:
        pat = pattern_file.read().strip()

    match_positions = reverse_boyer_moore_search(txt, pat)

    # Write match positions to 'output_q1.txt'
    with open('output_q1.txt', 'w') as output_file:
        for pos in match_positions:
            output_file.write(f"{pos}\n")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])





