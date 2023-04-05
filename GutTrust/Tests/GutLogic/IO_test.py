import os
import unittest
from GutTrust.GutLogic.templates import *
from GutTrust.GutLogic.LocalGutIO import LocalGutIO
import shutil


class IOTesting(unittest.TestCase):
    def setUp(self):
        """All tests start with an empty database."""
        self.mainPath = os.path.dirname(__file__)
        self.resetFoodList()
        self.io = LocalGutIO(path=self.mainPath)
        

    def tearDown(self):
        """This resets all files to its original state."""
        self.io.closeConnection()
        del self.io
        self.io = None
        self.resetFoodList()
        


    def resetFoodList(self):
        testFoodList = open(os.path.join(self.mainPath, "foodList.json"), "w")
        defaultFoodList = open(os.path.join(
            self.mainPath, "foodList_copy.json"), "r")
        testResetList = open(os.path.join(
            self.mainPath, "defaultList.json"), "w")
        defaultResetList = open(os.path.join(
            self.mainPath, "defaultList_copy.json"), "r")
        try:
            shutil.copyfileobj(defaultFoodList, testFoodList)
            shutil.copyfileobj(defaultResetList, testResetList)
            try:
                os.remove(os.path.join(self.mainPath, "mealData.sqlite3"))
            except FileNotFoundError:
                pass
            try:
                os.remove(os.path.join(self.mainPath, "foodlist_bu.json"))
            except FileNotFoundError:
                pass
        finally:
            testFoodList.close()
            defaultFoodList.close()
            testResetList.close()
            defaultResetList.close()
    """IO tests"""

    def test_Adding_Food(self):
        """Adds a food to the list, expects it to succeed.
        Then adds a food that exceeds the name character limit,
        and expects to fail."""
        self.assertEqual(self.io.addNewFood("Something").code,0, "Could not add food")
        self.assertEqual(self.io.addNewFood(
            "SOMETHING-ABSURDLY-LARGE-IMPOSSIBLE-TO-FIT").code,2, "Food name length not filtered")

    def test_Adding_Meal(self):
        """
        Adds a meal record, and expects it to succeed.
        Then adds the same meal record without giving permission for overwrite,
        and expects to fail.
        """
        self.assertEqual(self.io.addNewMeal(
            list((1, 2, 3, 4)), "rainbowSmoothie", False).code,0, "Could not add meal")
        self.assertEqual(self.io.addNewMeal(
            list((1, 2, 3, 4)), "rainbowSmoothie", False).code,2, "Meal Overwritten without permission")

    def test_Backup_And_Undo(self):
        """Adds a food to the list, adds a list of foods to today's
        record.Then rolls back the database,
        and expects both operations to be undone."""
        self.io.saveMood(4, 4, 4)
        self.io.saveFood(list((1, 2, 3, 4)))
        self.assertTrue(self.io.rollback(), msg="Rollback failed.")
        self.io.addNewFood("Disgusting Mush")
        self.assertTrue(self.io.rollback(), msg="Rollback failed.")
        newList = self.io.getFoodList()
        newNameList = [x[0] for x in newList]
        """TODO assert fails here. Fix this"""
        self.assertEqual(newNameList.count("Disgusting Mush"),
                         0, msg="New food operation not undone.")
        # Checks if the dataset returned has no food assigned
        self.assertFalse(self.io.returnDataset(queryType="all"),msg="Rollback returned True, but operations not undone")

    def test_Trained_Mark(self):
        """Marks the only record in the database as trained,
        then attempts to return all untrained records.
        Expects to be returned None."""
        self.assertTrue(self.io.markTrained())
        self.assertFalse(self.io.returnDataset(queryType="untrained"))


if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
