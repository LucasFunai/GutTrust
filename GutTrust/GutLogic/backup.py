#Functions that might or might not be used.


def update_state(self, y_true, y_pred, sample_weight = None):
        """y_pred and y_true are both 2D vectors in a categorical format, with shape [BATCH_SIZE,3,7]
        Both represents 3 mood scores, that ranges from 1 to 7, but
        y_pred is a probability distribuition.
        Returns accuracy, measured loosely."""
        positive = [4,5,6]
        negative = [0,1,2]
        correct = 0.0
        false = 0.0
        for t_batch,p_batch in zip(y_true,y_pred):
            for t_mood,p_mood in zip(t_batch,p_batch):
                trueIsNegative = set(numpy.argmax(t_mood)).issubset(negative)
                predIndex = 0
                for p_score in p_mood:
                    #True is negative but prediction is not
                    if trueIsNegative != set([predIndex]).issubset(negative):
                        if predIndex == 3:
                            correct = correct + (1 / 7)
                            false = false + (1 / 7)
                        else:
                            false = false + p_score
                    else:
                        correct = correct + p_score
                    predIndex = predIndex + 1
        
        return correct / false