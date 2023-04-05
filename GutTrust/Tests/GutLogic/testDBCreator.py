"""This creates a stub DB with random meals eaten and random mood."""
import os
from GutTrust.GutLogic.templates import GutIO
from GutTrust.GutLogic.LocalGutAI import LocalGutAI
import sqlite3
import json
import random
import copy

"""Weight for how much each food should affect mood.
Increasing weight means the specified food will have higher chance
of damaging score."""
weightList = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

"""Skin,Stomach, and Mood. Changing these weights will make these
scores more prone to being damaged."""
easeOfScoreChange = [1, 1, 1]

"""Amount of stub records to make"""
testDays = 100


enJsonPath = "languagePacks//ENLanguagePack.json"
jpJsonPath = "languagePacks//JPLanguagePack.json"
brJsonPath = "languagePacks//BRLanguagePack.json"

foodListPath = "GutLogic//foodList.json"
defaultListPath = "GutLogic//defaultList.json"


jsonIDDict = {
    "EN": enJsonPath,
    "JP": jpJsonPath,
    "BR": brJsonPath
}


class TestGutIO(GutIO):
    filePath = "testData.sqlite3"
    joinPath = ""
    backup = None
    connection = None
    languageDict = {}
    localFoodList = list()
    dbCreationString = """
    CREATE TABLE CALENDAR
    ("TIME" DATE PRIMARY KEY NOT NULL,
    "MEAL" VARCHAR,
    "MOOD" VARCHAR NOT NULL,
    "TRAINED" INTEGER);
    """

    def __init__(self, mainPath):
        self.joinPath = mainPath
        self.filePath = os.path.join(mainPath, self.filePath)
        self.connection = sqlite3.connect(self.filePath)
        try:
            if self.connection.execute("SELECT COUNT(MOOD) FROM CALENDAR").fetchone() == 0:
                self.connection.execute(self.dbCreationString)
                self.connection.commit()
            else:
                self.loadData()
        except sqlite3.OperationalError as e:
            print(e)
            self.connection.execute(self.dbCreationString)

    def saveMood(self, stomach, skin, body, date) -> bool:
        """saves mood to the SPECIFIED DATE."""
        self.backupDatabase()
        command = """
        INSERT INTO 'CALENDAR'('TIME','MOOD')
        VALUES (DATE(?),?);
        """
        moodString = ("%s,%s,%s" % (stomach, skin, body))
        self.connection.execute(command, (date, moodString))
        self.connection.commit()
        return True

    def saveFood(self, foodList, date) -> bool:
        """
        Saves all the foods selected TO THE SPECIFIED DATE, or updates
        the record if it already exists.
        Fails if foodList is empty.
        """
        getCommand = """
        SELECT MEAL 
        FROM CALENDAR
        WHERE TIME = DATE(?);
        """

        updateCommand = """
        UPDATE CALENDAR
        SET MEAL = ?
        WHERE TIME = DATE(?)
        """

        self.backupDatabase()
        if(not foodList):
            return False
        todayCursor = self.connection.execute(getCommand, (date,))
        result = todayCursor.fetchone()
        updateString = ""
        if result[0]:
            updateString = result[0]
            for food in foodList:
                updateString += "!%s" % food
        else:
            updateString = str(foodList.pop(0))
            for food in foodList:
                updateString += "!%s" % food
            """TIL: A string outside a tuple is a tuple of characters 
                in the eyes of sqlite3."""
        self.connection.execute(str(updateCommand), (updateString, date))
        self.connection.commit()
        return True

    def getFoodList(self) -> list():
        jsonFile = open(os.path.join(self.joinPath, foodListPath))
        foodDict = json.load(fp=jsonFile)
        returnable = list()
        """pair is a tuple of (food,id) where id is an int and food is a string"""
        for pair in foodDict.items():
            returnable.append(pair)
        self.localFoodList = returnable
        return returnable

    def moodIsSaved(self) -> bool:
        getCommand = """
        SELECT MOOD 
        FROM CALENDAR
        WHERE TIME = DATE('now');
        """
        todayMood = self.connection.execute(getCommand).fetchone()
        if todayMood and todayMood != "":
            return True
        else:
            return False

    def getJsonText(self, identifier) -> str:
        """Returns a String specified in the current json file, searched by the
            identifier"""
        return self.languageDict.get(identifier)

    def backupDatabase(self) -> bool:
        """Backs up the entire database to undo entries if needed.
            this definition's latency is untested, frequency of use should
            be changed based on performance."""
        """TODO: test performance of in-disk backup and in-memory temp backup."""
        realDB = self.connection
        backupDB = sqlite3.connect(":memory:")
        realDB.backup(backupDB)
        self.backup = backupDB
        return True

    def rollbackJson(self) -> bool:
        """Rolls back the foodlist json file to its previous state.
        Differently from resetFoodJson(), this only rolls back a single action."""
        pass

    def rollbackCommit(self) -> bool:
        """Rollsback the database to its previous state, by overwriting it
        with a previously made backup.
        """
        self.backup.backup(self.connection)
        return True

    def markTrained(self, date) -> bool:
        """Mark ANY SPECIFIED DATE as trained.
        Throws an exception if there is no record for that date."""
        self.backupDatabase()
        updateCommand = """
        UPDATE CALENDAR
        SET TRAINED = 1
        WHERE TIME = DATE('now');
        """
        self.connection.execute(updateCommand)
        return True

    def returnDataset(self) -> list():
        """TODO: Optimize this.
        This function currently searches from every single
        record.
        The better option would be to sort the table, and search from now,
        to the first one to have the trained flag."""

        """TIL 1: Variables do not exist in sqlite. Use temp tables instead.
        TIL 2: SELECT statements inside functions (eg.IFNULL(Select...))
        Are to be wrapped in parenthesis or they throw an error."""
        createVariableCommand = """
        DROP TABLE IF EXISTS variables;
        CREATE TEMP TABLE variables(
            lastTrainedDate
            );

        INSERT INTO variables 
        SELECT 
                MAX(TIME)
                FROM
                    CALENDAR
                WHERE
                    TRAINED = 1;
        """
        selectCommand = """
        SELECT
            MEAL,
            MOOD,
            DATE(TIME)
                FROM
                    CALENDAR
                WHERE
                    TIME <= DATE('now')
                AND TIME >= IFNULL((SELECT * from variables),(SELECT MIN(TIME) from CALENDAR));
        """
        self.connection.executescript(createVariableCommand)
        rawData = self.connection.execute(selectCommand)
        dataset = rawData.fetchall()
        index = 0
        """dataset is a 2d tuple. it has columns for each date, and has 3 rows.
        [0] foodIds separated by "!"
        [1] a list of ints, representing moodScore
        [2] date, as a string.
        Because it is a tuple, you cannot modify individual items.
        This is why the loop below has to recreate an entire tuple to replace it."""
        dataset = self.stringDataToList(dataset)
        
        """Both of the above together, splits all foodIds by the delimeter, and casts them to int."""
        return dataset

    def foodCount(self):
        """Returns the number of UNIQUE foods recorded. This does not
        include meals(food-sets) as they are combinations of other foods."""
        if not self.localFoodList:
            self.getFoodList()
        listCopy = copy.deepcopy(self.localFoodList)
        [listCopy.remove(x) for x in listCopy if type(x[1]) is str]
        return len(listCopy)

    def stringDataToList(self, rawData) -> list():
        """Fetched data, are strings by default.
        foodIds are separated by "!", and scores are inside brackets -> []
        this converts both to list of ints for easier handling."""
        dataset = rawData
        index = 0
        for row in dataset:
            splitIds = row[0].split("!")
            splitScores = row[1].replace("[","").replace("]","").split(",")
            dataset[index] = ([int(x) for x in splitIds],[int(x) for x in splitScores],row[2])
            index = index + 1
        
        return dataset
        

    def returnLatestData(self) -> list():
        """Returns the latest 10 entries.
        This method does not differenciate already used data, and is to be used
        for evaluation, and not training."""
        returnCommand = """
        SELECT 
            MEAL,
            MOOD,
            DATE(TIME)
                FROM CALENDAR
            LIMIT
                10
        """
        returned = self.connection.execute(returnCommand)
        dataset = returned.fetchall()
        return self.stringDataToList(dataset)

    def getLastId(self) -> int:
        return 15


def addTo(x, y):
    x = x + y


def divideWith(x, y):
    x = x / y
