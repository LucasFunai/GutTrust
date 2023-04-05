import copy
import datetime as dt
import numpy

from sklearn.model_selection import train_test_split

"""TODO: Refactor all the ugly code, and make the JSON remember the last
id it had even after deletion. It will be used to zero pad missing ids.
Example: last id is 19, 3,4,and 15 is missing(deleted) -> 0 pad all of those."""

def alignFoodScore(rowList: list):
    """Takes target (food,score,date) tuples and aligns them
        by offsetting food by 1.
        The first score element in the list is disregarded as a result.
        returns a tuple containing a foodList and a scoreList.
        Since the score column corresponds to what was eaten the day before,
        If the corresping score has no data to reference from, it is removed."""
    foodList = list()
    scoreList = list()
    yesterdayFood = None
    lastDate = None
    for row in rowList:
        (food,score,date) = row
        date = dt.datetime.strptime(date, r"%Y-%m-%d")
        if (score != None):
            if yesterdayFood is not None and (date - lastDate).days == 1:
                foodList.append(yesterdayFood)

                stomachScore, skinScore, moodScore = score
                scoreList.append((stomachScore, skinScore, moodScore))
        yesterdayFood = food
        lastDate = date
    return (foodList, scoreList)

def scoresToCategorical(scoreVector):
    #Takes a list of lists, with score in the format [3], 
    # and returns with each list reshaped to [3,7] in categorical format.
    resultList = list()
    for scoreList in scoreVector:
        result = [
            [0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0]
        ]
        i = 0
        for score in scoreList:
            score = round(score)
            if score > 7:
                score = 7
            elif score < 1:
                score = 1
            result[i][score - 1] = 1
            i = i + 1
        resultList.append(result)
    return resultList


def normalizeAndScale(scoreBatches,scale):
    """Takes a [?,3] shaped vector, and normalizes values along axis 0,
    then scales them by scale.
    Ex. test = [[1,3,3],[2,2,1],[3,1,2]]
    result = normalizeAndScale(test,7)
    output: result = [[1.66,3.5,3.5,],[2.33,2.33,1.66],[3.5,1.66,2.33]"""
    npScores = numpy.array(scoreBatches)
    totals = npScores.sum(axis=0)
    result = npScores / totals[numpy.newaxis,:]
    result *= (scale/result.max()) 
    return result.tolist()

def padFoods(foodLists,targetLength):
    paddedFoods = list()
    for foodList in foodLists:
        paddedList = foodList + [0] * (targetLength - len(foodList))
        paddedFoods.append(paddedList)
    return paddedFoods



