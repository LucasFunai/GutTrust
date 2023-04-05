
import os
from requests import session
import string
from GutTrust.GutLogic.templates import GutIO, GutResponse
import json
import copy
import shutil

import sqlalchemy
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.functions import now
from sqlalchemy import select,update,func

enJsonPath = "languagePacks//ENLanguagePack.json"
jpJsonPath = "languagePacks//JPLanguagePack.json"
brJsonPath = "languagePacks//BRLanguagePack.json"

DEFAULT_FOOD_FILE = "foodList.json"
DEFAULT_RESET_FILE = "defaultList.json"
DEFAULT_DB_FILE = "mealData.sqlite3"
DEFAULT_BACKUP_FILE = "backup_foodList.json"

LASTID_KEY = "lastID"

jsonIDDict = {
    "EN": enJsonPath,
    "JP": jpJsonPath,
    "BR": brJsonPath
}


Base = declarative_base()

"""TODO: Database is being created, but table doesn't exist."""


class DayData(Base):
    """Object representation of a single row of the DB, for usage with
    sqlalchemy with LocalGutIO"""
    __tablename__ = 'CALENDAR'
    time = sqlalchemy.Column(sqlalchemy.types.Time,primary_key=True,nullable=False)
    meal = sqlalchemy.Column(sqlalchemy.types.String,primary_key=False)
    mood = sqlalchemy.Column(sqlalchemy.types.String,primary_key=False,nullable=False)
    trained = sqlalchemy.Column(sqlalchemy.types.Integer,primary_key=False)

    def __repr__(self) -> str:
        return """Date:{time}, foodIds:{meal}, 
            moodScore:{mood}, trainedFlag:{trained}""".format(time=self.time, \
                meal=self.meal,mood=self.mood,trained=self.trained)


class LocalGutIO(GutIO):
    foodJsonPath = ""
    foodbackup_path = ""
    foodReset_path = ""
    db_path = ""
    current_path = ""
    savepoint = None
    engine = None
    languageDict = {}
    localFoodList = list()
    localFoodDict = dict()
    

    def __init__(self,path=None):
        self.setPaths(path)
        self.initializeConnection()
        self.importMealDict()
        self.queryDict = datasetQueryDict = {
            "latest" : self.returnLatestX,
            "all" : self.returnAll,
            "untrained" : self.returnUntrained
            }

    ### Setting Paths ###
    def setPaths(self,path=None):
        try:
            self.setCurrentPath(path=path)
            self.setFoodPath()
            self.setDBPath()
            self.setFoodBackupPath()
            self.setFoodResetPath()
        except Exception as e:
            print("Fatal error at LocalGutIO.py, {err_message}".format(err_message=str(e)))
            raise e
                

        
    def setDBPath(self):
        self.db_path = os.path.join(self.current_path, DEFAULT_DB_FILE)

    def setFoodResetPath(self):
        self.foodReset_path = os.path.join(self.current_path, DEFAULT_RESET_FILE)

    def setCurrentPath(self,path=None):
        if path:
            self.current_path = path
            return
        self.current_path = os.path.dirname(__file__)
        if not path.isdir(self.current_path): 
            raise OSError(2,'Unavailable path set as "mainPath"', self.current_path)
    
    def setFoodPath(self):
        self.foodJsonPath = os.path.join(
                self.current_path, DEFAULT_FOOD_FILE)
    
    def setFoodBackupPath(self):
        self.foodbackup_path = os.path.join(self.current_path, DEFAULT_BACKUP_FILE)

    ### Managing DB connection ###
    def initializeConnection(self):
        self.engine = sqlalchemy.create_engine("sqlite+pysqlite:///" + self.db_path,echo=True)
        self.connection = sessionmaker(bind=self.engine)
        if not self.DBExists(): 
            self.createDB()
            

    def DBExists(self) -> bool:
        return self.engine.has_table("CALENDAR")

    def createDB(self):
        Base.metadata.create_all(self.engine)

    def closeConnection(self):
        self.connection.close_all()

    def createSavepoint(self) -> Session:
        """Returns a nested session. Do transactions
        with the returned session, and call session.rollback()
        to undo transactions."""
        with self.connection() as session:
            self.savepoint = session
            return session

    def rollback(self) -> GutResponse:
        """TODO: Doing both of this together might be wrong. Separate these two"""
        self.rollbackCommit()
        self.rollbackJson()
        self.importMealDict()
        return GutResponse(0,self)

    def rollbackJson(self) -> bool:
        """Rolls back the foodlist json file to its previous state.
        Differently from resetFoodJson(), this only rolls back a single action."""
        backupJsonPath = self.foodbackup_path
        shutil.copy(backupJsonPath, self.foodJsonPath)     
        return True

    def rollbackCommit(self) -> bool:
        """Rollsback the database to its previous state, by overwriting it
        with a previously made backup.
        """
        self.savepoint.rollback()
        return True

    ### Saving ###

    def saveMood(self, stomach, skin, body) -> GutResponse:
        session = self.createSavepoint()
        insertingRow = self.createDBRow(mood=(stomach,skin,body))
        session.add(insertingRow)
        self.savepoint = session
        return GutResponse(0,sender=self)

    

    def saveFood(self, foodList) -> GutResponse:
        """
        Saves all the foods selected to the current date, or updates
        the record if it already exists.
        Fails if foodList is empty.
        """

        session = self.createSavepoint()
        if(not foodList):
            return False
        query = select(DayData).where(DayData.time == now())
        result = session.execute(query)

        updateString = ""
        if result.first() != None:
            prefix = result.fetchone().meal
            updateString = self.idListToDBString(foodList,prefix=prefix)
        else:
            updateString = self.idListToDBString(foodList)
        """TIL: A string outside a tuple is a tuple of characters 
                in the eyes of sqlite3."""
        self.updateTodaysRow(session,meal=updateString)
        return GutResponse(0,sender=self)

    



    def addNewFood(self, foodName) -> GutResponse:
        """Adds a new food to the allergen list."""
        if len(foodName) > 20: return GutResponse(2,self,message="Name cannot be above 20 letters.")
        if foodName in self.localFoodDict.keys(): return GutResponse(2,self,message="This food exists.")

        onlyNumbers = [num for num in self.localFoodDict.values() if isinstance(num, int)]
        last_number = sorted(onlyNumbers)[-1]
        self.localFoodDict[foodName] = int(last_number) + 1

        self.exportFoodDict()
        self.importMealDict()
        return GutResponse(0,self)

    def addNewMeal(self, foodList, mealName, override=False) -> GutResponse:
        """Creates a new entry in the allergen list
            that contains multiple foods.
            if override is True, if an entry with the same name 
            already exists, it is overwritten. Or else this returns False."""
        content = self.localFoodDict  # Will be a dict

        if self.mealExists(mealName) and not override:
            return GutResponse(2,self,message="""A meal with the same name already 
            exists. Do you want to overwrite it?""")

        listString = self.createMealString(foodList)
        content[str(mealName).capitalize()] = listString
        # TIL: .truncate() tries to go back to its original position
        #       after deletion. Not seeking to 0 leaves garbage.
        self.exportFoodDict()
        return GutResponse(0,self)

    def createMealString(self,foodList):
        """From a list of foodIds, creates a string to be inserted into the
        json file. Everytime a new meal needs to be added, use this method
        to ensure consistency of format."""
        listString = ""
        for food in foodList:
            listString = listString + str(food) + ","
        # Slices unnecesary comma
        return listString[:-1]

    def mealExists(self,mealName):
        return str(mealName).capitalize() in self.localFoodDict.keys()

    def exportFoodDict(self):
        """Pushes the current version of the food-id pairs
        into the local savefile, and pushes the previous
        version into the backup.
        The last id is saved to prevent overwriting existing ids."""
        self.updateLastId()
        self.backupFoodDict()
        with open(self.foodJsonPath, "w") as jsonFile:
            json.dump(self.localFoodDict, fp=jsonFile)

    def updateLastId(self):
        """Overwrites the lastId key only if its value is smaller
        than the current biggest Id, to keep track of the highest
        value it has ever been.
        This reads the json, so it has to be called before truncating."""
        lastId = self.getLastId()
        with open(self.foodJsonPath, "r+") as jsonFile:
            jsonDict = json.load(fp=jsonFile)
            if LASTID_KEY not in jsonDict.keys() :
                self.localFoodDict[LASTID_KEY] = lastId
                jsonFile.seek(0)
                jsonFile.truncate(0)
                json.dump(self.localFoodDict,fp=jsonFile)
                return
            if jsonDict[LASTID_KEY] < lastId: 
                self.localFoodDict[LASTID_KEY] = lastId

    def backupFoodDict(self):
        """Updates the backup to be the same as
        the current version.
        IT COPIES THE FILE, NOT THE IN-MEMORY DICT.
        used inside exportFoodDict() to create a backup
        before modifying files."""
        with open(self.foodJsonPath, "r") as currentJson:
            currentDict = json.load(fp=currentJson)
        
        with open(self.foodbackup_path, "w") as jsonFileBackup:
            json.dump(currentDict, fp=jsonFileBackup)

    def resetFoodJson(self) -> bool:
        """Resets all modifications made to the food json.
            this action cannot be undone, and occurs without confirmation on this end."""
        with (open(os.path.join(self.current_path, self.defaultPath), "r"),
            open(os.path.join(self.current_path, self.foodJsonPath), "w")) as jsons:
            defaultJson,currentJson = jsons
            defaultContents = json.load(fp=defaultJson)
            json.dump(defaultContents, fp=currentJson)
        self.importMealDict()
        return True

    def markTrained(self) -> bool:
        """Mark today's record as Trained.
        Any records before the latest Trained record is ignored in training."""
        session = self.createSavepoint()
        self.updateTodaysRow(session,trained=1)
        return True

    def updateTodaysRow(self,session,**params):
        """Updates today's record, overwriting any existing variables
        inside the fields passed to this method.
        The transaction is saved to the savepoint passed as "session"
        for rollback.
        Any number of fields can be omitted, and omitted fields are not modified.
        All keywords needs to have correct names, or else it is not recognized
        and will raise an exception."""
        statement = update(DayData).where(DayData.time == now()) \
            .values(**params).execution_options(synchronize_session = "fetch")
        session.execute(statement)

    

    ###   Getting   ###
    def getLastId(self) -> int:
        try:
            return self.localFoodDict[LASTID_KEY]
        except KeyError:
            onlyIds = [content for content in self.localFoodDict.values() if not type(content) == str]
            lastId = sorted(onlyIds,reverse=True)[0]
            self.localFoodDict[LASTID_KEY] = lastId
            return lastId


    def moodIsSaved(self) -> bool:
        """Check if today's record already has a mood
        inserted. This should be used to prompt the user
        for input if this returns false.
        Lock out the user from doing anything else until
        this returns True, or there might be unexpected exceptions."""
        statement = select(DayData.mood).where(DayData.time == now())
        mood = None
        with self.connection.begin as session:
            mood = session.execute(statement).fetchone()
        if mood != None:
            return True
        else:
            return False

    def importMealDict(self):   
        with open(self.foodJsonPath,"r") as jsonFile:
            self.localFoodDict = json.load(fp=jsonFile)

    def getFoodList(self) -> list():
        """pair is a tuple of (food,id) where id is an int and food is a string.
        Returns meals(More than one id assigned to a name) too."""
        pairs = list()
        for pair in self.localFoodDict.items():
            pairs.append(pair)
        return pairs

    def getIdList(self) -> list():
        """Returns all valid ids for the AI.
        Precisely, it returns from 1 to the highest id recorded (getLastId())"""
        return list(range(1,self.getLastId()))



    def returnLatestData(self) -> list():
        """Returns the latest 10 entries.
        This method does not differenciate already used data, and is to be used
        for evaluation, and not training."""
        query = select(DayData.meal,DayData.mood,func.date(DayData.time)) \
            .order_by(DayData.time.asc()).limit(10)
        returned = None
        with self.connection.begin() as session:
            returned = session.execute(query).all()
        result = list()
        for row in returned:
            result.append((row.meal,row.mood,row.date))
        return result

    def loadJson(self, language):
        """Load the corresponding json file for the language specified."""
        with open(os.path.join(self.current_path, jsonIDDict.get(language)),"r") as jsonFile:   
            if language in jsonIDDict.keys():
                self.languageDict = json.load(fp=jsonFile)
            else:
                return None

    def getJsonText(self, identifier) -> str:
        """Returns a String specified in the current json file, searched by the
            identifier"""
        return self.languageDict.get(identifier)


    def returnDataset(self,**kwargs) -> list():
        """TODO: Optimize this.
        Returns a dataset depending on keyword.
        For the list of accepted keywords check datasetQueryDict.py"""

        """TIL 1: Variables do not exist in sqlite. Use temp tables instead.
        TIL 2: SELECT statements inside functions (eg.IFNULL(Select...))
        Are to be wrapped in parenthesis or they throw an error."""
        # flagQuery is None if nothing is returned.
        result = None
        with self.connection.begin() as session:
            result = None
            if not 'queryType' in kwargs: raise ValueError("Query type not specified in returnDataset()")
            queryType = kwargs.pop("queryType") 
            records = self.datasetQuery(queryType,**kwargs)
            return self.dataSetFromRecords(records)

    ###   Misc   ###

    def dataSetFromRecords(self,records):
        dataset = list()
        for day in records:
            dataset.append((day.time,day.meal,day.food))
        return dataset

    def foodCount(self):
        """Returns the number of UNIQUE foods recorded. This does not
        include meals(food-sets) as they are combinations of other foods."""
        if not self.localFoodDict:
            self.importMealDict()
        pairsCopy = copy.deepcopy(self.localFoodDict.items)
        pairsCopy = list(pairsCopy)
        [pairsCopy.remove(x) for x in pairsCopy if type(x[1]) is str]
        return len(pairsCopy)

    def idListToDBString(self,foodList,prefix=None) -> string:
        """Takes a list of ids, and concatenates all of them
        into a String, in a format the DB recognizes.
        Do not manually process the strings, as changes
        in the syntax will only be affected here, and in DBStringToIdlist()
        If prefix is not None, and is a String, appends it to the start of the string."""
        updateString = ""
        if prefix != None:
            updateString = prefix
            for food in foodList:
                updateString += "!%s" % food
        else:
            updateString = str(foodList.pop(0))
            for food in foodList:
                updateString += "!%s" % food
        return updateString

    def createDBRow(self,mood,time=now(),foodList=None,trained=0):
        """Create an orm model of a row using given information.
        mood should be a tuple with 3 ints, each representing the moodScore for
        stomach, skin, and body, in this order."""
        stomach,skin,body = mood
        moodString = ("%s,%s,%s" % (stomach, skin, body))
        foodString = ""
        if foodList:
            foodString = self.idListToDBString(foodList)
        return DayData(mood=moodString,time=time,meal=foodString,trained=trained)







    def returnLatestX(self,x):
        """Returns the latest X entries"""
        session = self.createSavepoint()
        query = session.select().order_by(DayData.time.decending).limit(x)
        return query

    def returnAll(self):
        session = self.createSavepoint()
        query = session.query(DayData).all()
        return query

    def returnUntrained(self):
        """Gets all of the latest untrained rows.
        If no row is trained, returns all"""
        session = self.createSavepoint()
        flagQuery = select(DayData.time).where(DayData.trained == 1) \
            .order_by(DayData.time.desc()).limit(1)
        flaggedRow = session.execute(flagQuery).first()
        if not flaggedRow: return self.returnAll()
        query = session.select().where(DayData.time <= flaggedRow.time).order_by(DayData.time.asc)
        return query


    

    def datasetQuery(self,queryType,**kwargs):
        """Returns a specific query depending on
            the queryType passed to this method.
            for the list of accepted queryTypes, check datasetQueryDict
            in LocalGutIO.py
            Check method definitions for needed parameters.
            """
        return self.queryDict[queryType](**kwargs)




    



