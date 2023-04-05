import string
from kivy.app import App
from kivy.uix.stacklayout import StackLayout
import json
from functools import total_ordering

@total_ordering
class GutResponse(object):
    """Object for lower layers to communicate with
    upper layers. Any time you would return a boolean,
    or an integer, return this with the needed
    information instead.
    Insert the instance that created the response in sender.
    Current default is:
    0: Code executed OK. (This object handled the notification.)
    1: Warning. Message contains information meant for the code.
    (Or, this class recieved the notification, but could not handle it.)
    2: Error. Message contains information that should be shown
    to the user.
    You can compare a GutResponse to an Integer, to check for errors above
    a certain gravity.
    eg. if GutResponse == 0: can mean "If the returned handled". """
    def __init__(self,code,sender,payload=None,message="",**kwargs):
        self.message = message
        self.code = code
        self.payload = payload
        self.sender = sender

    def __eq__(self,other):
        if isinstance(other,GutResponse):
            return self.code == other.code
        if isinstance(other,int):
            return self.code == other
        return 

    def __lt__(self,other):
        if isinstance(other,GutResponse):
            return self.code < other.code
        if isinstance(other,int):
            return self.code < other
        return 

    def hasMessage(self) -> bool:
        """If code is 0, returns True, else false."""
        if self.code == 0:
            return True
        else:
            return False

    def hasPayload(self):
        if self.payload: return True
        return False

    def getMessage(self) -> string:
        """Returns the message this object holds.
        Only use on non-zero code."""
        return self.message

    def getCode(self) -> int:
        return self.code

    def setPayload(self,payload):
        self.payload = payload

    def getPayload(self):
        return self.payload

class GutIO(object):
    """Interface for the data handler."""
    importedModel = None
    customFoods = {}
    customMeals = {}
    languageObject = None

    def loadJson(self, language):
        """Load the corresponding json file for the language specified."""
        pass

    def getJsonText(self, identifier):
        """Returns a String specified in the current json file, searched by the
            identifier"""
        pass

    def initiateDB(self):
        """Initiate, or reset a database."""
        pass

    def saveMood(self, stomach, skin, body) -> GutResponse:
        """Save the scores for today's date."""
        pass

    def saveFood(self,foodlist) -> GutResponse:
        """Saves all the ids in the list in today's record."""
        pass

    def loadData(self, **kwargs) -> GutResponse:
        """Load all data(Including AI model) and return True if success."""
        pass

    def getFoodList(self) -> list:
        """Load all food pairs with their ids and return them in a list"""
        pass

    def addFoodList(self,idList) -> GutResponse:
        """Take all foods inside idList and register it to today's report"""
        pass

    def foodCount(self) -> int:
        """Returns the amount of allergens registered, including customs."""
        pass

    def returnModel(self):
        """Returns the saved AI model, or None if it does not exist."""
        pass

    def undoLastSave(self):
        """Undo's the last modification to the DB."""
        pass

    def returnDataset(self,all = False) -> list:
        """Return only data that has not yet been used to train the AI model, unless all is set to true"""
        pass

    def moodIsSaved(self) -> GutResponse:
        """Return True if today's mood was already recorded. Do not call
            saveFood if this is not True, and enforce user to input mood first."""
        pass

    def getLocalJson(self,langId):
        """Loads JSON for the UI"""
        pass


class GutAI(object):
    """Interface for the AI handler."""
    aiModel = None
    dataTreshold = None
    confidenceTreshold = None
    dataHandler = None

    def train(self, dataList) -> bool:
        """Train the AI model by feeding it the most recent data.
            Previous AI trainings are preserved, and defining which days are
            "recent" is to be done elsewhere. Returns True if success."""
        pass

    def accuse(self, i: int, **kwargs) -> list:
        """Check the chance of each food in kwargs 
            causing sickness in the next day,
            and return top i entries. If confidenceCheck returns False,
            return None"""
        pass

    def importModel(self) -> int:
        """Load existing AI model.
            returns:
            0 if success
            1 if it does not exist
            2 if an exception was thrown."""
        pass


class GutGUI(StackLayout):
    """The first object to be instantiated when the application runs.
        This class should be responsible for initializing all other gutLogic components,
        and needs to have methods to bridge the input from kivy to the code, so that the other components 
        can react."""
    state = None
    """MAIN MENU BUTTONS"""

    def graphTap(self):
        pass

    def moodButtonPress(self):
        pass

    def foodButtonPress(self):
        pass

    def settingButtonPress(self):
        pass

    """FOOD SCREEN BUTTONS"""

    def foodConfirmed(self):
        pass

    def foodAdded(self):
        pass

    def foodCancel(self):
        pass

    def mealConfirmed(self):
        pass

    """MOOD SCREEN BUTTONS"""

    def moodConfirmed(self):
        pass

    def moodAdded(self):
        pass

    def moodCancel(self):
        pass

    """SETTING SCREEN BUTTONS"""

    def dataResetPress(self):
        pass

    def createFoodSetPress(self):
        pass

    def showDisclaimerPress(self):
        pass

    def feedbackPress(self):
        pass

    """MISC"""

    def getJsonText(self, identifier):
        """Returns a String specified in the current json file, searched by the
            identifier"""
        pass



def GutService(object):
    """The service layer for the application."""
    
    def saveFoods(self,idList,date=None) -> GutResponse:
        """Saves all foods in idList to today's record if date
        is None, or attempts to modify the record of the date specified"""
        pass

    def getJson(self) -> GutResponse:
        """retrieves the Json file from the IO layer"""
        pass

    def saveMood(self,moodTuple) -> GutResponse:
        """Given a tuple (1-7,1-7,1-7) saves the moodScore
        to the DB, where the scores are (Stomach,Skin,Body)"""
        pass

    def moodIsSaved(self) -> GutResponse:
        """Returns 0 if there is already a report for today.
        Returns 1 If there is not, and 2 on Error."""
        pass



