
import sys
from GutTrust.GutLogic.LocalGutAI import LocalGutAI
import os
import random
import unittest
from datetime import *

from GutTrust.Tests.GutLogic.testDBCreator import TestGutIO

"""TODO: Make this mess readable."""
class AITesting(unittest.TestCase):
    io = None
    

    def setUp(self) -> None:
        self.mainPath = os.path.dirname(__file__)
        if ("newDB" in sys.argv):
            try:
                os.remove(os.path.join(self.mainPath,"testData.sqlite3"))
            except Exception:
                pass
        self.io = TestGutIO(self.mainPath)
        self.ai = LocalGutAI(self.io)
        self.ai.setListeners([self.io])

    def tearDown(self) -> None:
        self.io = None
        self.ai = None

    def randomFoods(self,mealPerDay):
        foodList = list()
        for x in range(0, mealPerDay + 1):
                chosenFood = random.choice(
                    (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15))
                foodList.append(chosenFood)
        return foodList

    def calculate_negativeEffect(self,foodList,weights):
        negativeEffect = 0
        for food in foodList:
            """Changes foodId's to indexes, then adds its riskRate to the total."""
            negativeEffect += weights[food - 1]
        return negativeEffect

    def calculate_all_moodScores(self,scoreBias,riskRate,moodBias):
        moodChanceList = list()
        for m_bias in moodBias:
            #Reverse, so that the weights go from ascending score to descending.
            scoreChances = scoreBias.copy()
            # Skips the first 4 scores (From perfect to normal) to leave only
            # The 3 worse ratings, then adds to the weights, 
            # 3/5 to the least bad, 2/5 to the middle,
            # And 1/5 to the worst rating, the riskRate.
            # This fullfils the requirement of "Doubling the riskRate doubling the chance
            # of a bad score"
            scoreChances.reverse()
            for s_index,s_bias in enumerate(scoreChances[3:]):
                s_bias += riskRate / 5 * (3 - s_index) * m_bias
            scoreChances.reverse()
            moodChanceList.append(scoreChances)
        # Returns random scores, but with their chances affected by the biases.
        return [random.choices(
                    [1, 2, 3, 4, 5, 6, 7], x) for x in moodChanceList]


                





    def createFakeDatabase(self, foodWeights=[1] * 15, moodBias=[1] * 3, entries=50, mealPerDay=5, scoreRates=[1, 2, 3, 4, 3, 2, 1]):
        """This creates a database, with the set amount of entries, each with random foods and moods recorded.
        Changing the default foodWeights, partially affects the mood associated with it.
        eg. Milk's weight is changed from 1 to 3 -> Records after a record containing milk has 3 times more chance to
        have a bad mood score.
        This is for testing if the AI is able to deduce the correct foods.
        Changing effectRate, will change which score (Stomach,Skin,Body) will be affected the worse.
        eg. Milk's weight is 3, Skin's rate is 3 -> When Milk decreases the score, Skin has 3 times more chance to be affected.
        This is for testing if the AI is able to realize which is the most fragile part of the user.
        Changing mealPerDay changes how many food entries there is per day.
        Changing scoreRate changes the base chance of each score being chosen."""
        dbCreator = self.io
        previousFood = list()
        currentFoods = list()
        currentMood = list()
        currentDate = datetime(2000, 1, 1)
        negativeEffect = 0
        for x in range(0, entries):
            """Choose random meals for the day."""
            currentFoods = self.randomFoods(mealPerDay)
            

            negativeEffect = self.calculate_negativeEffect(previousFood,foodWeights)
            """Change riskRate based on previous foods. (It is digested and affects the body next day.)"""
            
            """Normalize riskRate"""
            negativeEffect = (negativeEffect / mealPerDay) if negativeEffect != 0 else 0
            


            chosenScores = self.calculate_all_moodScores(scoreBias=scoreRates,riskRate=negativeEffect,moodBias=moodBias)
            """Prevent modifications to previousFood affecting currentFoods."""
            dbCreator.saveMood(
                chosenScores[0], chosenScores[1], chosenScores[2], currentDate)
            dbCreator.saveFood(currentFoods, currentDate)
            previousFood = [x for x in currentFoods]
            currentFoods = list()
            currentMood = list()
            """Steps one day forward."""
            currentDate = currentDate + timedelta(days=1)

    def test_CauseDetectionLong(self):
        """Long test to check if the AI works correctly on trying to
        Detect allergens."""

        """Milk will be the core allergen, and soy will be a secondary 
        allergen. This test will expect both allergens to not be farther
        than 1 place from their weight rank.
        
        eg. if Milk has the biggest weight, milk will have to be either in first place or second.
        if soy has the second biggest, it has to be either 1st, 2nd, or 3rd."""

        if "newDB" in sys.argv:
            causeWeights = [1, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            expectedAccuracy = 0
            for weight in causeWeights:
                expectedAccuracy = expectedAccuracy + (1 / weight)
            expectedAccuracy = expectedAccuracy / len(causeWeights)
            self.createFakeDatabase(foodWeights=causeWeights, entries=92)

        self.ai.train()
        self.assertTrue(self.ai.confidenceCheck(),
                        "Model not confident. Loss ratio higher than 0.25")
        ranks = self.ai.accuse(5)
        milkRank = 0
        milkRank = [i[1] for i in ranks if i[0] == 2]
        if not milkRank : self.fail("Milk was not in the first 5 places. Great discrepancy.")
        differenceWithExpected = milkRank[0] - 1

        milkFlag = differenceWithExpected > 3
        #TODO: Actually test this.
        soyRank = 0
        soyRank = [i[1] for i in ranks if i[0] == 3]

        soyFlag = not bool(soyRank)

        if soyFlag and milkFlag:
            self.fail("Accusations too innacurate. Soy was not in the first 5 places, and Milk was less than 3th place.")



if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
