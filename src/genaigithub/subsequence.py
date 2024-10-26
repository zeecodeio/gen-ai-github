class Subsequence:

    def __init__(self, array, sequence):
        self.sequence = sequence
        self.array = array
        self.is_valid = False

    # O(n) time | O(1) space
    def validate(self):
        seq_idx = 0
        for value in self.array:
            if seq_idx == len(self.sequence):
                break
            if self.sequence[seq_idx] == value:
                seq_idx += 1

        self.is_valid = seq_idx == len(self.sequence)
        return self.is_valid
